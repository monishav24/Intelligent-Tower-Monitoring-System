# ESP32 IoT Hardware Integration Guide

This directory contains the firmware sketch for integrating real ESP32 microcontroller hardware into the **Intelligent Telecom Tower Monitoring and Alert System**.

---

## 1. Hardware Pinout & Circuit Wiring Table

| Component | ESP32 DevKit V1 Pin | Notes / Resistors |
| :--- | :--- | :--- |
| **DHT22 Data** | `GPIO 4` | Pull-up resistor (4.7k or 10k) to 3.3V |
| **DHT22 VCC / GND** | `3.3V` / `GND` | Power from ESP32 3.3V rail |
| **INA219 SDA** | `GPIO 21` | I2C Data |
| **INA219 SCL** | `GPIO 22` | I2C Clock |
| **INA219 VCC / GND**| `3.3V` or `5V` / `GND` | Connected across monitored DC load |
| **0-25V Sensor (Signal)**| `GPIO 34` | Analog ADC pin |
| **Green LED** | `GPIO 18` | Anode to GPIO 18, Cathode via 220Ω resistor to GND |
| **Red LED** | `GPIO 19` | Anode to GPIO 19, Cathode via 220Ω resistor to GND |
| **Buzzer** | `GPIO 5` | Active Buzzer positive to GPIO 5, negative to GND |

---

## 2. Required Arduino IDE Libraries

Install the following libraries via **Arduino IDE -> Tools -> Manage Libraries...**:
1. `Adafruit INA219` by Adafruit
2. `DHT sensor library` by Adafruit
3. `Adafruit Unified Sensor` by Adafruit
4. `ArduinoJson` (v6.x) by Benoit Blanchon

---

## 3. Flashing & Setup Instructions

1. Open `esp32_firmware.ino` in Arduino IDE.
2. Select Board: **ESP32 Dev Module** (or **ESP32 WROOM DA Module**).
3. Set `WIFI_SSID` and `WIFI_PASSWORD` in `esp32_firmware.ino` to match your local Wi-Fi router or laptop hotspot.
4. Set `SERVER_URL` to your laptop's IP address:
   `http://<YOUR_LAPTOP_IP>:5000/api/esp32/telemetry`
5. Upload sketch to ESP32 via USB cable.
6. Open Serial Monitor at **115200 baud** to view real-time HTTP POST transmissions.

---

## 4. Hardware Actuator Behavior

- **Green LED ON**: System overall status is `NORMAL`.
- **Red LED ON**: System status is `WARNING` or `CRITICAL` or `DISCONNECTED`.
- **Buzzer SOUNDS**: System status is `CRITICAL` (e.g. overheating, low battery voltage, power surge, or network disconnection).
