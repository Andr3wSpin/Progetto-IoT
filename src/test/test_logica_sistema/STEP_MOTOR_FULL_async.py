import uasyncio as asyncio
from machine import Pin

class STEP_MOTOR_FULL:
    def __init__(
        self,
        sig_pin1: int,
        sig_pin2: int,
        sig_pin3: int,
        sig_pin4: int,
        step_index: int = 0
    ):
        self.STEPS = 10        # passi totali per corsa completa
        self.DELAY = 0.001       # ritardo fra un passo e l'altro in secondi
        self.stop = False      # flag per fermare l'esecuzione

        self.stepper_pins = [
            Pin(sig_pin1, Pin.OUT),
            Pin(sig_pin2, Pin.OUT),
            Pin(sig_pin3, Pin.OUT),
            Pin(sig_pin4, Pin.OUT)
        ]
        self.step_sequence = [
            [1, 0, 0, 1],
            [1, 1, 0, 0],
            [0, 1, 1, 0],
            [0, 0, 1, 1],
        ]
        self.step_index = step_index

    async def step(self, direction: int) -> None:
        """
        Ruota il motore di `STEPS` passi nella direzione specificata
        (1 = avanti, -1 = indietro). Se in qualsiasi momento `self.stop`
        diventa True, interrompe immediatamente.
        """
        if direction not in (1, -1):
            raise ValueError("Direction must be 1 (clockwise) or -1 (counterclockwise)")

        # Reset del flag stop all'inizio di una nuova corsa
        self.stop = False

        for _ in range(self.STEPS):
            if self.stop:
                # interrompe la sequenza
                break

            # calcola indice e aggiorna pin
            self.step_index = (self.step_index + direction) % len(self.step_sequence)
            seq = self.step_sequence[self.step_index]
            for pin, val in zip(self.stepper_pins, seq):
                pin.value(val)

            # pausa non bloccante
            await asyncio.sleep(self.DELAY)

    def stop_motor(self) -> None:
        """
        Imposta il flag stop a True: 
        al prossimo passo, il metodo step() si fermerà.
        """
        self.stop = True
