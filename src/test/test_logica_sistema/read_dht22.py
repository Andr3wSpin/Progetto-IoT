import uasyncio as asyncio
from machine import Pin
import dht

async def read_dht22(pin_num: int, interval_s: float, callback):
    sensor = dht.DHT22(Pin(pin_num))
    while True:
        try:
            sensor.measure()
            temp = sensor.temperature()
            hum  = sensor.humidity()
            callback(temp, hum)
        except:
            callback(None, None)
        await asyncio.sleep(interval_s)