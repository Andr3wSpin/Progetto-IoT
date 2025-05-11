from machine import Pin, I2C
import ssd1306
import framebuf


class DisplayUI:
    def __init__(self, scl_pin: int, sda_pin: int, i2c_id: int=0, width: int=128, height: int=64):
        """
        :scl_pin: numero del pin SCL
        :sda_pin: numero del pin SDA
        :width: larghezza display in pixel
        :height: altezza display in pixel
        """
        self.width = width
        self.height = height

        i2c = I2C(i2c_id, scl=Pin(scl_pin), sda=Pin(sda_pin))
        self.display = ssd1306.SSD1306_I2C(width, height, i2c)

    def show_image(self, image: bytearray, x: int=0, y: int=0) -> None:
        """
        Mostra un'immagine sul display.

        :image: immagine come bytearray, dimensione uguale al display (es. 1024 byte per 128x64)
        :x: posizione orizzontale in pixel
        :y: posizione verticale in pixel
        """
        fb = framebuf.FrameBuffer(image, self.width, self.height, framebuf.MONO_HLSB)
        
        self.display.blit(fb, x, y)
        self.display.show()

    def show_text(self, text: str, color: int=1, x: int=50, y: int=50) -> None:
        """
        Mostra `text` sul display.

        :text: stringa da visualizzare
        :color: colore del testo (0 o 1)
        :x: posizione orizzontale da 0 a 100
        :y: posizione verticale da 0 a 100
        """
        FONT_WIDTH = 8
        FONT_HEIGHT = 8
        # Controlli parametri
        if not (0 <= x <= 100):
            raise ValueError(f"x deve essere fra 0 e 100, {x} non valido")
        if not (0 <= y <= 100):
            raise ValueError(f"y deve essere fra 0 e 100, {y} non valido")

        text_w = len(text) * FONT_WIDTH
        text_h = FONT_HEIGHT

        x_px = (self.width - text_w) * x // 100
        y_px = (self.height - text_h) * y // 100

        x_px = min(max(0, x_px), max(0, self.width - text_w))
        y_px = min(max(0, y_px), max(0, self.height - text_h))

        self.display.text(text, x_px, y_px, color)
        self.display.show()