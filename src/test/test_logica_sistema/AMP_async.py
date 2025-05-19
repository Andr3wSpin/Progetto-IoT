from machine import Pin, I2S
import ustruct
import uasyncio as asyncio


class AMP:
    def __init__(self, bclk_pin: int, lrclk_pin: int, din_pin: int, i2s_id: int = 0):
        self.bclk = bclk_pin
        self.lrclk = lrclk_pin
        self.din = din_pin
        self.i2s_id = i2s_id
        self.en = True

    async def play(self, filename: str, volume: int = 100) -> None:
        DIM_HEADER = 84
        self.en = True

        try:
            with open(filename, 'rb') as f:
                header = f.read(DIM_HEADER)

                audio_format = ustruct.unpack_from('<H', header, 20)[0]
                num_channels = ustruct.unpack_from('<H', header, 22)[0]
                sample_rate = ustruct.unpack_from('<I', header, 24)[0]
                bits_per_sample = ustruct.unpack_from('<H', header, 34)[0]

                if audio_format != 1:
                    raise ValueError("Formato audio non supportato: deve essere PCM (audio_format = 1)")
                if bits_per_sample != 16:
                    raise ValueError("Supportati solo file con 16 bit per sample (2 byte)")

                i2s = I2S(
                    self.i2s_id,
                    sck=Pin(self.bclk),
                    ws=Pin(self.lrclk),
                    sd=Pin(self.din),
                    mode=I2S.TX,
                    bits=16,
                    format=I2S.MONO if num_channels == 1 else I2S.STEREO,
                    rate=sample_rate,
                    ibuf=20000
                )

                f.read(100)
                counter = 0
                while self.en:
                    data = f.read(1024)
                    if not data:
                        break

                    samples = ustruct.unpack('<' + 'h' * (len(data) // 2), data)
                    scaled_data = bytearray()
                    for sample in samples:
                        scaled_sample = max(min(int(sample * volume // 100), 32767), -32768)
                        scaled_data.extend(ustruct.pack('<h', scaled_sample))

                    i2s.write(scaled_data)

                    # Cede il controllo ogni 10 blocchi (~ogni 10 * 1024 byte)
                    counter += 1
                    if counter % 10 == 0:
                        await asyncio.sleep_ms(0)

            print("Riproduzione completata.")

        except Exception as e:
            print("Errore:", str(e))
        finally:
            i2s.deinit()

    async def play_loop(self, filename: str, volume: int = 100) -> None:
        DIM_HEADER = 84
        self.en = True

        try:
            with open(filename, 'rb') as f:
                header = f.read(DIM_HEADER)

                audio_format = ustruct.unpack_from('<H', header, 20)[0]
                num_channels = ustruct.unpack_from('<H', header, 22)[0]
                sample_rate = ustruct.unpack_from('<I', header, 24)[0]
                bits_per_sample = ustruct.unpack_from('<H', header, 34)[0]

                if audio_format != 1:
                    raise ValueError("Formato audio non supportato: deve essere PCM (audio_format = 1)")
                if bits_per_sample != 16:
                    raise ValueError("Supportati solo file con 16 bit per sample (2 byte)")

                i2s = I2S(
                    self.i2s_id,
                    sck=Pin(self.bclk),
                    ws=Pin(self.lrclk),
                    sd=Pin(self.din),
                    mode=I2S.TX,
                    bits=16,
                    format=I2S.MONO if num_channels == 1 else I2S.STEREO,
                    rate=sample_rate,
                    ibuf=20000
                )

                f.read(100)
                counter = 0
                while self.en:
                    data = f.read(1024)
                    if not data:
                        f.seek(DIM_HEADER + 100)
                        continue

                    samples = ustruct.unpack('<' + 'h' * (len(data) // 2), data)
                    scaled_data = bytearray()
                    for sample in samples:
                        scaled_sample = max(min(int(sample * volume // 100), 32767), -32768)
                        scaled_data.extend(ustruct.pack('<h', scaled_sample))

                    i2s.write(scaled_data)

                    # Cede il controllo ogni 10 blocchi
                    counter += 1
                    if counter % 10 == 0:
                        await asyncio.sleep_ms(0)

            print("Riproduzione completata.")

        except Exception as e:
            print("Errore:", str(e))
        finally:
            i2s.deinit()

    def stop(self) -> None:
        self.en = False