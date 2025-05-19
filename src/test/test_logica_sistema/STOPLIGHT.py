import uasyncio as asyncio
from machine import Pin

class Stoplight:
    # Stati
    OFF    = 0
    RED    = 1
    YELLOW = 2
    GREEN  = 3

    def __init__(
        self,
        red_pin: int,
        yellow_pin: int,
        green_pin: int,
        car_present_cb,
        shutter_opening_cb,
        shutter_closing_cb,
        shutter_opened_cb,
        poll_ms: int = 200
    ):
        # LED
        self.red_led    = Pin(red_pin, Pin.OUT)
        self.yellow_led = Pin(yellow_pin, Pin.OUT)
        self.green_led  = Pin(green_pin, Pin.OUT)

        # callback di input
        self.car_present     = car_present_cb
        self.shutter_opening = shutter_opening_cb
        self.shutter_closing = shutter_closing_cb
        self.shutter_opened  = shutter_opened_cb

        self.state   = Stoplight.OFF
        self.poll_ms = poll_ms

    # Metodi per accendere i LED
    def _set_lights(self, red: bool, yellow: bool, green: bool):
        self.red_led.value(red)
        self.yellow_led.value(yellow)
        self.green_led.value(green)

    def red_light(self):
        self._set_lights(True, False, False)

    def yellow_light(self):
        self._set_lights(False, True, False)

    def green_light(self):
        self._set_lights(False, False, True)

    def off_light(self):
        self._set_lights(False, False, False)

    async def run(self):
        """
        Loop principale che valuta le transizioni e
        invoca l’azione di stato corrispondente.
        """
        while True:
            car     = self.car_present()
            opening = self.shutter_opening()
            closing = self.shutter_closing()
            opened  = self.shutter_opened()

            # --- Transizioni ---
            if self.state == Stoplight.OFF:
                if car or closing:
                    self.state = Stoplight.RED
                elif opening:
                    self.state = Stoplight.YELLOW

            elif self.state == Stoplight.RED:
                if not car and not closing:
                    self.state = Stoplight.OFF

            elif self.state == Stoplight.YELLOW:
                if car:
                    self.state = Stoplight.RED
                elif opened and not car:
                    self.state = Stoplight.GREEN

            elif self.state == Stoplight.GREEN:
                if car or closing:
                    self.state = Stoplight.RED

            # --- Azioni di uscita/stato ---
            if self.state == Stoplight.OFF:
                self.off_light()

            elif self.state == Stoplight.RED:
                self.red_light()

            elif self.state == Stoplight.YELLOW:
                self.yellow_light()

            elif self.state == Stoplight.GREEN:
                self.green_light()

            # attende prima di rivedere gli input
            await asyncio.sleep_ms(self.poll_ms)
