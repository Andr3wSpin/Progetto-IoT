import uasyncio as asyncio
from machine import SPI, Pin
import PN532 as pn532

class NFCReader:
    def __init__(
        self,
        sck_pin: int,
        mosi_pin: int,
        miso_pin: int,
        cs_pin: int,
        reset_pin: int,
        baudrate: int = 1_000_000,
        debug: bool = False
    ):
        # 1) Hardware SPI
        self.spi = SPI(1,
                       baudrate=baudrate,
                       polarity=0,
                       phase=0,
                       sck=Pin(sck_pin),
                       mosi=Pin(mosi_pin),
                       miso=Pin(miso_pin))
        
        self.cs = Pin(cs_pin, Pin.OUT)
        self.reset = Pin(reset_pin, Pin.OUT)
        self.debug = debug

        # 2) Istanza PN532
        self.pn = pn532.PN532(self.spi, self.cs, reset=self.reset, debug=self.debug)
        self.initialized = False

    async def monitor(self, card_callback, read_interval_s: float = 1.0):
        # 1) Inizializzazione una tantum
        if not self.initialized:
            try:
                ic, ver, rev, support = self.pn.get_firmware_version()
                if self.debug:
                    print("PN532 firmware: IC=0x{:02X}, Ver={}.{}, Support=0x{:02X}".format(ic, ver, rev, support))
                self.pn.SAM_configuration()
                self.initialized = True
            except Exception as e:
                print("Errore PN532:", e)
                return

        # 2) Polling NFC card
        while True:
            try:
                uid = self.pn.read_passive_target(timeout=500)
                if uid:
                    uid_str = "".join("{:02X}".format(b) for b in uid)
                    if self.debug:
                        print("Card UID:", uid_str)
                    card_callback(uid_str)
                else:
                    card_callback(None)
            except Exception as e:
                print("Errore lettura NFC:", e)
                card_callback(None)

            await asyncio.sleep(read_interval_s)
