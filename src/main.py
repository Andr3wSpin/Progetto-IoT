import network
import time
import ujson
from umqtt.simple import MQTTClient
import dht
import libs

# valori massimi di temperatura e umidità
MAX_TEMP = 25
MAX_HUM = 30

'''
QUESTA SEZIONE VA TUTTA NEL FILE boot.py

# parametri server MQTT
MQTT_CLIENT_ID = ""
MQTT_BROKER    = ""
MQTT_USER      = ""
MQTT_PASSWORD  = "" 

# definzione topic (aggiungere altri topic)
MQTT_TOPIC     = ""
MQTT_TOPIC_SUB_1 = ""
'''

def nfc_handler(msg):
    # gestisce i messaggi ricevuti da NodeRed relativi al sensore NFC
    pass

def dht_handler(msg):
    # aggiorna MAX_TEMP e MAX_HUM in base ai valori ricevuti per messaggio
    data = ujson.loads(msg)

    if 'max_temp' in data:
        MAX_TEMP = data['max_temp']
        
    if 'max_hum' in data:
        MAX_HUM = data['max_hum']

def sub_callback(topic, msg):
    # richiama l'handler associato al topic del messaggio ricevuto
    pass

def connect_and_subscribe():
    global client_id, mqtt_server, topic_list

    client = MQTTClient(client_id, mqtt_server)
    client.set_callback(sub_callback)
    client.connect()
 
    for topic in topic_list:
        client.subscribe(topic)

    print('Connessione al broker completata.')

    return client

def restart_and_reconnect():
    print('Errore durante la connessione con il broker MQTT. Riconessione in corso...')
    time.sleep(10)
    machine.reset()

try:
    client = connect_and_subscribe()
except OSError as e:
    restart_and_reconnect()

while True:
    client.check_msg()