from machine import Pin, ADC


class SENSOR:
    def __init__(self, sig_pin: int, attn: int=ADC.ATTN_11DB):
        self.vmaxi = 4095                   #Valore massimo ADC su ESP32
        self.vmaxo = 1023                   #Valore massimo per PWM su ESP32
        self.adc = ADC(Pin(sig_pin))
        self.adc.attn(attn)                #imposta l'attenuazione dell'ADC a 11dB. L'attenuazione determina l'intervallo di tensione che l'ADC può leggere. Con un'attenuazione di 11dB, l'ADC sarà in grado di leggere tensioni comprese tra 0 e 3.6V

    def read(self) -> int:
        return self.adc.read()
    
    def set_attn(self, attn: int) -> None:
        self.adc.attn(attn)