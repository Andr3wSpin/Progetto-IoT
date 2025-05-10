from machine import Pin, PWM
from time import sleep_ms


class LED:
    def __init__(self, sig_pin: int, freq: int=2000):
        self.pwm = PWM(Pin(sig_pin, Pin.OUT))
        self.pwm.freq(freq)
        self.pwm.duty(0)  # Inizialmente spento
        
    def on(self, duty: int=1023) -> None:
        self.pwm.duty(duty)

    def off(self) -> None:
        self.pwm.duty(0)
        
    def set_freq(self, freq: int) -> None:
        self.pwm.freq(freq)
            
    def fade(self, duty_min: int=0, duty_max: int=1023, resolution: int=10) -> None:
  
        for duty in range(duty_min, duty_max, resolution):  # fade in
            self.pwm.duty(duty)
            sleep_ms(10)

        for duty in range(duty_max-1, duty_min-1, -resolution):  # fade out
            self.pwm.duty(duty)
            sleep_ms(10)