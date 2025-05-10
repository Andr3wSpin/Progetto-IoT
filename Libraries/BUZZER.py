from machine import Pin, PWM
from Utility import Pointer
from time import sleep_ms


class BUZZER:
    def __init__(self, sig_pin: int):
        self.pwm = PWM(Pin(sig_pin, Pin.OUT))
        self.pwm.duty(0)  # Inizialmente spento
        
    def play(self, melodies: list, wait_ptr: Pointer, duty_ptr: Pointer) -> None:
        for note in melodies:
            if note == 0:
                self.pwm.duty(0) # Pausa
            else:
                self.pwm.freq(note)
                self.pwm.duty(duty_ptr.value) # Imposta il volume del suono
            sleep_ms(wait_ptr.value) # Durata della nota
        self.stop() # Ferma il suono alla fine
        
    def stop(self):
        self.pwm.duty(0)  # Spegne il suono