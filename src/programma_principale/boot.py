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
    oled.show_text("Impossibile")
    oled.show_text("connettersi a .",x=50,y=70)
    oled.show_text(f"{WIFI_SSID}.",x=50,y=90)
    utime.sleep(2)
    oled.display.fill(0)
    oled.show_text("Riconessione")
    oled.show_text("in corso...")
    utime.sleep(2)
    reset()

oled = DisplayUI(scl_pin=SCL_PIN, sda_pin=SDA_PIN)

wlan.active(True)
try:
    wlan.connect(WIFI_SSID, WIFI_PASSWORD)
    oled.show_text("Connessione")
    oled.show_text("in corso...",x=50,y=70)
    for _ in range(timeout):
        if wlan.isconnected():
            oled.display.fill(0)
            break
        utime.sleep(1)
    else:
        restart()
    oled.show_text("Connesso a ")
    oled.show_text(f"{WIFI_SSID}",x=50,y=70)
    ntptime.settime() # sincronizzazione data e ora
except OSError as e:
    restart()

