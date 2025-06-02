import utime
from machine import reset
import micropython
import ntptime
from wlan_config import wlan

import esp
esp.osdebug(None)
import gc
gc.collect()

from DisplayUI import DisplayUI

# WiFi settings
WIFI_SSID = ''
WIFI_PASSWORD = ''

SCL_PIN = 38
SDA_PIN = 37

timeout = 10

def restart():
    utime.sleep(1)
    oled.display.fill(0)
    oled.show_text("Impossibile connettersi al wifi.")
    utime.sleep(2)
    oled.display.fill(0)
    oled.show_text("Riconessione in corso...")
    utime.sleep(2)
    reset()

oled = DisplayUI(scl_pin=SCL_PIN, sda_pin=SDA_PIN)

wlan.active(True)
try:
    wlan.connect(WIFI_SSID, WIFI_PASSWORD)
    oled.show_text("Connessione in corso...")
    for _ in range(timeout):
        if wlan.isconnected():
            oled.display.fill(0)
            break
        utime.sleep(1)
    else:
        restart()
    oled.show_text("Connessione wifi riuscita.")
    ntptime.settime() # sincronizzazione data e ora
except OSError as e:
    restart()