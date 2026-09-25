/*
 * Intelligent Telecom Tower Monitoring System - ESP32 USB Serial Firmware
 * Target Microcontroller: ESP32 DevKit V1
 * Sensor: DHT22 (Temperature & Humidity Sensor)
 * Communication: USB Serial Port (JSON streaming at 115200 Baud)
 *
 * Wiring Instructions:
 * - DHT22 Data Pin  -> GPIO 4 (10k resistor to 3.3V required if 4-pin sensor module)
 * - DHT22 VCC       -> 3.3V
 * - DHT22 GND       -> GND
 * - USB Cable       -> Connected to Laptop COM Port
 *
 * Serial Output Format (JSON line every 2 seconds):
 * {"device_id":"ESP32_TOWER_NODE_1","temperature":28.6}
 */

#include <DHT.h>
#include <ArduinoJson.h>

// ================= CONFIGURATION =================
#define DEVICE_ID       "ESP32_TOWER_NODE_1"
#define DHTPIN          4
#define DHTTYPE         DHT22
#define BAUD_RATE       115200
#define READ_INTERVAL_MS 2000
// =================================================

DHT dht(DHTPIN, DHTTYPE);
unsigned long lastReadTime = 0;

void setup() {
  Serial.begin(BAUD_RATE);
  delay(1000);

  // Initialize DHT sensor
  dht.begin();
}

void loop() {
  unsigned long currentMillis = millis();
  
  if (currentMillis - lastReadTime >= READ_INTERVAL_MS) {
    lastReadTime = currentMillis;

    float temp_c = dht.readTemperature();

    // Validate sensor reading
    if (!isnan(temp_c) && temp_c >= -20.0 && temp_c <= 100.0) {
      StaticJsonDocument<128> doc;
      doc["device_id"] = DEVICE_ID;
      doc["temperature"] = round(temp_c * 10.0) / 10.0;

      String jsonOutput;
      serializeJson(doc, jsonOutput);

      // Send JSON line over USB Serial
      Serial.println(jsonOutput);
    } else {
      // Sensor reading invalid or warming up
      StaticJsonDocument<128> doc;
      doc["device_id"] = DEVICE_ID;
      doc["temperature"] = nullptr;

      String jsonOutput;
      serializeJson(doc, jsonOutput);

      Serial.println(jsonOutput);
    }
  }
}
