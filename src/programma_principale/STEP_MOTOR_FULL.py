from machine import Pin

class STEP_MOTOR_FULL:
    def __init__(self, pins):
        """
        pins: lista di oggetti Pin già configurati come Pin.OUT
        """
        self.stepper_pins = pins
        self.step_sequence = [
            [1, 0, 0, 1],
            [1, 1, 0, 0],
            [0, 1, 1, 0],
            [0, 0, 1, 1],
        ]
        self.step_index = 0

    def step_cw(self):
        """Un singolo passo in senso orario."""
        self.step_index = (self.step_index - 1) % len(self.step_sequence)
        self._write_pins()

    def step_ccw(self):
        """Un singolo passo in senso antiorario."""
        self.step_index = (self.step_index + 1) % len(self.step_sequence)
        self._write_pins()

    def _write_pins(self):
        seq = self.step_sequence[self.step_index]
        for pin, val in zip(self.stepper_pins, seq):
            pin.value(val)