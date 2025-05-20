
import network
import urandom
import time
from umqtt.simple import MQTTClient
import machine
import ubinascii
import ujson





# Feed/topic da usare
DHT_TOPIC = f"{AIO_USER}/feeds/DHT"
READ_NFC_TOPIC = f"{AIO_USER}/feeds/READNFC"
CHECK_NFC_TOPIC = f"{AIO_USER}/feeds/CHECK_NFC"
MOTOR_TOPIC = f"{AIO_USER}/feeds/MOTOR"


# Connessione WiFi
def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print("Connessione al WiFi...")
        wlan.connect(WIFI_SSID, pw )
        while not wlan.isconnected():
            time.sleep(0.5)
    print("✅ WiFi connesso:", wlan.ifconfig())

# Setup MQTT client
def setup_mqtt():
    client_id = ubinascii.hexlify(machine.unique_id())
    client = MQTTClient(client_id, BROKER, PORT, AIO_USER, AIO_KEY)
    client.connect()
    print("Connesso a Adafruit IO MQTT")
    return client

# MAIN
connect_wifi()
client = setup_mqtt()
