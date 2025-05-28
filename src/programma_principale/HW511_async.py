### HW511_async.py
import uasyncio as asyncio
from machine import Pin

class HW511:
    def __init__(self, sig_pin: int):
        # Il sensore HW511 è active-LOW: restituisce LOW quando il finecorsa è premuto
        self.sensor = Pin(sig_pin, Pin.IN, Pin.PULL_UP)

    def object_detected(self) -> bool:
        """
        Ritorna True se il finecorsa è premuto (active-LOW).
        """
        return not self.sensor.value()

    async def monitor(self, callback, interval_ms: int = 200):
        """
        Ogni `interval_ms` ms:
         - legge lo stato del finecorsa
         - stampa lo stato su console
         - invoca callback(new_state) solo se lo stato è cambiato (incluso primo ciclo)
        """
        last = None
        while True:
            current = self.object_detected()
            if last is None or current != last:
                callback(current)
            last = current
            await asyncio.sleep_ms(interval_ms)