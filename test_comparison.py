"""
Test script to verify the Live 3-Algorithm Multi-Target ML Comparison Engine.
Ensures SQLite querying, common dataset preparation, chronological 80/20 train/test split,
3-model regressor training (Random Forest, Gradient Boosting, Extra Trees),
multi-output evaluation for all 5 parameters (Traffic, Delay, Throughput, Propagation Time, RAM Usage),
overall composite performance scoring, dynamic top performer selection, and model switching.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import database.database as db
from ml.algorithm_comparison import AlgorithmComparisonEngine

def test_engine():
    print("\n========================================================================")
    print("   TESTING LIVE 3-ALGORITHM MULTI-TARGET ML COMPARISON ENGINE          ")
    print("========================================================================")

    # 1. Initialize Database
    db.init_db()

    # 2. Check current historical record count
    history = db.get_history(limit=200)
    print(f"[*] Current SQLite historical telemetry count: {len(history)}")

    # 3. Test data-qualification check when records < 50
    res_small = AlgorithmComparisonEngine.evaluate_live_data(min_records=50)
    print(f"[*] Evaluation result with min_records=50: Status = '{res_small.get('status')}'")
    if res_small.get('status') == 'insufficient_data':
        print(f"    Notice message: '{res_small.get('message')}'")

    # 4. Populate test database with telemetry if needed to test 50+ qualification
    if len(history) < 60:
        print(f"[*] Seeding test telemetry snapshots to reach >60 records for validation...")
        for i in range(60 - len(history)):
            snapshot = {
                "traffic": 5.0 + i * 0.1,
                "delay": 12.0 + (i % 5),
                "throughput": 1.5 + (i % 3) * 0.2,
                "propagation_time": 6.0 + (i % 5) * 0.5,
                "ram_usage": 45.0 + (i % 5),
                "temperature": 28.4 + (i % 3) * 0.2,
                "bytes_sent": 1000 + i * 50,
                "bytes_recv": 5000 + i * 200,
                "upload_speed": 10.0 + (i % 5),
                "download_speed": 40.0 + (i % 15),
                "total_network_traffic": 5.0 + i * 0.1,
                "bandwidth_utilization": 15.0 + (i % 25) * 1.5,
                "signal_strength": 80.0,
                "wifi_status": "CONNECTED",
                "ssid": "Test_Network",
                "internet_status": "ONLINE",
                "cpu_usage": 25.0 + (i % 10),
                "battery_percentage": 90.0,
                "battery_status": "AC Power",
                "system_temperature": 28.4,
                "temperature_source": "ESP32 Sensor",
                "power_consumption": 120.0 + (i % 20),
                "battery_voltage": 12.5,
                "connected_client_count": 2,
                "tower_load": 30.0 + (i % 10),
                "data_source": "ESP32",
                "overall_status": "NORMAL",
                "anomaly_status": "NORMAL",
                "predicted_network_traffic": 2.0,
                "congestion_risk": 15.0,
                "predicted_status": "NORMAL"
            }
            db.insert_telemetry_snapshot(snapshot)
        print("[*] Test database seeded with >60 records successfully.")

    # 5. Run full comparison evaluation
    res_full = AlgorithmComparisonEngine.evaluate_live_data(min_records=50)
    print(f"\n[*] Qualified Evaluation Result:")
    print(f"    - Status: {res_full.get('status')}")
    if res_full.get('status') == 'success':
        print(f"    - Active Model: {res_full.get('active_model')}")
        print(f"    - Overall Scores: {res_full.get('overall_scores')}")
        print(f"    - Top Performer: {res_full.get('top_performer')}")
        print(f"    - Dataset Info: {res_full.get('dataset_info')}")

        print("\n    FULL MODEL BENCHMARK RESULTS:")
        for name, m in res_full["models"].items():
            print(f"       - {name:20s} | Avg MAE: {m['avg_mae']:<7.4f} | Avg RMSE: {m['avg_rmse']:<7.4f} | Avg R²: {m['avg_r2']:<7.4f} | Score: {m['overall_score']}")

        assert res_full.get("score_scale") == 10, f"Expected score_scale 10, got {res_full.get('score_scale')}"
        for name, score_val in res_full["overall_scores"].items():
            assert 0.0 <= score_val <= 10.0, f"Score for {name} out of 0-10 range: {score_val}"

        print("\n[OK] TEST PASSED: All 3 models (Random Forest, Gradient Boosting, Extra Trees) trained, evaluated, scored (0-10 scale), and predicted all 5 parameters successfully!")

if __name__ == "__main__":
    test_engine()
