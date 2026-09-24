"""
ESP32 Hardware Collector Module.
Manages thread-safe in-memory telemetry state received from ESP32 IoT hardware node.
The ONLY physical hardware sensor supported is the TEMPERATURE SENSOR (DHT22/DS18B20).
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
        self.last_raw_payload = {}

    def update_telemetry(self, payload):
        """
        Validate and update in-memory telemetry from incoming HTTP POST payload.
        Parses strictly the Temperature Sensor reading (°C).
        """
        if not isinstance(payload, dict):
            return False

        with self._lock:
            self.last_seen = time.time()
            self.device_id = str(payload.get("device_id", "ESP32_TOWER_NODE_1"))
            self.last_raw_payload = payload

            # Extract & sanitize Temperature (°C) from ESP32 hardware sensor
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
                "source": "ESP32 IoT Hardware" if online else "Host Laptop"
            }
