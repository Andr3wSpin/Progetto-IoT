import utime
from machine import reset
import micropython

from wlan_config import wlan

import esp
esp.osdebug(None)
import gc
gc.collect()

# WiFi settings
WIFI_SSID = ''
WIFI_PASSWORD = ''

timeout = 10

def restart():
    print("Impossibile connettersi al wifi. Riconessione in corso...")
    utime.sleep(2)
    reset()

wlan.active(True)
try:
    wlan.connect(WIFI_SSID, WIFI_PASSWORD)
    for _ in range(timeout):
        if wlan.isconnected():
            print("Connessione al wifi riuscita.")
            break
        utime.sleep(1)
    else:
        restart()
except OSError as e:
    restart()