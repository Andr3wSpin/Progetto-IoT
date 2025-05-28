import uasyncio as asyncio
import utime
import _thread
from machine import Pin

from AMP import AMP  
from animation_async import Animation
from HCSR04_async    import HCSR04
from HW511_async     import HW511
from NFC_reader      import NFCReader
from read_dht22      import read_dht22
from DisplayUI       import DisplayUI
from STEP_MOTOR_FULL import STEP_MOTOR_FULL
from STOPLIGHT       import Stoplight


# Pin configuration
SCL_PIN         = 38
SDA_PIN         = 37
RED_PIN         = 40
YELLOW_PIN      = 41
GREEN_PIN       = 42
BTN_SHUTTER_PIN = 1
RESET_BTN_PIN   = 10
AMP_BCLK_PIN    = 5
AMP_LRCLK_PIN   = 4
AMP_DIN_PIN     = 6
STEP_PINS       = [21, 35, 13, 14]
NFC_SCK_PIN     = 18
NFC_MOSI_PIN    = 16
NFC_MISO_PIN    = 17
NFC_CS_PIN      = 15
NFC_RESET_PIN   = 7
DHT22_PIN       = 2
TRIG1, ECHO1    = 48, 9
TRIG2, ECHO2    = 11, 12
HW511_PIN       = 36

# Global shared state
shutter_state     = 'closing'  # 'closed','opening','opened','closing'
car_in_garage     = False
obstacle_detected = False
security_alarm    = False
fire_alarm        = False
AUTHORIZED_UIDS   = {'12052F02'}

from _thread import allocate_lock
state_lock = allocate_lock()

# Event callbacks
def on_nfc(uid_str):
    global shutter_state
    if shutter_state != 'closed' or not uid_str:
        print("not closed")
        return
    if uid_str in AUTHORIZED_UIDS:
        print("autorizzato")
        animation.set_state(Animation.ACCESS_ALLOWED)
        amp.play('access_allowed.wav')
        with state_lock:
            shutter_state = 'opening'
    else:
        print("non autorizzato")
        animation.set_state(Animation.ACCESS_DENIED)
        amp.play('access_denied.wav')


def on_car_near(is_near):
    global car_in_garage
    with state_lock:
        if shutter_state == 'closed':
            if not is_near:
                car_in_garage = False
        else:
            car_in_garage = is_near
    print("car_in_garage:", car_in_garage)


def on_obstacle(is_near):
    global obstacle_detected
    obstacle_detected = is_near


def on_dht(temp, hum):
    global fire_alarm
    if temp is not None and temp >= 50.0:
        fire_alarm = True


def on_reset():
    global security_alarm, fire_alarm
    security_alarm = False
    fire_alarm     = False
    animation.set_state(Animation.ANIMATION)


def on_shutter():
    global shutter_state
    with state_lock:
        if shutter_state == 'closed':
            shutter_state = 'opening'
        elif shutter_state == 'opened':
            shutter_state = 'closing'


def on_limit_change(state: bool):
    global shutter_state
    if state and shutter_state == 'closing':
        with state_lock:
            shutter_state = 'closed'


# Hardware instantiation
oled          = DisplayUI(scl_pin=SCL_PIN, sda_pin=SDA_PIN)
animation     = Animation(oled)
amp           = AMP(bclk_pin=AMP_BCLK_PIN, lrclk_pin=AMP_LRCLK_PIN, din_pin=AMP_DIN_PIN)

motor_pins    = [Pin(p, Pin.OUT) for p in STEP_PINS]
shutter_motor = STEP_MOTOR_FULL(motor_pins)

car_sensor      = HCSR04(trigger_pin=TRIG1, echo_pin=ECHO1)
obstacle_sensor = HCSR04(trigger_pin=TRIG2, echo_pin=ECHO2)
limit_switch    = HW511(sig_pin=HW511_PIN)
nfc             = NFCReader(
    sck_pin=NFC_SCK_PIN, mosi_pin=NFC_MOSI_PIN,
    miso_pin=NFC_MISO_PIN, cs_pin=NFC_CS_PIN,
    reset_pin=NFC_RESET_PIN
)
reset_btn       = Pin(RESET_BTN_PIN, Pin.IN, Pin.PULL_DOWN)
reset_btn.irq(trigger=Pin.IRQ_FALLING, handler=lambda p: on_reset())
btn_shutter     = Pin(BTN_SHUTTER_PIN, Pin.IN, Pin.PULL_DOWN)
btn_shutter.irq(trigger=Pin.IRQ_FALLING, handler=lambda p: on_shutter())

stoplight = Stoplight(
    red_pin=RED_PIN,
    yellow_pin=YELLOW_PIN,
    green_pin=GREEN_PIN,
    logic_cb=lambda: (
        'green'  if shutter_state == 'opened' else
        'yellow' if shutter_state == 'opening' else
        'red'    if shutter_state == 'closing' or (shutter_state == 'closed' and car_in_garage) else
        'off'
    ),
    poll_ms=200
)


# THREAD per il motore
def shutter_thread():
    global shutter_state, obstacle_detected, car_in_garage

    delay_ms    = 8
    full_steps  = 2048
    last_car_in = False

    while True:
        if shutter_state == 'opening':
            for _ in range(full_steps):
                shutter_motor.step_ccw()
                utime.sleep_ms(delay_ms)
            with state_lock:
                shutter_state = 'opened'
            last_car_in = car_in_garage

        elif shutter_state == 'closing':
            count = 0
            while not limit_switch.object_detected() and not obstacle_detected:
                shutter_motor.step_cw()
                utime.sleep_ms(delay_ms)
                count += 1
            if obstacle_detected:
                with state_lock:
                    shutter_state = 'opening'
                for _ in range(count):
                    shutter_motor.step_ccw()
                    utime.sleep_ms(delay_ms)
                with state_lock:
                    shutter_state = 'opened'
                last_car_in = car_in_garage
            else:
                with state_lock:
                    shutter_state = 'closed'

        elif shutter_state == 'opened':
            if not last_car_in and car_in_garage:
                with state_lock:
                    shutter_state = 'closing'
            else:
                last_car_in = car_in_garage
        else:
            utime.sleep_ms(200)


async def security_sm():
    """
    Scatta l'allarme se un'auto non viene più rilevata quando il garage è chiuso.
    """
    global security_alarm
    last_car_state = False

    while True:
        if shutter_state == 'closed':
            if last_car_state and not car_in_garage and not security_alarm:
                security_alarm = True
                while security_alarm:
                    amp.play('alarm.wav')
                    await asyncio.sleep_ms(100)
            last_car_state = car_in_garage
        await asyncio.sleep_ms(200)

async def fire_sm():
    """
    Riproduce l'allarme incendio finché fire_alarm rimane True, controllando ogni secondo.
    """
    while True:
        if fire_alarm:
            while fire_alarm:
                amp.play('alarm.wav')
                await asyncio.sleep_ms(1000)
        await asyncio.sleep_ms(1000)

async def auto_toggle_sm():
    while True:
        await asyncio.sleep_ms(10000)
        if shutter_state == 'opened':
            with state_lock:
                shutter_state = 'closing'

async def main():
    asyncio.create_task(nfc.monitor(on_nfc,                read_interval_s=1))
    asyncio.create_task(car_sensor.detect_obj(on_car_near, threshold_cm=15, interval_s=2))
    asyncio.create_task(obstacle_sensor.detect_obj(on_obstacle, threshold_cm=15, interval_s=2))
    asyncio.create_task(limit_switch.monitor(on_limit_change, interval_ms=200))
    asyncio.create_task(read_dht22(pin_num=DHT22_PIN,       interval_s=10, callback=on_dht))
    asyncio.create_task(security_sm())
    asyncio.create_task(fire_sm())
    asyncio.create_task(auto_toggle_sm())
    asyncio.create_task(animation.loop())
    asyncio.create_task(stoplight.run())

    while True:
        await asyncio.sleep_ms(1000)

if __name__ == '__main__':
    _thread.start_new_thread(shutter_thread, ())
    asyncio.run(main())