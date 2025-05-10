from machine import Pin, ADC


class LDR:
    """This class read a value from a light dependent resistor (LDR)"""
    MAX_V = 4095
    MIN_V = 0

    def __init__(self, sig_pin: int):
        """
        Initializes a new instance.
        :sig_pin: ldr pin.
        """
        # initialize ADC (analog to digital conversion)
        # create an object ADC
        self.adc = ADC(Pin(sig_pin))

    def read(self) -> int:
        """
        Read a raw value from the LDR.
        :return a value from 0 to 4095.
        """
        return self.adc.read()
   
    @classmethod
    def get_max_value(cls) -> int:
        return cls.MAX_V
    
    @classmethod
    def get_min_value(cls) -> int:
        return cls.MIN_V