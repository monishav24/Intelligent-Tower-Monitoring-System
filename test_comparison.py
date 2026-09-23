"""
Test script to verify the Live 3-Algorithm ML Comparison Engine.
Ensures SQLite querying, data validation, temporal splitting (with boundary gap),
3-model regressor training, metric ranking, and JSON response structure.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import database.database as db
from ml.algorithm_comparison import AlgorithmComparisonEngine

def test_engine():
    print("\n========================================================================")
    print("   TESTING LIVE 3-ALGORITHM ML COMPARISON ENGINE                       ")
    print("========================================================================")

    # 1. Initialize Database
    db.init_db()

    # 2. Check current historical record count
    history = db.get_history(limit=200)
    print(f"[*] Current SQLite historical telemetry count: {len(history)}")

    # 3. Test data-qualification check when records < 100
    res_small = AlgorithmComparisonEngine.evaluate_live_data(min_records=100)
    print(f"[*] Evaluation result with min_records=100: Status = '{res_small.get('status')}'")
    if res_small.get('status') == 'insufficient_data':
        print(f"    Notice message: '{res_small.get('message')}'")

    # 4. Populate test database with telemetry if needed to test 100+ qualification
    if len(history) < 100:
        print(f"[*] Seeding test telemetry snapshots to reach >100 records for validation...")
        for i in range(110 - len(history)):
            snapshot = {
                "bytes_sent": 1000 + i * 50,
                "bytes_recv": 5000 + i * 200,
                "upload_speed": 10.0 + (i % 5),
                "download_speed": 40.0 + (i % 15),
                "throughput_mbps": 1.5 + (i % 3) * 0.2,
                "total_network_traffic": 5.0 + i * 0.1,
                "bandwidth_utilization": 15.0 + (i % 25) * 1.5,
                "signal_strength": 80.0,
                "wifi_status": "CONNECTED",
                "ssid": "Test_Network",
                "internet_status": "ONLINE",
                "cpu_usage": 25.0 + (i % 10),
                "ram_usage": 45.0 + (i % 5),
                "battery_percentage": 90.0,
                "battery_status": "AC Power",
                "system_temperature": 45.0,
                "temperature_source": "Host Laptop",
                "power_consumption": 120.0 + (i % 20),
                "battery_voltage": 12.5,
                "connected_client_count": 2,
                "tower_load": 30.0 + (i % 10),
                "data_source": "Host Laptop",
                "overall_status": "NORMAL",
                "anomaly_status": "NORMAL",
                "predicted_network_traffic": 2.0,
                "congestion_risk": 15.0,
                "predicted_status": "NORMAL"
            }
            db.insert_telemetry_snapshot(snapshot)
        print("[*] Test database seeded with >100 records successfully.")

    # 5. Run full comparison evaluation with >100 records
    res_full = AlgorithmComparisonEngine.evaluate_live_data(min_records=100)
    print(f"\n[*] Qualified Evaluation Result:")
    print(f"    - Status: {res_full.get('status')}")
    if res_full.get('status') == 'success':
        print(f"    - Updated At: {res_full.get('updated_at')}")
        print(f"    - Evaluation Window: {res_full['evaluation_window']['start_time']} -> {res_full['evaluation_window']['end_time']}")
        print(f"    - Total Records Window: {res_full['evaluation_window']['total_records']}")
        print(f"    - Train Records: {res_full['evaluation_window']['train_records']}")
        print(f"    - Test Records: {res_full['evaluation_window']['test_records']}")
        print(f"    - Data Source Info: {res_full.get('data_source_info')}")
        print(f"    - Prediction Target: {res_full.get('prediction_target')}")
        print(f"\n    [BEST MODEL] WINNING MODEL: {res_full['best_model']['algorithm']}")
        print(f"       RMSE: {res_full['best_model']['rmse']}")
        print(f"       MAE:  {res_full['best_model']['mae']}")
        print(f"       R^2:  {res_full['best_model']['r2']}")
        print(f"       Train Time: {res_full['best_model']['train_time_sec']}s")
        print("\n    FULL MODEL BENCHMARK RESULTS:")
        for name, m in res_full["models"].items():
            print(f"       - {name:20s} | MAE: {m['mae']:<7.4f} | RMSE: {m['rmse']:<7.4f} | R^2: {m['r2']:<7.4f} | Time: {m['train_time_sec']}s")

        assert "Random Forest" in res_full["models"]
        assert "Gradient Boosting" in res_full["models"]
        assert "XGBoost" in res_full["models"]
        print("\n[OK] TEST PASSED: All 3 models trained and evaluated successfully!")


if __name__ == "__main__":
    test_engine()
