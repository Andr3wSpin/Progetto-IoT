import uasyncio as asyncio
import utime
import _thread
import ujson
from machine import Pin, reset, unique_id
from umqtt.simple import MQTTClient
import ubinascii
from wlan_config import wlan
from collections import deque

from AMP import AMP  
from animation_async import Animation
from HCSR04_async    import HCSR04
from HW511_async     import HW511
from NFC_reader      import NFCReader
from read_dht22      import read_dht22
from DisplayUI       import DisplayUI
from STEP_MOTOR_FULL import STEP_MOTOR_FULL
from STOPLIGHT       import Stoplight

# Adafruit IO settings
AIO_USER = 'paolo32v'         
AIO_KEY = 'aio_WYgF56MUytvkbPPsixQVBkWVfI7o'      
BROKER = 'io.adafruit.com'
PORT = 1883

# Topics declaration
DHT_TOPIC_READ_VAL = f"{AIO_USER}/feeds/readVAL".encode()      # invia i valori misurati dal dht al broker 
DHT_TOPIC_INIT_MAX = f"{AIO_USER}/feeds/initMAX".encode()      # inizializza gli slider di NodeRed con il valore iniziale di MAX_TEMP e MAX_HUM
DHT_TOPIC_SET_MAX  = f"{AIO_USER}/feeds/setMAX".encode()       # cambia il valore di MAX_TEMP e MAX_HUM utilizzando i valori passati da NodeRed
READ_NFC_TOPIC     = f"{AIO_USER}/feeds/readNFC".encode()      # invia al broker il codice UID letto
CHECK_NFC_TOPIC    = f"{AIO_USER}/feeds/checkNFC".encode()     # riceve la risposta dal broker per la validazione del codice letto
SHUTTER_TOPIC      = f"{AIO_USER}/feeds/shutter".encode()      # apertura / chiusura serranda da NodeRed
ALARM_TOPIC        = f"{AIO_USER}/feeds/alarm".encode()        # disattivazione allarme da NodeRed
REPORT_TOPIC       = f"{AIO_USER}/feeds/report".encode()       # genera un report con data e ora di ingresso e uscita e UID dell'utente
INFO_GARAGE_TOPIC  = f"{AIO_USER}/feeds/infoGarage".encode()   # invia informazioni sullo stato del garage, della serrana e dell'allarme

subscriptions_list = [DHT_TOPIC_SET_MAX, CHECK_NFC_TOPIC, SHUTTER_TOPIC, ALARM_TOPIC]

# Global shared variables
client = None
msg_queue = deque((), 30)
broker_connected = False

# Initial temperature and humidity thresholds
MAX_TEMP = 50
MAX_HUM  = 60

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
#AUTHORIZED_UIDS   = {'12052F02'}

shutter_status_map = {"closed": "Chiusa", "opened": "Aperta", "closing": "In chiusura", "opening": "In apertura"}

from _thread import allocate_lock
state_lock = allocate_lock()
queue_lock = allocate_lock()

# Event callbacks
def on_nfc(uid_str):
    global shutter_state
    if shutter_state != 'closed' or not uid_str:
        print("not closed")
        return
    
    msg = ujson.dumps({
        "uid": uid_str
    })
    with queue_lock:
        msg_queue.append((READ_NFC_TOPIC, msg))


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
    if temp is not None and temp > MAX_TEMP:
        fire_alarm = True

    msg = ujson.dumps({
        "temp": temp,
        "hum":  hum
    })
    with queue_lock:
        msg_queue.append((DHT_TOPIC_READ_VAL, msg))


def on_reset():
    global security_alarm, fire_alarm
    security_alarm = False
    fire_alarm     = Falseè
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


# Message handlers
def dht_handler(msg):
    global MAX_TEMP, MAX_HUM
    msg = msg.decode()
    data = ujson.loads(msg)

    if 'max_temp' in data:
        MAX_TEMP = data['max_temp']

    if 'max_hum' in data:
        MAX_HUM = data['max_hum']


def nfc_handler(msg):
    global  shutter_state
    msg = msg.decode()

    if msg == "1":
        print("autorizzato")
        animation.set_state(Animation.ACCESS_ALLOWED)
        amp.play('access_allowed.wav')
        with state_lock:
            shutter_state = 'opening'
    else:
        print("non autorizzato")
        animation.set_state(Animation.ACCESS_DENIED)
        amp.play('access_denied.wav')


# MQTT messages callback
def sub_callback(topic, msg):
    """
    Richiama l'handler associato al topic del messaggio ricevuto
    """
    if topic == DHT_TOPIC_SET_MAX:
        dht_handler(msg)

    elif topic == CHECK_NFC_TOPIC:
       nfc_handler(msg)

    elif topic == SHUTTER_TOPIC:
        on_shutter()

    elif topic == ALARM_TOPIC:
        on_reset()


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


async def update_garage_info():
    while True:
        garage_status  = "Occupato" if car_in_garage else "Libero"
        shutter_status = shutter_status_map[shutter_state]
        alarm_status   = "Attivo" if fire_alarm or security_alarm else "Spento"
        
        msg = ujson.dumps({
            "stato_garage": garage_status,
            "stato serranda": shutter_status,
            "stato_allarme": alarm_status
        })
        with queue_lock:
            msg_queue.append((INFO_GARAGE_TOPIC, msg))
        await asyncio.sleep_ms(5000)


async def send_msg():
    global client, broker_connected
    while True:
        if msg_queue:
            with queue_lock:
                topic, msg = msg_queue.popleft()
                try:
                    client.publish(topic, msg)
                except OSError as e:
                    broker_connected = False
        await asyncio.sleep_ms(100)

def connect_and_subscribe():
    """
    Connessione al broker MQTT e sottoscrizione ai topic
    """
    global client, broker_connected

    client_id = ubinascii.hexlify(unique_id())
    client = MQTTClient(client_id, BROKER, PORT, AIO_USER, AIO_KEY)
    client.set_callback(sub_callback)
    client.connect()
    
    for topic in subscriptions_list:
        client.subscribe(topic)

    broker_connected = True
    print('Connessione al broker completata.')


def restart_and_reconnect():
    """
    Riavvia il dispositivo se non riesce a connettersi al broker
    """
    utime.sleep(2)
    reset()


def init_sliders():
    msg = ujson.dumps({
            "max_temp": MAX_TEMP,
            "max_hum": MAX_HUM,
            }) 
    with queue_lock:
        msg_queue.append((DHT_TOPIC_INIT_MAX, msg))


async def main():
    global client, broker_connected

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
    asyncio.create_task(update_garage_info())

    while wlan.isconnected() and broker_connected:
        try:
            client.check_msg()
        except OSError as e:
            broker_connected = False

        await asyncio.sleep_ms(500)

    print("Il dispositivo si è disconesso. Riconnessione in corso...")
    restart_and_reconnect()

if __name__ == '__main__':
    try:
        connect_and_subscribe()
    except OSError as e:
        print('Errore durante la connessione con il broker MQTT. Riconessione in corso...')
        restart_and_reconnect()
    _thread.start_new_thread(shutter_thread, ())
    init_sliders()
    asyncio.run(main())