import ustruct
from machine import Pin, I2S

class AMP:
    def __init__(self, bclk_pin: int, lrclk_pin: int, din_pin: int, i2s_id: int = 0):
        self.bclk = bclk_pin
        self.lrclk = lrclk_pin
        self.din = din_pin
        self.i2s_id = i2s_id

    def play(self, filename: str, volume: int = 50) -> None:
        """
        Riproduce un file WAV in modo bloccante.
        Volume: 0-100
        """
        DIM_HEADER = 84
        # Apri file
        f = open(filename, 'rb')
        header = f.read(DIM_HEADER)

        # Estrai dati da header WAV
        audio_format   = ustruct.unpack_from('<H', header, 20)[0]
        num_channels   = ustruct.unpack_from('<H', header, 22)[0]
        sample_rate    = ustruct.unpack_from('<I', header, 24)[0]
        bits_per_sample= ustruct.unpack_from('<H', header, 34)[0]

        if audio_format != 1 or bits_per_sample != 16:
            f.close()
            raise ValueError('Supportati solo WAV PCM 16-bit')

        # Inizializza I2S
        i2s = I2S(
            self.i2s_id,
            sck = Pin(self.bclk),
            ws  = Pin(self.lrclk),
            sd  = Pin(self.din),
            mode=I2S.TX,
            bits=16,
            format = I2S.MONO if num_channels == 1 else I2S.STEREO,
            rate   = sample_rate,
            ibuf   = 4096
        )
        # Salta extra header
        f.read(100)

        try:
            while True:
                data = f.read(1024)
                if not data:
                    break
                # Scala volume
                samples = ustruct.unpack('<' + 'h'*(len(data)//2), data)
                buf = bytearray(len(data))
                for i, s in enumerate(samples):
                    vs = int(s * volume / 100)
                    if vs > 32767: vs = 32767
                    elif vs < -32768: vs = -32768
                    ustruct.pack_into('<h', buf, i*2, vs)
                # Scrivi su I2S
                i2s.write(buf)
        finally:
            i2s.deinit()
            f.close()