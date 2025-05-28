import uasyncio as asyncio
from machine import Pin

class Stoplight:
    def __init__(self, red_pin, yellow_pin, green_pin, logic_cb, poll_ms=200):
        self.red_led    = Pin(red_pin, Pin.OUT)
        self.yellow_led = Pin(yellow_pin, Pin.OUT)
        self.green_led  = Pin(green_pin, Pin.OUT)
        self.logic_cb   = logic_cb
        self.poll_ms    = poll_ms
        # inizializza LED spenti
        self._set_lights()

    def _set_lights(self, red=False, yellow=False, green=False):
        self.red_led.value(red)
        self.yellow_led.value(yellow)
        self.green_led.value(green)

    def apply_state(self, state: str):
        if state == "red":
            self._set_lights(red=True, yellow=False, green=False)
        elif state == "yellow":
            self._set_lights(red=False, yellow=True, green=False)
        elif state == "green":
            self._set_lights(red=False, yellow=False, green=True)
        else:
            # tutto spento
            self._set_lights(red=False, yellow=False, green=False)

    async def run(self):
        while True:
            state = self.logic_cb()
            self.apply_state(state)
            await asyncio.sleep_ms(self.poll_ms)

