/*
 * Intelligent Telecom Tower Monitoring System - ESP32 USB Serial Firmware (PlatformIO)
 * Target Microcontroller: ESP32 DevKit V1
 * Sensor: DHT22 (Temperature & Humidity Sensor on GPIO 4)
 * Framework: Arduino (PlatformIO Core CLI)
 *
 * Hardware Pin Connections:
 * - DHT22 Data Pin  -> GPIO 4 (10k resistor to 3.3V required if 4-pin module)
 * - DHT22 VCC       -> 3.3V
 * - DHT22 GND       -> GND
 * - USB Cable       -> Connected to Laptop COM Port
 *
 * Serial Output Format (JSON line every 2 seconds at 115200 Baud):
 * {"device_id":"ESP32_TOWER_NODE_1","temperature":28.6}
 */

#include <Arduino.h>
#include <DHT.h>
#include <ArduinoJson.h>

// ================= CONFIGURATION =================
#define DEVICE_ID        "ESP32_TOWER_NODE_1"
#define DHTPIN           4
#define DHTTYPE          DHT22
#define BAUD_RATE        115200
#define READ_INTERVAL_MS 2000
// =================================================

DHT dht(DHTPIN, DHTTYPE);
unsigned long lastReadTime = 0;

void setup() {
    Serial.begin(BAUD_RATE);
    delay(1000);

    // Initialize DHT22 temperature sensor
    dht.begin();
}

void loop() {
    unsigned long currentMillis = millis();

    if (currentMillis - lastReadTime >= READ_INTERVAL_MS) {
        lastReadTime = currentMillis;

        float temp_c = dht.readTemperature();

        StaticJsonDocument<128> doc;
        doc["device_id"] = DEVICE_ID;

        // Validate temperature range
        if (!isnan(temp_c) && temp_c >= -20.0 && temp_c <= 100.0) {
            doc["temperature"] = round(temp_c * 10.0) / 10.0;
        } else {
            doc["temperature"] = nullptr;
        }

        String jsonOutput;
        serializeJson(doc, jsonOutput);

        // Send JSON line over USB Serial
        Serial.println(jsonOutput);
    }
}
