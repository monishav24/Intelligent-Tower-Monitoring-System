"""
ESP32 Hardware Collector Module.
Manages thread-safe in-memory telemetry state received from ESP32 IoT hardware nodes.
Tracks packet timestamp to evaluate ONLINE vs OFFLINE fallback state.
"""
import threading
import time
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

class ESP32Collector:
    def __init__(self):
        self._lock = threading.Lock()
        self.last_seen = 0.0
        self.device_id = "ESP32_TOWER_NODE_1"
        self.temperature = None
        self.humidity = None
        self.voltage = None
        self.current_ma = None
        self.power_w = None
        self.analog_voltage = None
        self.last_raw_payload = {}

    def update_telemetry(self, payload):
        """
        Validate and update in-memory telemetry from incoming HTTP POST payload.
        Sanitizes NaN / null values.
        """
        if not isinstance(payload, dict):
            return False

        with self._lock:
            self.last_seen = time.time()
            self.device_id = str(payload.get("device_id", "ESP32_TOWER_NODE_1"))
            self.last_raw_payload = payload

            # Extract & sanitize Temperature (°C)
            temp = payload.get("temperature")
            if temp is not None:
                try:
                    f_temp = float(temp)
                    if not math.isnan(f_temp) and -20.0 <= f_temp <= 100.0:
                        self.temperature = round(f_temp, 1)
                    else:
                        self.temperature = None
                except (ValueError, TypeError):
                    self.temperature = None
            else:
                self.temperature = None

            # Extract & sanitize Humidity (%)
            hum = payload.get("humidity")
            if hum is not None:
                try:
                    f_hum = float(hum)
                    if not math.isnan(f_hum) and 0.0 <= f_hum <= 100.0:
                        self.humidity = round(f_hum, 1)
                    else:
                        self.humidity = None
                except (ValueError, TypeError):
                    self.humidity = None
            else:
                self.humidity = None

            # Extract & sanitize Bus Voltage (V) from INA219 or 0-25V sensor
            volt = payload.get("bus_voltage_v")
            if volt is None:
                volt = payload.get("voltage")
            if volt is None:
                volt = payload.get("analog_voltage_v")

            if volt is not None:
                try:
                    f_volt = float(volt)
                    if not math.isnan(f_volt) and 0.0 <= f_volt <= 50.0:
                        self.voltage = round(f_volt, 2)
                    else:
                        self.voltage = None
                except (ValueError, TypeError):
                    self.voltage = None
            else:
                self.voltage = None

            # Extract & sanitize Current (mA)
            curr = payload.get("current_ma")
            if curr is not None:
                try:
                    f_curr = float(curr)
                    if not math.isnan(f_curr):
                        self.current_ma = round(f_curr, 1)
                    else:
                        self.current_ma = None
                except (ValueError, TypeError):
                    self.current_ma = None
            else:
                self.current_ma = None

            # Extract or calculate Power (W)
            pwr = payload.get("power_w")
            if pwr is not None:
                try:
                    f_pwr = float(pwr)
                    if not math.isnan(f_pwr) and f_pwr >= 0.0:
                        self.power_w = round(f_pwr, 2)
                    else:
                        self.power_w = None
                except (ValueError, TypeError):
                    self.power_w = None
            elif self.voltage is not None and self.current_ma is not None:
                # Calculate Power = Voltage (V) * Current (A)
                calculated_power = self.voltage * (abs(self.current_ma) / 1000.0)
                self.power_w = round(calculated_power, 2)
            else:
                self.power_w = None

            # Analog Voltage Sensor (0-25V module)
            an_v = payload.get("analog_voltage_v")
            if an_v is not None:
                try:
                    f_an_v = float(an_v)
                    if not math.isnan(f_an_v):
                        self.analog_voltage = round(f_an_v, 2)
                    else:
                        self.analog_voltage = None
                except (ValueError, TypeError):
                    self.analog_voltage = None
            else:
                self.analog_voltage = None

            return True

    def is_online(self):
        """Check whether ESP32 packet was received within timeout interval."""
        with self._lock:
            if self.last_seen == 0.0:
                return False
            elapsed = time.time() - self.last_seen
            return elapsed <= getattr(config, "ESP32_TIMEOUT_SECONDS", 6.0)

    def get_telemetry(self):
        """Get copy of latest telemetry dictionary with online status."""
        with self._lock:
            online = False
            if self.last_seen > 0.0:
                elapsed = time.time() - self.last_seen
                online = elapsed <= getattr(config, "ESP32_TIMEOUT_SECONDS", 6.0)

            return {
                "is_online": online,
                "last_seen_seconds_ago": round(time.time() - self.last_seen, 1) if self.last_seen > 0 else None,
                "device_id": self.device_id,
                "temperature": self.temperature,
                "humidity": self.humidity,
                "voltage": self.voltage,
                "current_ma": self.current_ma,
                "power_w": self.power_w,
                "analog_voltage": self.analog_voltage,
                "source": "ESP32 Hardware Node" if online else "Simulated Fallback"
            }
