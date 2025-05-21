import uasyncio as asyncio
import utime
from machine import Pin
import os

os.chdir('/test')

from AMP_async       import AMP
from animation_async import Animation
from HCSR04_async    import HCSR04
from HW511_async     import HW511
from NFC_reader      import NFCReader
from read_dht22      import read_dht22
from DisplayUI       import DisplayUI
from STEP_MOTOR_FULL_async import STEP_MOTOR_FULL
from STOPLIGHT       import Stoplight


SCL_PIN = 37
SDA_PIN = 38
RED_PIN=40,
YELLOW_PIN=41
GREEN_PIN=42
BTN_SHUTTER_PIN = 1
RESET_BTN_PIN = 10
AMP_BCLK_PIN=5
AMP_LRCLK_PIN=6
AMP_DIN_PIN=7
STEP_MOTOR_FULL_1 = 21
STEP_MOTOR_FULL_2 = 35
STEP_MOTOR_FULL_3 = 13
STEP_MOTOR_FULL_4 = 14
NFC_SCK_PIN = 18
NFC_MOSI_PIN = 16
NFC_MISO_PIN = 17
NFC_CS_PIN = 15
NFC_RESET_PIN = 7
DHT22_PIN = 2
HCSR04_TRIGGER_1_PIN = 46
HCSR04_TRIGGER_2_PIN = 11
HCSR04_ECHO_1_PIN = 9
HCSR04_ECHO_2_PIN = 12
HW511_PIN = 36


# -----------------------------------------------------------------------------
# 1) Stato globale condiviso
# -----------------------------------------------------------------------------
shutter_state     = "closed"      # "closed","opening","opened","closing"
car_in_garage     = False
obstacle_detected = False
security_alarm    = False
fire_alarm        = False
AUTHORIZED_UIDS   = {"12052F02"}

# -----------------------------------------------------------------------------
# 2) Callback per eventi (con debug prints)
# -----------------------------------------------------------------------------
def on_nfc(uid_str):
    global shutter_state
    print("[DEBUG] on_nfc called with uid_str=", uid_str, "state=", shutter_state)
    if shutter_state != "closed" or not uid_str:
        print("[DEBUG] on_nfc ignored: shutter_state=", shutter_state, "or no uid")
        return
    if uid_str in AUTHORIZED_UIDS:
        print("[DEBUG] NFC authorized")
        asyncio.create_task(amp.play("access_allowed.wav"))
        animation.set_state(Animation.ACCESS_ALLOWED)
        shutter_state = "opening"
        print("[DEBUG] shutter_state set to opening")
    else:
        print("[DEBUG] NFC denied")
        asyncio.create_task(amp.play("access_denied.wav"))
        animation.set_state(Animation.ACCESS_DENIED)


def on_car_near(is_near):
    global car_in_garage
    car_in_garage = is_near
    print("[DEBUG] on_car_near: car_in_garage=", car_in_garage)


def on_obstacle(is_near):
    global obstacle_detected
    obstacle_detected = is_near
    print("[DEBUG] on_obstacle: obstacle_detected=", obstacle_detected)


def on_dht(temp, hum):
    global fire_alarm
    print("[DEBUG] on_dht: temp=", temp, "hum=", hum)
    if temp is not None and temp >= 50.0:
        fire_alarm = True
        print("[DEBUG] fire_alarm triggered")


def on_reset():
    global security_alarm, fire_alarm
    print("[DEBUG] on_reset: clearing alarms")
    security_alarm = False
    fire_alarm     = False
    animation.set_state(Animation.ANIMATION)
    amp.stop()


def on_shutter():
    global shutter_state
    print("[DEBUG] on_shutter: current shutter_state=", shutter_state)
    if shutter_state == "closed":
        shutter_state = "opening"
        print("[DEBUG] shutter_state set to opening by button")
    elif shutter_state == "opened":
        shutter_state = "closing"
        print("[DEBUG] shutter_state set to closing by button")


def on_limit_change(state: bool):
    global shutter_state
    print(f"[DEBUG] on_limit_change: state={state}")
    if state:
        print(">> Finecorsa raggiunto: tapparella chiusa")
        if shutter_state == "closing":
            shutter_state = "closed"
            print("[DEBUG] shutter_state set to closed (from on_limit_change)")
    else:
        print(">> Finecorsa rilasciato: tapparella non in posizione")

# -----------------------------------------------------------------------------
# 3) Istanze hardware e servizi
# -----------------------------------------------------------------------------
oled = DisplayUI(scl_pin=SCL_PIN, sda_pin=SDA_PIN)
animation      = Animation(oled)
amp            = AMP(bclk_pin=AMP_BCLK_PIN, lrclk_pin=AMP_LRCLK_PIN, din_pin=AMP_DIN_PIN)
shutter_motor  = STEP_MOTOR_FULL(STEP_MOTOR_FULL_1, STEP_MOTOR_FULL_2, STEP_MOTOR_FULL_3, STEP_MOTOR_FULL_4)
car_sensor     = HCSR04(trigger_pin=HCSR04_TRIGGER_1_PIN, echo_pin=HCSR04_ECHO_1_PIN)
obstacle_sensor= HCSR04(trigger_pin=HCSR04_TRIGGER_2_PIN, echo_pin=HCSR04_ECHO_2_PIN)
limit_switch   = HW511(sig_pin=HW511_PIN)
nfc            = NFCReader(
                   sck_pin=NFC_SCK_PIN, mosi_pin=NFC_MOSI_PIN, miso_pin=NFC_MISO_PIN,
                   cs_pin=NFC_CS_PIN, reset_pin=NFC_RESET_PIN, debug=False)
reset_btn      = Pin(RESET_BTN_PIN, Pin.IN, Pin.PULL_DOWN)
reset_btn.irq(trigger=Pin.IRQ_FALLING, handler=lambda p: on_reset())
btn_shutter    = Pin(BTN_SHUTTER_PIN,  Pin.IN,  Pin.PULL_DOWN)
btn_shutter.irq(trigger=Pin.IRQ_FALLING, handler=lambda p: on_shutter())



def cb_car_present():     return car_in_garage

def cb_shutter_opening(): return shutter_state == "opening"

def cb_shutter_closing(): return shutter_state == "closing"

def cb_shutter_opened():  return shutter_state == "opened"

def cb_stoplight_logic():
    if shutter_state == "opened":
        return "green"
    elif shutter_state == "opening":
        return "yellow"
    elif shutter_state == "closing":
        return "red"
    elif shutter_state == "closed":
        if car_in_garage:
            return "red"
        else:
            return "off"
    else:
        return "off"

stoplight = Stoplight(
    red_pin=RED_PIN,
    yellow_pin=YELLOW_PIN,
    green_pin=GREEN_PIN,
    logic_cb=cb_stoplight_logic,
    poll_ms=200
)

# -----------------------------------------------------------------------------
# 4) State-machine Coroutines (con debugging)
# -----------------------------------------------------------------------------
async def shutter_sm():
    global shutter_state, obstacle_detected
    print("[DEBUG] shutter_sm starting: forcing close")
    shutter_state = "closing"
    await shutter_motor.step(-1)
    while not limit_switch.object_detected():
        await asyncio.sleep_ms(50)
    print("[DEBUG] shutter_sm: limit sensor detected -> closed")
    shutter_motor.stop_motor()
    shutter_state = "closed"

    while True:
        print(f"[DEBUG] shutter_sm loop: state={shutter_state}")
        if shutter_state == "opening":
            print("[DEBUG] shutter_sm: opening...")
            await shutter_motor.step(1)
            shutter_state = "opened"
            print("[DEBUG] shutter_sm: opened")

        elif shutter_state == "closing":
            print("[DEBUG] shutter_sm: closing...")
            await shutter_motor.step(-1)
            if obstacle_detected:
                print("[DEBUG] shutter_sm: obstacle detected during closing -> reopening")
                shutter_motor.stop_motor()
                shutter_state = "opening"
                continue
            while not limit_switch.object_detected():
                await asyncio.sleep_ms(50)
            shutter_motor.stop_motor()
            shutter_state = "closed"
            print("[DEBUG] shutter_sm: closed")

        else:
            await asyncio.sleep_ms(100)

async def security_sm():
    global security_alarm
    state = "idle"
    while True:
        print(f"[DEBUG] security_sm: state={state}, shutter_state={shutter_state}, car_in_garage={car_in_garage}")
        if state == "idle" and shutter_state == "closed" and car_in_garage:
            state = "monitoring"
            print("[DEBUG] security_sm: transition idle->monitoring")

        elif state == "monitoring":
            if shutter_state != "closed":
                state = "idle"
                print("[DEBUG] security_sm: transition monitoring->idle (shutter opened)")
            elif not car_in_garage:
                security_alarm = True
                asyncio.create_task(amp.play("alarm.wav"))
                state = "alarm"
                print("[DEBUG] security_sm: transition monitoring->alarm")

        elif state == "alarm" and not security_alarm:
            state = "idle"
            print("[DEBUG] security_sm: transition alarm->idle (reset)")

        await asyncio.sleep_ms(200)

async def fire_sm():
    global fire_alarm
    state = "idle"
    last = utime.ticks_ms()
    while True:
        now = utime.ticks_ms()
        print(f"[DEBUG] fire_sm: state={state}, fire_alarm={fire_alarm}")
        if state == "idle" and utime.ticks_diff(now, last) >= 10_000:
            state = "reading"
            print("[DEBUG] fire_sm: transition idle->reading")

        elif state == "reading":
            state = "checking"
            print("[DEBUG] fire_sm: transition reading->checking")

        elif state == "checking":
            if fire_alarm:
                asyncio.create_task(amp.play("alarm.wav"))
                state = "alarm"
                print("[DEBUG] fire_sm: transition checking->alarm")
            else:
                state = "idle"
                print("[DEBUG] fire_sm: transition checking->idle")
            last = utime.ticks_ms()

        elif state == "alarm" and not fire_alarm:
            state = "idle"
            print("[DEBUG] fire_sm: transition alarm->idle (reset)")

        await asyncio.sleep_ms(100)

async def auto_toggle_sm():
    while True:
        print(f"[DEBUG] auto_toggle_sm: shutter_state={shutter_state}")
        await asyncio.sleep_ms(10000)
        if shutter_state == "opened":
            shutter_state = "closing"
            print("[DEBUG] auto_toggle_sm: auto closing shutter")

# -----------------------------------------------------------------------------
# 5) Main: crea e avvia tutti i task
# -----------------------------------------------------------------------------
async def main():
    print("[DEBUG] main: starting all tasks")
    asyncio.create_task(nfc.monitor(on_nfc,                read_interval_s=1))
    asyncio.create_task(car_sensor.detect_obj(on_car_near, threshold_cm=15, interval_s=2.0))
    asyncio.create_task(obstacle_sensor.detect_obj(on_obstacle, threshold_cm=15, interval_s=2.0))
    asyncio.create_task(limit_switch.monitor(on_limit_change, interval_ms=200))
    asyncio.create_task(read_dht22(pin_num=DHT22_PIN,               interval_s=10, callback=on_dht))
    asyncio.create_task(shutter_sm())
    asyncio.create_task(security_sm())
    asyncio.create_task(fire_sm())
    asyncio.create_task(auto_toggle_sm())
    asyncio.create_task(animation.loop())
    asyncio.create_task(stoplight.run())
    print("[DEBUG] main: tasks launched")
    while True:
        await asyncio.sleep_ms(1000)

if __name__ == '__main__':
    asyncio.run(main())
