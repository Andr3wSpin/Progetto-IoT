from machine import Pin, ADC


class POTENTIOMETER:
    '''approssimative ranges (from micropython docs):
       0dB : 0-1.1V
       2.5dB : 0-1.5V
       6dB : 0-2.2V
       11dB : 0-3.6V'''
    def __init__(self, sig_pin: int, mode: int=Pin.IN, attn: int=ADC.ATTN_11DB, max_v: float=3.3 ,resolution: int=4095):   #4095 rapresentable values for 12 bit resolution
        if max_v <= 0:
            raise Exception('Min value is greater or equal to max value')
        self.max_v = max_v
        self.resolution = resolution
        self.adc = ADC(Pin(sig_pin, mode))
        self.adc.atten(attn)

    def set_attn(self, attn: int) -> None:
        self.attn = attn

    def set_max_v(self, max_v: int) -> None:
        if max_v <= 0:
            raise Exception('max_v is greater than 0')
        self.max_v = max_v
    
    def set_resolution(self, resolution: int) -> None:
        if resolution <= 0:
            raise Exception('resolution is greater than 0')
        self.resolution = resolution

    def read(self) -> float:
        return self.adc.read() * (self.max_v / self.resolution)