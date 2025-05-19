import time
from machine import SPI, Pin
import PN532 as pn532


SPI_SCK  = 18
SPI_MOSI = 16
SPI_MISO = 17
CS_PIN   = 15    # chip‐select del PN532
RESET_PIN= 7  

# 2) Inizializza l’interfaccia SPI
spi = SPI(1,
          baudrate=1_000_000,   # 1 MHz è più che sufficiente
          polarity=0,
          phase=0,
          sck=Pin(SPI_SCK),
          mosi=Pin(SPI_MOSI),
          miso=Pin(SPI_MISO))

# 3) Inizializza pin di chip‐select e reset
cs = Pin(CS_PIN, Pin.OUT)
reset = Pin(RESET_PIN, Pin.OUT)

# 4) Crea l’istanza PN532
#    debug=True per avere stampe di diagnosi sul terminale
pn = pn532.PN532(spi, cs, reset=reset, debug=False)

# 5) Verifica comunicazione e mostra versione firmware
try:
    ic, ver, rev, support = pn.get_firmware_version()
    print("PN532 firmware: IC=0x{:02X}, Ver={}.{}, Support=0x{:02X}"
          .format(ic, ver, rev, support))
except RuntimeError as e:
    print("Errore rilevamento PN532:", e)
    raise SystemExit

# 6) Configura il PN532 in modalità lettura MiFare
pn.SAM_configuration()

print("In attesa di una card NFC...")

while True:
    uid = pn.read_passive_target(timeout=500)
    if uid:
        uid_str = " ".join("{:02X}".format(b) for b in uid)
        print("Card trovata! UID:", uid_str)
    else:
        print(".", end="")  
    time.sleep(0.5)