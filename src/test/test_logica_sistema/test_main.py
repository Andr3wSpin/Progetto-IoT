import uasyncio as asyncio
from machine import Pin

from AMP_async       import AMP
from animation_async import Animation
from HCSR04_async    import HCSR04
from HW511_async     import HW511   # solo per finecorsa
from NFC_reader      import NFCReader
from read_dht22      import read_dht22
from DisplayUI       import DisplayUI
from STEP_MOTOR_FULL_async import STEP_MOTOR_FULL
from STOPLIGHT       import Stoplight

# -----------------------------------------------------------------------------
# 1) Stato globale condiviso
# -----------------------------------------------------------------------------
shutter_state     = "closed"      # "closed","opening","opened","closing"
car_in_garage     = False
obstacle_detected = False
security_alarm    = False
fire_alarm        = False

AUTHORIZED_UIDS = {"04AABBCC", "11223344"}

# -----------------------------------------------------------------------------
# 2) Callback per eventi
# -----------------------------------------------------------------------------
def on_nfc(uid_str):
    global shutter_state
    # ignoriamo NFC se non siamo chiusi o non c'è UID
    if shutter_state != "closed" or not uid_str:
        return

    if uid_str in AUTHORIZED_UIDS:
        # accesso permesso
        asyncio.create_task(amp.play("access_allowed.wav"))
        animation.set_state(Animation.ACCESS_ALLOWED)
        shutter_state = "opening"
    else:
        # UID non riconosciuto
        asyncio.create_task(amp.play("access_denied.wav"))
        animation.set_state(Animation.ACCESS_DENIED)

def on_car_near(is_near):
    global car_in_garage
    car_in_garage = is_near

def on_obstacle(is_near):
    global obstacle_detected
    obstacle_detected = is_near

def on_dht(temp, hum):
    global fire_alarm
    print(temp, "\n", hum)
    if temp is not None and temp >= 50.0:
        fire_alarm = True

def on_reset():
    """
    Callback del pulsante di reset (IRQ):
    azzera gli allarmi e riporta animazione su ANIMATION.
    """
    global security_alarm, fire_alarm
    security_alarm = False
    fire_alarm     = False
    animation.set_state(Animation.ANIMATION)
    amp.stop()

def on_shutter():
    """
    Callback del pulsante shutter (IRQ):
    toggle tra 'opening' e 'closing' solo se siamo in 'closed' o 'opened'
    """
    global shutter_state
    if shutter_state == "closed":
        shutter_state = "opening"
    elif shutter_state == "opened":
        shutter_state = "closing"

# -----------------------------------------------------------------------------
# 3) Istanze hardware e servizi
# -----------------------------------------------------------------------------
# Display e animazione
oled      = DisplayUI(scl_pin=22, sda_pin=21)
animation = Animation(oled)

# Amplificatore
amp = AMP(bclk_pin=14, lrclk_pin=15, din_pin=32)

# Motore tapparella
shutter_motor = STEP_MOTOR_FULL(2, 3, 4, 5)

# Sensori ultrasuoni
car_sensor      = HCSR04(trigger_pin=18, echo_pin=19)
obstacle_sensor = HCSR04(trigger_pin=21, echo_pin=22)

# Finecorsa tapparella
limit_switch = HW511(sig_pin=23)

# Lettore NFC
nfc = NFCReader(
    spi_id=1,
    sck_pin=18, mosi_pin=16, miso_pin=17,
    cs_pin=15, reset_pin=7
)

# Pulsante reset allarmi su GPIO27, pull-up e IRQ su fronte di discesa
reset_btn = Pin(27, Pin.IN, Pin.PULL_UP)
reset_btn.irq(trigger=Pin.IRQ_FALLING, handler=lambda pin: on_reset())

# Nuovo pulsante shutter su GPIO26, pull-up e IRQ
btn_shutter = Pin(26, Pin.IN, Pin.PULL_UP)
btn_shutter.irq(trigger=Pin.IRQ_FALLING, handler=lambda pin: on_shutter())

# -----------------------------------------------------------------------------
# 3-bis) Semaforo (LED)
# -----------------------------------------------------------------------------
def cb_car_present():      return car_in_garage
def cb_shutter_opening():  return shutter_state == "opening"
def cb_shutter_closing():  return shutter_state == "closing"
def cb_shutter_opened():   return shutter_state == "opened"

stoplight = Stoplight(
    red_pin=12,
    yellow_pin=13,
    green_pin=14,
    car_present_cb     = cb_car_present,
    shutter_opening_cb = cb_shutter_opening,
    shutter_closing_cb = cb_shutter_closing,
    shutter_opened_cb  = cb_shutter_opened,
    poll_ms=200
)

# -----------------------------------------------------------------------------
# 4) State-machine Coroutines
# -----------------------------------------------------------------------------
async def shutter_sm():
    global shutter_state, obstacle_detected

    # Partenza: forzo chiusura per portarmi a “closed”
    shutter_state = "closing"
    await shutter_motor.step(-1)
    while not limit_switch.object_detected():
        await asyncio.sleep_ms(50)
    shutter_motor.stop_motor()
    shutter_state = "closed"

    # Loop operativo
    while True:
        if shutter_state == "opening":
            await shutter_motor.step(1)
            shutter_state = "opened"

        elif shutter_state == "closing":
            await shutter_motor.step(-1)
            # se compare un ostacolo interrompi e riapri
            if obstacle_detected:
                shutter_motor.stop_motor()
                shutter_state = "opening"
                continue
            # altrimenti attendi finecorsa
            while not limit_switch.object_detected():
                await asyncio.sleep_ms(50)
            shutter_motor.stop_motor()
            shutter_state = "closed"

        else:
            await asyncio.sleep_ms(100)

async def security_sm():
    global security_alarm
    state = "idle"
    while True:
        if state == "idle":
            if shutter_state == "closed" and car_in_garage:
                state = "monitoring"
        elif state == "monitoring":
            if shutter_state != "closed":
                state = "idle"
            elif not car_in_garage:
                security_alarm = True
                asyncio.create_task(amp.play("alarm.wav"))
                state = "alarm"
        elif state == "alarm":
            if not security_alarm:
                state = "idle"
        await asyncio.sleep_ms(200)

async def fire_sm():
    global fire_alarm
    state = "idle"
    last = asyncio.get_event_loop().time()
    while True:
        now = asyncio.get_event_loop().time()
        if state == "idle" and now - last >= 10:
            state = "reading"
        elif state == "reading":
            state = "checking"
        elif state == "checking":
            if fire_alarm:
                asyncio.create_task(amp.play("alarm.wav"))
                state = "alarm"
            else:
                state = "idle"
            last = now
        elif state == "alarm":
            if not fire_alarm:
                state = "idle"
        await asyncio.sleep_ms(100)

async def auto_toggle_sm():
    """
    Ogni 10 secondi, se il garage è aperto, lo prova a richiudere automaticamente.
    """
    while True:
        await asyncio.sleep(10)
        if shutter_state == "opened":
            shutter_state = "closing"

# -----------------------------------------------------------------------------
# 5) Main: crea e avvia tutti i task
# -----------------------------------------------------------------------------
async def main():
    # sensori e NFC
    asyncio.create_task(nfc.monitor(on_nfc,        read_interval_s=1))
    asyncio.create_task(car_sensor.detect_obj(on_car_near,    threshold_cm=5,   interval_s=1))
    asyncio.create_task(obstacle_sensor.detect_obj(on_obstacle,threshold_cm=5,   interval_s=0.25))
    asyncio.create_task(limit_switch.watch_on_rising(lambda: None, interval_ms=200))
    asyncio.create_task(read_dht22(pin_num=4,     interval_s=10, callback=on_dht))

    # state-machine
    asyncio.create_task(shutter_sm())
    asyncio.create_task(security_sm())
    asyncio.create_task(fire_sm())
    asyncio.create_task(auto_toggle_sm())

    # animazione e semaforo
    asyncio.create_task(animation.loop())
    asyncio.create_task(stoplight.run())

    # mantieni vivo il loop
    while True:
        await asyncio.sleep(1)

# Avvio
asyncio.run(main())

