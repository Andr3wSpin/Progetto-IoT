from machine import Pin


class HW511:
    def __init__(self, sig_pin: int):
        self.sensor = Pin(sig_pin, Pin.IN, Pin.PULL_UP)
    
    def object_detected(self) -> bool:
        '''
        Restituisce True se viene rilevato un oggetto, altrimenti False
        '''
        return bool(self.sensor.value())