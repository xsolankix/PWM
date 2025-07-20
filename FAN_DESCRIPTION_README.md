## Fan Control System with PWM Regulation and LCD Display

**Project Description:**  
This is a MicroPython program for a microcontroller (e.g., ESP32) that controls a fan using PWM based on temperature and humidity readings from AHT20 and BMP280 sensors. 
The system displays data on a 1602/2004 I2C LCD and uses a touch button to switch between modes and adjust the fan speed. 
The system also monitors fan RPM and features sound alerts for mode changes and critical states.

---

## Hardware Requirements

- **Microcontroller**: ESP32 (or compatible with MicroPython)
- **Display**: 1602 or 2004 LCD with I2C interface
- **Sensors**:
  - **AHT20**: Temperature and humidity sensor
  - **BMP280**: Temperature and pressure sensor
- **Fan**: Any 5V DC fan with PWM control input (3 or 4 pin fan preferred)
- **Fan RPM Sensor**: Hall effect sensor or similar for RPM feedback (optional if the fan has only 2 pins)
- **Touch Button**: Capacitive or digital for mode/speed control
- **Buzzer**: For audio feedback

---

## Pinout and Connections

| Component           | Microcontroller Pin | Notes                                      |
|---------------------|---------------------|--------------------------------------------|
| LCD SCL             | GPIO 22             | I2C clock for LCD                          |
| LCD SDA             | GPIO 21             | I2C data for LCD                           |
| Sensors SCL         | GPIO 19             | I2C clock for AHT20 and BMP280             |
| Sensors SDA         | GPIO 18             | I2C data for AHT20 and BMP280              |
| Fan PWM             | GPIO 13             | PWM output to control fan speed            |
| Touch Button        | GPIO 4              | Digital input for touch control            |
| Buzzer              | GPIO 5              | PWM output for sound alerts                |
| Fan RPM or (Sensor) | GPIO 23             | Digital input for RPM pulses (optional)    |


**Note:** Connect all I2C devices (LCD and sensors) to their respective SDA/SCL pins. 
The BMP280 should be set to address 0x77 (default). The touch button uses a pull-down resistor internally. 
The buzzer should be a piezo or similar driven by PWM. The RPM sensor (if used) should provide one pulse per revolution and connect to GPIO 23 with internal pull-up.

---

## Main Features

- **Automatic fan speed control** based on temperature ("TEMP" mode) or humidity ("HUM" mode)
- **Manual mode** ("MAN") for direct speed adjustment via the touch button
- **Fan RPM monitoring** (if sensor connected)
- **Boost mode**: Temporarily increases fan speed if RPM drops too low
- **LCD display** shows current temperature, humidity, mode, and fan speed
- **Touch button** controls modes, speed, and system lock
- **Sound alerts** for mode changes and critical states

---

## System Parameters

- **Temperature range**: 20.0°C (min) – 30.0°C (max)
- **Humidity range**: 0% (min) – 100% (max)
- **Fan speed range**: 25% (min) – 100% (max)
- **PWM frequency**: 25 kHz
- **Debounce time**: 200 ms
- **Minimum RPM for boost**: 100 RPM

---

## Usage Instructions

1. **Connect all components** according to the pinout above.
2. **Upload** the `Fan-PWM-control.py` script to your microcontroller.
3. **Ensure** all required libraries (`lib_lcd1602_2004_with_i2c`, `ahtx0`, `bmp280`) are available.
4. **Power up** the system — it will start automatically.
5. **Interact**:
   - **Short press** the touch button to cycle through modes (TEMP → MAN → HUM).
   - In **MAN** mode, short press to step the fan speed (25% → 50% → 75% → 100% → 25%...).
   - **Press and hold** (2+ seconds) to lock/unlock the system (stops/starts fan control).
6. **Monitor** temperature, humidity, and fan speed on the LCD.

---

## Troubleshooting

- **Fan does not spin**: Check PWM output and power to the fan.
- **Sensors not responding**: Verify I2C connections and addresses.
- **LCD not displaying**: Check SDA/SCL connections and power.
- **Touch button unresponsive**: Ensure proper pull-down configuration.
- **No sound from the buzzer**: Check PWM output and buzzer connection.

---

## Expansion

- Add logging or wireless control.
- Implement alarms for critical values.
- Calibrate temperature filtering as needed.

---

## Contact

For questions or improvements, open an issue or contact the repository owner.

**Thank you for using this project!**
