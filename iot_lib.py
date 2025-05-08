from machine import ADC, Pin, PWM
from time import sleep, sleep_ms
from utime import sleep as sleep_us


class Utility:
    def map_linear(x: int | float, x_start: int | float, x_end: int | float, y_start: int | float, y_end: int | float):
        if x_end == x_start:
            raise ValueError("x_start e x_end non possono essere uguali")

        # Calcolo del rapporto di progressione normalizzato
        ratio = (x - x_start) / (x_end - x_start)
        
        # Mappatura lineare
        y = y_start + ratio * (y_end - y_start)
        
        return y


class Pointer:
    def __init__(self, value: any):
        self.value = value


class LDR:
    """This class read a value from a light dependent resistor (LDR)"""
    MAX_V = 4095
    MIN_V = 0

    def __init__(self, sig_pin: int):
        """
        Initializes a new instance.
        :parameter pin A pin that's connected to an LDR.
        """
        # initialize ADC (analog to digital conversion)
        # create an object ADC
        self.adc = ADC(Pin(sig_pin))

    def read(self):
        """
        Read a raw value from the LDR.
        :return a value from 0 to 4095.
        """
        return self.adc.read()
   
    @classmethod
    def get_max_value(cls):
        return cls.MAX_V
    
    @classmethod
    def get_min_value(cls):
        return cls.MIN_V


class BUZZER:
    def __init__(self, sig_pin: int):
        self.pwm = PWM(Pin(sig_pin, Pin.OUT))
        self.pwm.duty(0)  # Inizialmente spento
        
    def play(self, melodies: list, wait_ptr: Pointer, duty_ptr: Pointer):
        for note in melodies:
            if note == 0:
                self.pwm.duty(0) # Pausa
            else:
                self.pwm.freq(note)
                self.pwm.duty(duty_ptr.value) # Imposta il volume del suono
            sleep_ms(wait_ptr.value) # Durata della nota
        self.stop() # Ferma il suono alla fine
        
    def stop(self):
        self.pwm.duty(0)  # Spegne il suono
    

class PASSIVE_BUZZER:
    def __init__(self, sig_pin: int, freq: int=2000):
        self.pwm = PWM(Pin(sig_pin, Pin.OUT), freq)
        self.pwm.duty(0)
    
    def set_duty(self, duty: int):
        self.pwm.duty(duty)

    def set_freq(self, freq: int):
        self.pwm.freq(freq)


class SERVO:
    def __init__(self, sig_pin: int, freq: int=50, duty_min: int=26, duty_max: int=128):
        if duty_min >= duty_max:
            raise Exception('Min value is greater or equal to max value')
        
        self.pwm = PWM(Pin(sig_pin), freq)
        self.duty_min = duty_min
        self.duty_max = duty_max
    
    def set_angle(self, angle: int):
        self.pwm.duty(int(self.duty_min + ((angle/180) * (self.duty_max-self.duty_min))))


class SENSOR:
    def __init__(self, sig_pin: int, attn: int=ADC.ATTN_11DB):
        self.vmaxi = 4095                   #Valore massimo ADC su ESP32
        self.vmaxo = 1023                   #Valore massimo per PWM su ESP32
        self.adc = ADC(Pin(sig_pin))
        self.adc.attn(attn)                #imposta l'attenuazione dell'ADC a 11dB. L'attenuazione determina l'intervallo di tensione che l'ADC può leggere. Con un'attenuazione di 11dB, l'ADC sarà in grado di leggere tensioni comprese tra 0 e 3.6V

    def read(self):
        return self.adc.read()
    
    def set_attn(self, attn: int):
        self.adc.attn(attn)


class POTENTIOMETER:
    #approssimative ranges (from micropython docs):
    #0dB : 0-1.1V
    #2.5dB : 0-1.5V
    #6dB : 0-2.2V
    #11dB : 0-3.6V
    def __init__(self, sig_pin: int, mode=Pin.IN, attn: int=ADC.ATTN_11DB, max_v: float=3.3 ,resolution=4095):   #4095 rapresentable values for 12 bit resolution
        if max_v <= 0:
            raise Exception('Min value is greater or equal to max value')
        self.max_v = max_v
        self.resolution = resolution
        self.adc = ADC(Pin(sig_pin, mode))
        self.adc.atten(attn)

    def set_attn(self, attn: int):
        self.attn = attn

    def set_max_v(self, max_v: int):
        if max_v <= 0:
            raise Exception('max_v is greater than 0')
        self.max_v = max_v
    
    def set_resolution(self, resolution: int):
        if resolution <= 0:
            raise Exception('resolution is greater than 0')
        self.resolution = resolution

    def read(self):
        return self.adc.read() * (self.max_v / self.resolution)


class LED:
    def __init__(self, sig_pin: int, freq: int=2000):
        self.pwm = PWM(Pin(sig_pin, Pin.OUT))
        self.pwm.freq(freq)
        self.pwm.duty(0)  # Inizialmente spento
        
    def on(self, duty: int=1023):
        self.pwm.duty(duty)

    def off(self):
        self.pwm.duty(0)
        
    def set_freq(self, freq: int):
        self.pwm.freq(freq)
            
    def fade(self, duty_min: int=0, duty_max: int=1023, resolution: int=10):
  
        for duty in range(duty_min, duty_max, resolution):  # fade in
            self.pwm.duty(duty)
            sleep_ms(10)

        for duty in range(duty_max-1, duty_min-1, -resolution):  # fade out
            self.pwm.duty(duty)
            sleep_ms(10)


class STEP_MOTOR_SIMPLE:
    def __init__(self, sig_pin1: int, sig_pin2: int, sig_pin3: int, sig_pin4: int):
        self.stepper_pins = [Pin(sig_pin1, Pin.OUT), Pin(sig_pin2, Pin.OUT), Pin(sig_pin3, Pin.OUT), Pin(sig_pin4, Pin.OUT)]
        self.step_sequence = [[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]]

    def step(self, steps: int, delay_ptr: Pointer):
        for _ in range(steps):
            for step in self.step_sequence:
                for i in range(len(self.stepper_pins)):
                    self.stepper_pins[i].value(step[i])
                    #serve per regolare la velocità di rotazione
                    sleep(delay_ptr.value)    #0.001 


class STEP_MOTOR_FULL:
    def __init__(self, sig_pin1: int, sig_pin2: int, sig_pin3: int, sig_pin4: int, step_index: int=0):
        self.stepper_pins = [Pin(sig_pin1, Pin.OUT), Pin(sig_pin2, Pin.OUT), Pin(sig_pin3, Pin.OUT), Pin(sig_pin4, Pin.OUT)]
        # full-step con 2 bobbine attive
        # due bobbine accese per ogni step -> più coppia
        self.step_sequence = [
            [1, 0, 0, 1], # IN1 and IN2 on
            [1, 1, 0, 0], # IN2 and IN3 on
            [0, 1, 1, 0], # IN3 and IN4 on
            [0, 0, 1, 1], # IN4 and IN1 on
        ]
        self.step_index = step_index
    

    def step(self, direction: int, steps: int, delay_ptr: Pointer):
        if direction != 1 and direction != -1:
            raise Exception("Direction is 1 (clockwise), or -1 (counterclockwise)")
        for _ in range(steps):
            # l'operatore % garantisce che step_index rimanga all'interno dell'intervallo valido,
            # assicurando che la sequenza dei passi venga ripetuta ciclicamente.
            self.step_index = (self.step_index + direction) % len(self.step_sequence) #mod 4
            for pin_index in range(len(self.stepper_pins)):
                #Esempio: se step_index = 2, la sequenza è [0, 1, 1, 0]
                # Se pin_index = 0 → pin_value = 0
                # Se pin_index = 1 → pin_value = 1
                # ecc.
                pin_value = self.step_sequence[self.step_index][pin_index] 
                self.stepper_pins[pin_index].value(pin_value)
            sleep_us(delay_ptr.value)