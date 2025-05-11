from machine import Pin, PWM


class SERVO:
    def __init__(self, sig_pin: int, freq: int=50, duty_min: int=26, duty_max: int=128):
        if duty_min >= duty_max:
            raise Exception('Min value is greater or equal to max value')
        
        self.pwm = PWM(Pin(sig_pin), freq)
        self.duty_min = duty_min
        self.duty_max = duty_max
    
    def set_angle(self, angle: int) -> None:
        self.pwm.duty(int(self.duty_min + ((angle/180) * (self.duty_max-self.duty_min))))