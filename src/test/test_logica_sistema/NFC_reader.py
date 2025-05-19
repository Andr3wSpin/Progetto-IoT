import uasyncio as asyncio
from machine import SPI, Pin
import PN532 as pn532

class NFCReader:
    def __init__(
        self,
        spi_id: int,
        sck_pin: int,
        mosi_pin: int,
        miso_pin: int,
        cs_pin: int,
        reset_pin: int,
        baudrate: int = 1_000_000,
        debug: bool = False
    ):
        # 1) Inizializza SPI
        self.spi = SPI(
            spi_id,
            baudrate=baudrate,
            polarity=0,
            phase=0,
            sck=Pin(sck_pin),
            mosi=Pin(mosi_pin),
            miso=Pin(miso_pin)
        )
        # 2) CS e RESET
        self.cs = Pin(cs_pin, Pin.OUT)
        self.reset = Pin(reset_pin, Pin.OUT)
        # 3) Istanza PN532
        self.pn = pn532.PN532(self.spi, self.cs, reset=self.reset, debug=debug)

    async def monitor(self, card_callback, read_interval_s: float = 1.0):
        """
        Ogni read_interval_s secondi tenta di leggere una card.
        Se trova UID chiama card_callback(uid_str),
        altrimenti card_callback(None).
        """
        # verifica e configura
        try:
            ic, ver, rev, support = self.pn.get_firmware_version()
        except RuntimeError as e:
            print("Errore rilevamento PN532:", e)
            return

        self.pn.SAM_configuration()

        while True:
            uid = self.pn.read_passive_target(timeout=500)
            if uid:
                uid_str = "".join(f"{b:02X}" for b in uid)
                card_callback(uid_str)
            else:
                card_callback(None)
            await asyncio.sleep(read_interval_s)