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

def run_tests():
    print("=========================================================================")
    print("   INTELLIGENT TELECOM TOWER MONITORING - VERIFICATION SUITE")
    print("=========================================================================\n")

    # 1. Live Telemetry Snapshot
    print("[TEST 1] Fetching /api/latest telemetry snapshot...")
    res = get_json("/api/latest")
    data = res.get("data", {})
    print(f"  - Internet Status: {data.get('internet_status')}")
    print(f"  - Local Monitoring Status: ACTIVE")
    print(f"  - Hotspot Status: {data.get('hotspot_status')}")
    print(f"  - Connected Hotspot Devices Count: {data.get('connected_client_count')}")
    print(f"  - Active Scenario (Auto-detected): {data.get('active_scenario')}")
    print(f"  - Download Speed: {data.get('download_speed')} KB/s")
    print(f"  - Temperature: {data.get('system_temperature')} °C")
    assert 'internet_status' in data, "internet_status missing!"
    assert 'connected_client_count' in data, "connected_client_count missing!"
    assert 'active_scenario' in data, "active_scenario missing!"
    print("  => /api/latest PASSED\n")

    # 2. Hotspot Endpoint Verification
    print("[TEST 2] Fetching /api/hotspot...")
    hotspot_info = get_json("/api/hotspot")
    print(f"  - Hotspot Status: {hotspot_info.get('hotspot_status')}")
    print(f"  - Connected Devices Count: {hotspot_info.get('connected_client_count')}")
    print(f"  - Client IP List: {hotspot_info.get('client_ip_list')}")
    assert 'hotspot_status' in hotspot_info, "Hotspot status key missing!"
    assert 'client_ip_list' in hotspot_info, "client_ip_list missing!"
    print("  => /api/hotspot PASSED\n")

    # 3. System Status Endpoint (Tri-Status)
    print("[TEST 3] Fetching /api/status...")
    status_info = get_json("/api/status")
    print(f"  - Overall Status: {status_info.get('overall_status')}")
    print(f"  - Internet Connectivity: {status_info.get('internet_status')}")
    print(f"  - Local Monitoring: {status_info.get('local_monitoring_status')}")
    print(f"  - Hotspot Status: {status_info.get('hotspot_status')}")
    assert status_info.get('local_monitoring_status') == 'ACTIVE', "Local monitoring status should be ACTIVE!"
    print("  => /api/status PASSED\n")

    # 4. Demo Scenarios & Manual Overrides Test (All 7 Scenarios)
    demos = [
        ("NORMAL", "Normal operation"),
        ("HIGH_TRAFFIC", "High traffic"),
        ("NETWORK_CONGESTION", "Network congestion"),
        ("WEAK_SIGNAL", "Weak signal"),
        ("HIGH_TEMPERATURE", "Thermal anomaly"),
        ("POWER_ANOMALY", "Power anomaly"),
        ("NETWORK_DISCONNECTED", "Network disconnected")
    ]

    for scenario_id, desc in demos:
        print(f"[TEST OVERRIDE] Triggering manual test override for {desc} ({scenario_id})...")
        res = post_json("/api/demo-mode", {"scenario": scenario_id})
        print(f"  - API Response: {res.get('message')}")
        time.sleep(3.0)
        
        # Verify active alerts and snapshot
        alerts = get_json("/api/alerts")
        latest = get_json("/api/latest").get("data", {})
        print(f"  - Active Scenario: {latest.get('active_scenario')}")
        print(f"  - Manual Override Flag: {latest.get('is_manual_override')}")
        print(f"  - Active Alerts Count: {alerts.get('count')}")
        assert latest.get('active_scenario') == scenario_id, f"Active scenario should be {scenario_id}, got {latest.get('active_scenario')}!"
        print(f"  => {desc} OVERRIDE VERIFIED\n")

    # Reset demo mode & verify return to automatic live detection
    print("[RESET] Resetting Manual Override back to LIVE monitoring...")
    res = post_json("/api/demo-mode/reset", {})
    print(f"  - Reset Response: {res.get('message')}")
    time.sleep(3.0)


    latest_auto = get_json("/api/latest").get("data", {})
    print(f"  - Auto-detected Scenario: {latest_auto.get('active_scenario')}")
    print(f"  - Manual Override Flag: {latest_auto.get('is_manual_override')}")
    assert latest_auto.get('is_manual_override') == 0, "Manual override flag should be 0 after reset!"
    print("  => Automatic Live Monitoring Return VERIFIED\n")

    # 5. ML Prediction Endpoint
    print("[TEST 5] Testing /api/prediction ML forecast...")
    pred = get_json("/api/prediction")
    print(f"  - Predicted Traffic: {pred.get('predicted_network_traffic_mbps')} Mbps")
    print(f"  - Congestion Risk: {pred.get('congestion_risk_pct')}%")
    print(f"  - Predicted Status: {pred.get('predicted_status')}")
    assert 'congestion_risk_pct' in pred, "Congestion risk missing!"
    print("  => /api/prediction PASSED\n")

    print("=========================================================================")
    print("   ALL VERIFICATION SCENARIOS PASSED SUCCESSFULLY!")
    print("=========================================================================")

if __name__ == "__main__":
    run_tests()

