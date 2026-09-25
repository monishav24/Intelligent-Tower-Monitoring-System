"""
ESP32 USB Serial Telemetry Collector Module.
Continuously reads JSON lines from ESP32 via USB Serial COM port
and forwards parsed telemetry to the existing ESP32Collector instance.

Features:
- Background daemon thread execution (non-blocking for Flask).
- Automatic COM port reconnection handling on cable disconnect/reconnect.
- Safe JSON parsing and logging of malformed lines.
- Forwarding of valid data to ESP32Collector.update_telemetry().
"""
import threading
import time
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

try:
    import serial
except ImportError:
    serial = None


class ESP32SerialCollector:
    def __init__(self, esp32_collector, port=None, baudrate=None, enabled=None):
        self.esp32_collector = esp32_collector
        self.port = port if port is not None else getattr(config, "ESP32_SERIAL_PORT", "COM3")
        self.baudrate = baudrate if baudrate is not None else getattr(config, "ESP32_SERIAL_BAUD_RATE", 115200)
        self.enabled = enabled if enabled is not None else getattr(config, "ESP32_SERIAL_ENABLED", True)

        self.running = False
        self.thread = None
        self.serial_conn = None
        self.is_connected = False

    def start(self):
        """Start background serial reader thread if enabled."""
        if not self.enabled:
            print("[ESP32 USB] Serial collector disabled in configuration.")
            return

        if serial is None:
            print("[ESP32 USB] Warning: 'pyserial' package is not installed. Serial communication disabled.")
            return

        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._read_loop, name="ESP32SerialThread", daemon=True)
            self.thread.start()
            print(f"[ESP32 USB] Serial background reader thread started (Target Port: {self.port}, Baud: {self.baudrate}).")

    def stop(self):
        """Stop background serial reader thread and close serial port."""
        self.running = False
        if self.serial_conn and hasattr(self.serial_conn, "is_open") and self.serial_conn.is_open:
            try:
                self.serial_conn.close()
            except Exception:
                pass
        self.is_connected = False
        print("[ESP32 USB] Serial collector stopped.")

    def _read_loop(self):
        """Main loop: Connect, read, parse, and dispatch serial data."""
        while self.running:
            if not self.is_connected:
                try:
                    print(f"[ESP32 USB] Connecting to {self.port}...")
                    self.serial_conn = serial.Serial(self.port, self.baudrate, timeout=2.0)
                    self.is_connected = True
                    print(f"[ESP32 USB] Connected successfully to {self.port}.")
                except Exception as e:
                    self.is_connected = False
                    # Wait and retry without crashing app
                    time.sleep(3.0)
                    continue

            try:
                line = self.serial_conn.readline()
                if not line:
                    continue

                decoded_line = line.decode('utf-8', errors='ignore').strip()
                if not decoded_line:
                    continue

                # Parse JSON payload
                try:
                    payload = json.loads(decoded_line)
                except json.JSONDecodeError:
                    print(f"[ESP32 USB] Invalid JSON received: {decoded_line[:100]}")
                    continue

                if isinstance(payload, dict):
                    print(f"[ESP32 USB] Received: {json.dumps(payload)}")
                    success = self.esp32_collector.update_telemetry(payload)
                    if success:
                        print("[ESP32 USB] Telemetry updated successfully.")
                    else:
                        print("[ESP32 USB] Payload rejected by ESP32Collector validation.")
                else:
                    print(f"[ESP32 USB] Payload ignored (not a JSON object): {payload}")

            except (serial.SerialException, OSError) as e:
                print(f"[ESP32 USB] Serial connection lost on {self.port}. Retrying connection...")
                self.is_connected = False
                if self.serial_conn:
                    try:
                        self.serial_conn.close()
                    except Exception:
                        pass
                time.sleep(3.0)
            except Exception as e:
                print(f"[ESP32 USB] Unexpected error in serial loop: {e}")
                time.sleep(1.0)
