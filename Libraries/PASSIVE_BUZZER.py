from machine import Pin, PWM


class PASSIVE_BUZZER:
    def __init__(self, sig_pin: int, freq: int=2000):
        self.pwm = PWM(Pin(sig_pin, Pin.OUT), freq)
        self.pwm.duty(0)
    
    def set_duty(self, duty: int) -> None:
        self.pwm.duty(duty)

    def set_freq(self, freq: int) -> None:
        self.pwm.freq(freq)