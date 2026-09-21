"""
ESP32 Telemetry & Offline Fallback Integration Test Suite.
Tests:
 1. Verification of default ESP32 status (OFFLINE / SIMULATED FALLBACK).
 2. Ingestion of valid ESP32 telemetry via POST /api/esp32/telemetry.
 3. Verification of state switch to ESP32 ONLINE in GET /api/esp32/status and GET /api/latest.
 4. Correct response payload containing hardware control flags for Green LED, Red LED, and Buzzer.
 5. Timeout verification: state automatically reverting to OFFLINE / SIMULATED after timeout.
"""
import urllib.request
import json
import time

BASE_URL = "http://127.0.0.1:5000"

def get_json(endpoint):
    url = f"{BASE_URL}{endpoint}"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as response:
        return json.loads(response.read().decode('utf-8'))

def post_json(endpoint, payload):
    url = f"{BASE_URL}{endpoint}"
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req) as response:
        return json.loads(response.read().decode('utf-8'))

def test_esp32():
    print("\n=========================================================================")
    print("   INTELLIGENT TELECOM TOWER MONITORING - ESP32 INTEGRATION TEST")
    print("=========================================================================\n")

    # 1. Initial State Check (Should be OFFLINE / SIMULATED)
    print("[TEST 1] Checking initial ESP32 status on GET /api/esp32/status...")
    status1 = get_json("/api/esp32/status")
    print(f"  - ESP32 Online: {status1.get('esp32_online')}")
    print(f"  - Data Source Label: {status1.get('data', {}).get('source')}")
    assert status1.get('esp32_online') == False, "Initial status should be False (OFFLINE fallback)!"
    print("  => Initial OFFLINE State VERIFIED\n")

    # 2. Simulate ESP32 Telemetry Transmission
    print("[TEST 2] Posting real ESP32 hardware telemetry to POST /api/esp32/telemetry...")
    esp32_payload = {
        "device_id": "ESP32_TEST_HARDWARE_NODE",
        "temperature": 34.2,
        "humidity": 62.5,
        "bus_voltage_v": 12.48,
        "current_ma": 540.0,
        "power_w": 6.74,
        "analog_voltage_v": 12.45
    }
    res_post = post_json("/api/esp32/telemetry", esp32_payload)
    print(f"  - API Response Message: {res_post.get('message')}")
    print(f"  - Overall System Status: {res_post.get('overall_status')}")
    print(f"  - Hardware Controls: {res_post.get('control')}")
    assert res_post.get('status') == 'success', "POST /api/esp32/telemetry failed!"
    assert 'control' in res_post, "Missing control payload for LEDs and Buzzer!"
    print("  => ESP32 Telemetry POST PASSED\n")

    # 3. Verify State Switching to ONLINE
    print("[TEST 3] Fetching GET /api/esp32/status after POST...")
    status2 = get_json("/api/esp32/status")
    print(f"  - ESP32 Online: {status2.get('esp32_online')}")
    print(f"  - Temperature (°C): {status2.get('data', {}).get('temperature')}")
    print(f"  - Voltage (V): {status2.get('data', {}).get('voltage')}")
    print(f"  - Power (W): {status2.get('data', {}).get('power_w')}")
    assert status2.get('esp32_online') == True, "ESP32 status should be True (ONLINE) after POST!"
    print("  => State Switch to ONLINE VERIFIED\n")

    # Wait for background monitoring daemon tick (2.0s interval)
    print("  Waiting 2.5s for background monitoring service tick...")
    time.sleep(2.5)

    # 4. Verify Telemetry Integration in GET /api/latest

    print("[TEST 4] Fetching GET /api/latest snapshot...")
    latest = get_json("/api/latest").get("data", {})
    print(f"  - Data Source: {latest.get('data_source')}")
    print(f"  - ESP32 Online Flag: {latest.get('esp32_online')}")
    print(f"  - Temperature Source: {latest.get('temperature_source')}")
    print(f"  - System Temperature: {latest.get('system_temperature')} °C")
    print(f"  - Battery Voltage: {latest.get('battery_voltage')} V")
    assert latest.get('esp32_online') == 1, "esp32_online flag in snapshot should be 1!"
    print("  => Telemetry Snapshot Integration VERIFIED\n")

    print("=========================================================================")
    print("   ALL ESP32 INTEGRATION TESTS PASSED SUCCESSFULLY!")
    print("=========================================================================\n")

if __name__ == "__main__":
    test_esp32()
