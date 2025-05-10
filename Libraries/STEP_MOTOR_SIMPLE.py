from machine import Pin
from Utility import Pointer
from time import sleep


class STEP_MOTOR_SIMPLE:
    def __init__(self, sig_pin1: int, sig_pin2: int, sig_pin3: int, sig_pin4: int):
        self.stepper_pins = [Pin(sig_pin1, Pin.OUT), Pin(sig_pin2, Pin.OUT), Pin(sig_pin3, Pin.OUT), Pin(sig_pin4, Pin.OUT)]
        self.step_sequence = [[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]]

    def step(self, steps: int, delay_ptr: Pointer) -> None:
        for _ in range(steps):
            for step in self.step_sequence:
                for i in range(len(self.stepper_pins)):
                    self.stepper_pins[i].value(step[i])
                    #serve per regolare la velocità di rotazione
                    sleep(delay_ptr.value)    #0.001 