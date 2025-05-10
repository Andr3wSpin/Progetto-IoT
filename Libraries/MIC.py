from machine import Pin, I2S
from time import sleep_ms
import gc


class MIC:
    def __init__(self, sck_pin: int, ws_pin: int, sd_pin: int, bits_per_sample: int, format: int=I2S.MONO, sample_rate: int = 22050, buff_size: int = 4096, i2s_id: int=0):
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

    def record(self, callback, buff_size: int = 1024) -> None:
        '''Chiama una callback per ogni blocco di dati captati.

            :callback: callback da chiamare su ogni blocco di dati catturato
            :buff_size: dimensione del buffer
        '''
        self.en = True
        buf = bytearray(buff_size)
        try:
            while self.en:
                n = self.i2s.readinto(buf)
                if not n:
                    sleep_ms(1)
                callback(buf[:n])
        finally:
            self.i2s.deinit()
    
    def record_and_store(self, buff_size: int = 1024) -> bytearray:
        """
        Registra fino a stop() e restituisce tutti i dati letti come bytearray.

        :buff_size: quanti byte leggere per volta
        """
        self.en = True
        buf = bytearray(buff_size)
        data = bytearray()
        try:
            while self.en:
                n = self.i2s.readinto(buf)
                if not n:
                    sleep_ms(1)
                    continue
                try:
                    data.extend(buf[:n])
                except MemoryError:
                    # Memoria esaurita: liberiamo e rilanciamo
                    del data
                    gc.collect()
                    raise
        finally:
            self.i2s.deinit()

        return data


    def stop(self) -> None:
        '''Stoppa la registrazione'''
        self.en = False