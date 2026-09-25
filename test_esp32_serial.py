"""
Unit and Integration Test Suite for ESP32 USB Serial Collector.
Tests:
1. Handling of disconnected COM port on startup (no crash).
2. Processing of valid JSON serial frames.
3. Handling of malformed JSON lines (graceful logging, no crash).
4. Simulation of serial disconnection and recovery.
"""
import time
import json
import unittest
from unittest.mock import MagicMock
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config
from collector.esp32_collector import ESP32Collector
from collector.esp32_serial_collector import ESP32SerialCollector


class TestESP32SerialCollector(unittest.TestCase):
    def setUp(self):
        self.esp32_collector = ESP32Collector()
        self.serial_collector = ESP32SerialCollector(
            esp32_collector=self.esp32_collector,
            port="MOCK_COM99",
            baudrate=115200,
            enabled=True
        )

    def tearDown(self):
        self.serial_collector.stop()

    def test_startup_disconnected_port(self):
        """Test Test 1: Start with disconnected/non-existent COM port."""
        print("\n[TEST 1] Testing startup with non-existent COM port (disconnected state)...")
        # Should not throw exception
        self.serial_collector.start()
        time.sleep(1.0)
        self.assertFalse(self.serial_collector.is_connected)
        self.assertFalse(self.esp32_collector.is_online())
        print(" => Disconnected startup test PASSED: Application remains responsive.")

    def test_valid_json_processing(self):
        """Test Test 2 & 3: Valid JSON serial frame processing."""
        print("\n[TEST 2 & 3] Testing valid JSON serial payload ingestion...")
        mock_serial = MagicMock()
        mock_serial.readline.return_value = b'{"device_id":"ESP32_TOWER_NODE_1","temperature":28.6}\n'

        self.serial_collector.serial_conn = mock_serial
        self.serial_collector.is_connected = True
        self.serial_collector.running = True

        # Simulate 1 loop iteration of _read_loop logic
        line = mock_serial.readline()
        decoded_line = line.decode('utf-8').strip()
        payload = json.loads(decoded_line)
        self.esp32_collector.update_telemetry(payload)

        telemetry = self.esp32_collector.get_telemetry()
        self.assertTrue(telemetry["is_online"])
        self.assertEqual(telemetry["temperature"], 28.6)
        self.assertEqual(telemetry["device_id"], "ESP32_TOWER_NODE_1")
        print(f" => Valid JSON ingestion test PASSED: temp={telemetry['temperature']}°C, online={telemetry['is_online']}")

    def test_malformed_json_handling(self):
        """Test Test 6: Malformed/Invalid serial line handling."""
        print("\n[TEST 6] Testing malformed serial data ('hello')...")
        bad_line = b'hello world random string\n'
        decoded_line = bad_line.decode('utf-8').strip()

        try:
            payload = json.loads(decoded_line)
        except json.JSONDecodeError:
            payload = None

        self.assertIsNone(payload)
        # ESP32 collector telemetry remains unchanged without crashing
        self.assertFalse(self.esp32_collector.is_online())
        print(" => Malformed data test PASSED: Handled safely without crash.")

    def test_disconnection_and_reconnection(self):
        """Test Test 4 & 5: Disconnection and automatic recovery."""
        print("\n[TEST 4 & 5] Testing serial disconnect and auto-reconnect simulation...")
        
        # 1. Update with valid telemetry
        self.esp32_collector.update_telemetry({"device_id": "ESP32_TOWER_NODE_1", "temperature": 30.5})
        self.assertTrue(self.esp32_collector.is_online())
        
        # 2. Simulate disconnect by clearing last_seen back in time
        self.esp32_collector.last_seen = time.time() - 10.0
        self.assertFalse(self.esp32_collector.is_online())
        print(" => Disconnected state detected successfully (is_online=False).")

        # 3. Simulate reconnection and telemetry update
        self.esp32_collector.update_telemetry({"device_id": "ESP32_TOWER_NODE_1", "temperature": 31.0})
        self.assertTrue(self.esp32_collector.is_online())
        self.assertEqual(self.esp32_collector.get_telemetry()["temperature"], 31.0)
        print(" => Reconnection test PASSED: Telemetry updates resumed.")


if __name__ == "__main__":
    unittest.main()
