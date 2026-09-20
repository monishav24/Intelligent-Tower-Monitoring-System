/*
 * Intelligent Telecom Tower Monitoring System - ESP32 IoT Firmware (Audited & Safe Version)
 * Target Microcontroller: ESP32 DevKit V1
 * Sensors: DHT22 (Temp & Humidity), INA219 (Voltage/Current/Power), 0-25V Voltage Divider (Disabled by default for safety)
 * Actuators: Green LED (Normal), Red LED (Alert), Buzzer (Critical Alarm)
 * 
 * Hardware Pin Connections:
 *  - DHT22 Data Pin  -> GPIO 4 (10k resistor to 3.3V required if 4-pin sensor; onboard if 3-pin module)
 *  - INA219 SDA      -> GPIO 21
 *  - INA219 SCL      -> GPIO 22
 *  - 0-25V Sensor S  -> GPIO 34 (DISABLED by default; Vin > 16.5V WILL DAMAGE ESP32!)
 *  - Green LED       -> GPIO 18 (via 220 ohm resistor to GND)
 *  - Red LED         -> GPIO 19 (via 220 ohm resistor to GND)
 *  - Buzzer          -> GPIO 5  (Active Buzzer to GND)
 */

#include <WiFi.h>
#include <HTTPClient.h>
#include <Wire.h>
#include <Adafruit_INA219.h>
#include <DHT.h>
#include <ArduinoJson.h>

// ================= USER CONFIGURATION =================
const char* WIFI_SSID     = "YOUR_WIFI_SSID";
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";

// Replace <LAPTOP_IP> with your laptop's Wi-Fi / Local Network IP address (e.g. http://192.168.1.100:5000/api/esp32/telemetry)
const char* SERVER_URL    = "http://192.168.1.100:5000/api/esp32/telemetry";
const char* DEVICE_ID     = "ESP32_TOWER_NODE_1";

// HARDWARE SAFETY: Set to 'true' ONLY if measuring Vin <= 16.5V max on 0-25V divider module!
#define ENABLE_ANALOG_VOLTAGE_SENSOR false
// ======================================================

// Hardware Pin Definitions
#define DHTPIN            4
#define DHTTYPE           DHT22
#define ANALOG_VOLT_PIN   34
#define GREEN_LED_PIN     18
#define RED_LED_PIN       19
#define BUZZER_PIN        5

// Sensor Objects
DHT dht(DHTPIN, DHTTYPE);
Adafruit_INA219 ina219;
bool ina219_present = false;

void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println("\n=======================================================");
  Serial.println(" ESP32 TELECOM TOWER HARDWARE NODE INITIALIZING...");
  Serial.println("=======================================================");

  // Initialize Actuator Pins
  pinMode(GREEN_LED_PIN, OUTPUT);
  pinMode(RED_LED_PIN, OUTPUT);
  pinMode(BUZZER_PIN, OUTPUT);

  digitalWrite(GREEN_LED_PIN, LOW);
  digitalWrite(RED_LED_PIN, LOW);
  digitalWrite(BUZZER_PIN, LOW);

  // Initialize Sensors
  dht.begin();
  
  Wire.begin(21, 22);
  if (ina219.begin()) {
    ina219_present = true;
    Serial.println("[SENSOR INITIALIZED] INA219 Current/Voltage Sensor Ready (SDA=21, SCL=22).");
  } else {
    ina219_present = false;
    Serial.println("[SENSOR ERROR] INA219 Sensor not detected on I2C bus. Software will report null and continue safely.");
  }

  // Connect to Wi-Fi
  Serial.print("[WIFI CONNECTING] Connecting to SSID: ");
  Serial.println(WIFI_SSID);
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 30) {
    delay(500);
    Serial.print(".");
    digitalWrite(GREEN_LED_PIN, !digitalRead(GREEN_LED_PIN)); // Blink green LED during connection setup
    attempts++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\n[WIFI CONNECTED] Wi-Fi Connected Successfully!");
    Serial.print("                 IP Address: ");
    Serial.println(WiFi.localIP());
    digitalWrite(GREEN_LED_PIN, HIGH);
  } else {
    Serial.println("\n[SERVER ERROR] Wi-Fi Connection Failed! Will retry in main loop without crashing.");
    digitalWrite(GREEN_LED_PIN, LOW);
  }
}

void loop() {
  // Ensure Wi-Fi is connected
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("[WIFI CONNECTING] Reconnecting to Wi-Fi...");
    WiFi.disconnect();
    WiFi.reconnect();
    digitalWrite(GREEN_LED_PIN, LOW);
    digitalWrite(RED_LED_PIN, HIGH);
    delay(2000);
    return;
  }

  // 1. Read DHT22 Temperature & Humidity
  float temp_c = dht.readTemperature();
  float humidity_pct = dht.readHumidity();

  bool dht_valid = true;
  if (isnan(temp_c) || isnan(humidity_pct)) {
    dht_valid = false;
    Serial.println("[SENSOR ERROR] Failed to read from DHT22 sensor!");
  }

  // 2. Read INA219 Voltage, Current, Power
  float bus_voltage_v = 0.0;
  float current_ma = 0.0;
  float power_w = 0.0;

  if (ina219_present) {
    bus_voltage_v = ina219.getBusVoltage_V();
    current_ma = ina219.getCurrent_mA();
    float power_mW = ina219.getPower_mW();
    power_w = power_mW / 1000.0;
  }

  // 3. Read Analog 0-25V Voltage Divider Sensor on GPIO 34 (Safely Disabled by default)
  float analog_voltage_v = -1.0;
  if (ENABLE_ANALOG_VOLTAGE_SENSOR) {
    int raw_adc = analogRead(ANALOG_VOLT_PIN);
    float v_out = (raw_adc * 3.3) / 4095.0;
    analog_voltage_v = v_out * 5.0; // 5:1 divider ratio
  }

  // Print local sensor diagnostic log
  Serial.println("\n--- [ESP32 Telemetry Snapshot] ---");
  if (dht_valid) {
    Serial.printf("  DHT22 Temp: %.1f °C | Humidity: %.1f %%\n", temp_c, humidity_pct);
  } else {
    Serial.println("  DHT22 Sensor: UNAVAILABLE / ERROR");
  }

  if (ina219_present) {
    Serial.printf("  INA219 Voltage: %.2f V | Current: %.1f mA | Power: %.2f W\n", bus_voltage_v, current_ma, power_w);
  } else {
    Serial.println("  INA219 Sensor: UNAVAILABLE / NOT CONNECTED");
  }

  if (ENABLE_ANALOG_VOLTAGE_SENSOR) {
    Serial.printf("  Analog Voltage (0-25V Module): %.2f V\n", analog_voltage_v);
  } else {
    Serial.println("  Analog 0-25V Sensor: DISABLED FOR HARDWARE SAFETY (Vin > 16.5V overvolts GPIO34)");
  }

  // 4. Build JSON Payload (Sends explicit JSON null for missing sensors)
  StaticJsonDocument<512> doc;
  doc["device_id"] = DEVICE_ID;
  
  if (dht_valid) {
    doc["temperature"] = round(temp_c * 10) / 10.0;
    doc["humidity"] = round(humidity_pct * 10) / 10.0;
  } else {
    doc["temperature"] = nullptr;
    doc["humidity"] = nullptr;
  }

  if (ina219_present) {
    doc["bus_voltage_v"] = round(bus_voltage_v * 100) / 100.0;
    doc["current_ma"] = round(current_ma * 10) / 10.0;
    doc["power_w"] = round(power_w * 100) / 100.0;
  } else {
    doc["bus_voltage_v"] = nullptr;
    doc["current_ma"] = nullptr;
    doc["power_w"] = nullptr;
  }

  if (ENABLE_ANALOG_VOLTAGE_SENSOR) {
    doc["analog_voltage_v"] = round(analog_voltage_v * 100) / 100.0;
  } else {
    doc["analog_voltage_v"] = nullptr;
  }

  String jsonString;
  serializeJson(doc, jsonString);

  // 5. Send HTTP POST request to Flask laptop server
  HTTPClient http;
  http.begin(SERVER_URL);
  http.addHeader("Content-Type", "application/json");
  http.setTimeout(3000); // 3.0 second HTTP timeout

  int httpResponseCode = http.POST(jsonString);

  if (httpResponseCode > 0) {
    String responseString = http.getString();
    Serial.printf("[SERVER CONNECTED] HTTP %d OK: %s\n", httpResponseCode, responseString.cbegin());

    // 6. Parse response to actuate Green LED, Red LED, and Buzzer
    StaticJsonDocument<512> responseDoc;
    DeserializationError err = deserializeJson(responseDoc, responseString);
    if (!err) {
      bool g_led = responseDoc["control"]["green_led"] | true;
      bool r_led = responseDoc["control"]["red_led"] | false;
      bool bzr   = responseDoc["control"]["buzzer"] | false;

      digitalWrite(GREEN_LED_PIN, g_led ? HIGH : LOW);
      digitalWrite(RED_LED_PIN, r_led ? HIGH : LOW);
      digitalWrite(BUZZER_PIN, bzr ? HIGH : LOW);
    }
  } else {
    Serial.printf("[SERVER ERROR] Failed to reach laptop server at %s (HTTP Code: %d)\n", SERVER_URL, httpResponseCode);
    digitalWrite(GREEN_LED_PIN, LOW);
    digitalWrite(RED_LED_PIN, HIGH);
  }

  http.end();
  delay(2000); // 2 second telemetry loop interval
}
