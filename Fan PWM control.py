from machine import Pin, SoftI2C, PWM
from lib_lcd1602_2004_with_i2c import LCD
from ahtx0 import AHT20
from bmp280 import BMP280
import uasyncio as asyncio
import time

#konfiguracja sprzętowa
I2C_LCD_SCL = 22
I2C_LCD_SDA = 21
SENSORS_SCL = 19
SENSORS_SDA = 18
FAN_PIN = 13
TOUCH_PIN = 4
BUZZER_PIN = 5

#parametry systemowe
TEMP_MIN = 20.0
TEMP_MAX = 30.0
HUM_MIN = 0.0
HUM_MAX = 100.0
MIN_SPEED = 25
FREQ_PWM = 25000
TOUCH_DEBOUNCE = 200
PWM_MAX = 1023

#stałe dla monitorowania impulsów wentylatora
FAN_RPM_PIN = 23
PULSES_PER_REVOLUTION = 1
MIN_RPM = 100

class FanRPM:
    def __init__(self, pin_num):
        self.pulse_count = 0
        self.rpm = 0
        self.last_check = time.ticks_ms()
        self.fan_pin = Pin(pin_num, Pin.IN, Pin.PULL_UP)
        self.fan_pin.irq(trigger=Pin.IRQ_FALLING, handler=self.pulse_handler)
        
    def pulse_handler(self, pin):
        self.pulse_count += 1
        
    async def monitor_rpm(self):
        while True:
            await asyncio.sleep_ms(1000)
            now = time.ticks_ms()
            time_diff = time.ticks_diff(now, self.last_check)/1000
            if time_diff > 0:
                self.rpm = (self.pulse_count / PULSES_PER_REVOLUTION) * 60 / time_diff
                self.pulse_count = 0
                self.last_check = now

class DigitalTouch:
    def __init__(self, pin_num, buzzer):
        self.touch = Pin(pin_num, Pin.IN, Pin.PULL_DOWN)
        self.last_state = False
        self.last_press_time = 0
        self.buzzer = buzzer

    def is_pressed(self):
        current_state = self.touch.value()
        now = time.ticks_ms()
        if current_state and not self.last_state:
            if time.ticks_diff(now, self.last_press_time) > TOUCH_DEBOUNCE:
                self.last_press_time = now
                self.last_state = current_state
                asyncio.create_task(self.play_beep())
                return True
        self.last_state = current_state
        return False
    
    async def play_beep(self):
        self.buzzer.freq(2000)
        self.buzzer.duty(256)
        await asyncio.sleep_ms(100)
        self.buzzer.duty(0)

class SystemSterowania:
    def __init__(self):
        self.system_active = True
        self.mode = "TEMP"
        self.fan_speed = MIN_SPEED
        self._init_hardware()
        self.buzzer = PWM(Pin(BUZZER_PIN))
        self.touch = DigitalTouch(TOUCH_PIN, self.buzzer)
        self.filtered_temp = TEMP_MIN
        self.humidity = 50.0
        self.pressure = 1000.0
        self.buzzer.duty(0)
        self.fan_rpm = FanRPM(FAN_RPM_PIN)
        self.boost_active = False

    def _init_hardware(self):
        self.i2c_lcd = SoftI2C(scl=Pin(I2C_LCD_SCL), sda=Pin(I2C_LCD_SDA))
        self.lcd = LCD(self.i2c_lcd)
        self.lcd.clear()
        self.i2c_sensors = SoftI2C(scl=Pin(SENSORS_SCL), sda=Pin(SENSORS_SDA))
        self.bmp = BMP280(self.i2c_sensors, addr=0x77)
        self.aht = AHT20(self.i2c_sensors)
        self.fan = PWM(Pin(FAN_PIN), freq=FREQ_PWM)
        self.fan.duty(0)

    async def update_display(self):
        self.lcd.clear()
        if self.system_active:
            self.lcd.puts(f"T:{self.filtered_temp:.1f}C {self.mode}", 0, 0)
            hum_str = f"H:{self.humidity:.1f}%"
            fan_str = f"FAN:{self.fan_speed:.1f}%"
            self.lcd.puts(f"{hum_str} {fan_str}", 1, 0)
        else:
            self.lcd.puts("TO UNLOCK PRESS", 0, 0)
            self.lcd.puts("BUTTON FOR 2s", 1, 0)

    async def play_mode_changed_sound(self):
        self.buzzer.freq(1500)
        self.buzzer.duty(154)
        await asyncio.sleep_ms(50)
        self.buzzer.freq(2000)
        await asyncio.sleep_ms(50)
        self.buzzer.duty(0)

    async def play_fan_changed_sound(self):
        self.buzzer.freq(1000)
        self.buzzer.duty(102)
        await asyncio.sleep_ms(30)
        self.buzzer.duty(0)
        await asyncio.sleep_ms(30)
        self.buzzer.duty(102)
        await asyncio.sleep_ms(30)
        self.buzzer.duty(0)

    async def read_sensors(self):
        last_boost = time.ticks_ms()
        while True:
            if self.system_active:
                try:
                    bmp_temp = self.bmp.temperature
                    aht_temp = self.aht.temperature
                    self.humidity = self.aht.relative_humidity
                    self.pressure = self.bmp.pressure / 100
                    current_temp = (bmp_temp + aht_temp) / 2
                    self.filtered_temp = self.filtered_temp * 0.9 + current_temp * 0.1
                    
                    if (self.fan_rpm.rpm <= MIN_RPM or self.fan_rpm.rpm == 0) and not self.boost_active:
                        self.boost_active = True
                        self.fan_speed = 90
                        self.fan.duty(int(self.fan_speed * PWM_MAX / 100))
                        last_boost = time.ticks_ms()
                        print(f"Aktywacja BOOST - RPM: {self.fan_rpm.rpm}")
                    
                    if self.boost_active:
                        if time.ticks_diff(time.ticks_ms(), last_boost) > 3000:
                            self.boost_active = False
                            print("Wyłączanie BOOST")
                        else:
                            self.fan.duty(int(90 * PWM_MAX / 100))
                    
                    if not self.boost_active:
                        if self.mode == "TEMP":
                            speed = (self.filtered_temp - TEMP_MIN) * 100 / (TEMP_MAX - TEMP_MIN)
                            self.fan_speed = max(MIN_SPEED, min(100, speed))
                        elif self.mode == "HUM":
                            speed = (self.humidity - HUM_MIN) * 100 / (HUM_MAX - HUM_MIN)
                            self.fan_speed = max(MIN_SPEED, min(100, speed))
                        self.fan.duty(int(self.fan_speed * PWM_MAX / 100))
                    await self.update_display()
                    
                except Exception as e:
                    print("Błąd czujników:", e)
                    self.system_active = False
                    self.fan.duty(0)
                    self.lcd.clear()
                    self.lcd.puts("CORR SENSORS", 0, 0)
            await asyncio.sleep(0.5)

    async def check_touch(self):
        while True:
            try:
                if self.touch.is_pressed():
                    start = time.ticks_ms()
                    while self.touch.touch.value():
                        await asyncio.sleep_ms(10)
                    
                    duration = time.ticks_diff(time.ticks_ms(), start)
                    
                    if duration > 2000:
                        self.system_active = not self.system_active
                        if not self.system_active:
                            self.fan.duty(0)
                            self.lcd.clear()
                            self.lcd.puts("TO UNLOCK PRESS", 0, 0)
                            self.lcd.puts("BUTTON FOR 2s", 1, 0)
                        else:
                            await self.update_display()
                        await self.play_mode_changed_sound()
                    
                    elif duration > 1000:
                        if self.system_active:
                            old_mode = self.mode
                            modes = ["TEMP", "MAN", "HUM"]
                            self.mode = modes[(modes.index(self.mode)+1) % 3]
                            if self.mode == "MAN":
                                self.fan_speed = MIN_SPEED
                            await self.play_mode_changed_sound()
                    
                    else:
                        if self.system_active and self.mode == "MAN":
                            old_speed = self.fan_speed
                            new_speed = old_speed + 25 if old_speed < 100 else MIN_SPEED
                            self.fan_speed = new_speed
                            if old_speed != self.fan_speed:
                                await self.play_fan_changed_sound()
                    if self.system_active:
                        await self.update_display()
                
            except Exception as e:
                print("Błąd przycisku:", e)
            await asyncio.sleep(0.1)

async def main():
    system = SystemSterowania()
    await asyncio.gather(
        system.read_sensors(),
        system.check_touch(),
        system.fan_rpm.monitor_rpm()
    )

try:
    asyncio.run(main())
except KeyboardInterrupt:
    PWM(Pin(FAN_PIN)).duty(0)
    PWM(Pin(BUZZER_PIN)).duty(0)
finally:
    asyncio.new_event_loop()

