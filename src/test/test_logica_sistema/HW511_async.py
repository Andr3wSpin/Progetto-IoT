import uasyncio as asyncio
from machine import Pin

class HW511:
    def __init__(self, sig_pin: int):
        self.sensor = Pin(sig_pin, Pin.IN, Pin.PULL_UP)

    def object_detected(self) -> bool:
        """
        Ritorna True se viene rilevato un oggetto, altrimenti False.
        """
        return bool(self.sensor.value())

    async def watch_on_rising(self, callback, interval_ms: int = 200):
        """
        Esegue il polling ogni `interval_ms` ms e chiama `callback()`
        solo quando lo stato passa da False a True (rising edge).
        
        :callback: funzione senza argomenti chiamata alla rilevazione
        """
        last = False
        while True:
            current = self.object_detected()
            if current and not last:
                #False -> True
                callback()
            last = current
            await asyncio.sleep_ms(interval_ms)