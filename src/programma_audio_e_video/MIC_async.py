import uasyncio as asyncio
from machine import Pin, I2S
import gc


class MIC:
    def __init__(
        self,
        sck_pin: int,
        ws_pin: int,
        sd_pin: int,
        bits_per_sample: int,
        format: int = I2S.MONO,
        sample_rate: int = 22050,
        buff_size: int = 4096,
        i2s_id: int = 0
    ):
        self.i2s = I2S(
            i2s_id,
            sck    = Pin(sck_pin),
            ws     = Pin(ws_pin),
            sd     = Pin(sd_pin),
            mode   = I2S.RX,
            bits   = bits_per_sample,
            format = format,
            rate   = sample_rate,
            ibuf   = buff_size
        )
        self.en = True

    async def record(self, callback, buff_size: int = 1024) -> None:
        """
        Metodo async: chiama `callback(data)` per ogni blocco di dati
        letti da I2S. Cede il controllo se non ci sono dati.
        """
        self.en = True
        buf = bytearray(buff_size)
        try:
            while self.en:
                n = self.i2s.readinto(buf)
                if n:
                    # chiama callback con i soli byte letti
                    callback(buf[:n])
                    # piccola cessione opzionale ogni iterazione
                    await asyncio.sleep_ms(0)
                else:
                    # nessun dato: cedi controllo per 1 ms
                    await asyncio.sleep_ms(1)
        finally:
            self.i2s.deinit()

    async def record_and_store(self, buff_size: int = 1024) -> bytearray:
        """
        Metodo async: registra fino a stop() e restituisce tutti i dati letti.
        """
        self.en = True
        buf = bytearray(buff_size)
        data = bytearray()
        try:
            while self.en:
                n = self.i2s.readinto(buf)
                if n:
                    # accumula i dati
                    try:
                        data.extend(buf[:n])
                    except MemoryError:
                        # gestione out of memory
                        del data
                        gc.collect()
                        raise
                    await asyncio.sleep_ms(0)
                else:
                    await asyncio.sleep_ms(1)
        finally:
            self.i2s.deinit()

        return data

    def stop(self) -> None:
        """Ferma la registrazione async."""
        self.en = False
