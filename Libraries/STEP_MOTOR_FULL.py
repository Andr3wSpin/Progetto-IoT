from machine import Pin
from utime import sleep as sleep_us
from Utility import Pointer


class STEP_MOTOR_FULL:
    def __init__(self, sig_pin1: int, sig_pin2: int, sig_pin3: int, sig_pin4: int, step_index: int=0):
        self.stepper_pins = [Pin(sig_pin1, Pin.OUT), Pin(sig_pin2, Pin.OUT), Pin(sig_pin3, Pin.OUT), Pin(sig_pin4, Pin.OUT)]
        # full-step con 2 bobbine attive
        # due bobbine accese per ogni step -> più coppia
        self.step_sequence = [
            [1, 0, 0, 1], # IN1 and IN2 on
            [1, 1, 0, 0], # IN2 and IN3 on
            [0, 1, 1, 0], # IN3 and IN4 on
            [0, 0, 1, 1], # IN4 and IN1 on
        ]
        self.step_index = step_index
    

    def step(self, direction: int, steps: int, delay_ptr: Pointer) -> None:
        if direction != 1 and direction != -1:
            raise Exception("Direction is 1 (clockwise), or -1 (counterclockwise)")
        for _ in range(steps):
            # l'operatore % garantisce che step_index rimanga all'interno dell'intervallo valido,
            # assicurando che la sequenza dei passi venga ripetuta ciclicamente.
            self.step_index = (self.step_index + direction) % len(self.step_sequence) #mod 4
            for pin_index in range(len(self.stepper_pins)):
                #Esempio: se step_index = 2, la sequenza è [0, 1, 1, 0]
                # Se pin_index = 0 → pin_value = 0
                # Se pin_index = 1 → pin_value = 1
                # ecc.
                pin_value = self.step_sequence[self.step_index][pin_index] 
                self.stepper_pins[pin_index].value(pin_value)
            sleep_us(delay_ptr.value)