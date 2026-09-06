"""
Main Application Entry Point for Intelligent Telecom Tower Monitoring & Alert System.
Initializes Flask web server, SQLite database, background telemetry collection thread,
and registers REST API routes.
"""
import threading
import time
from datetime import datetime
from flask import Flask, render_template, jsonify

import config
import database.database as db
from collector.network_collector import NetworkCollector
from collector.wifi_signal import get_wifi_signal_strength
from collector.simulated_tower_data import SimulatedTowerCollector
from ml.predictor import NetworkPredictor
from ml.anomaly_detection import AnomalyDetector
from routes.api import api_bp

app = Flask(__name__)
app.register_blueprint(api_bp)

# Global background collector state
network_collector = NetworkCollector()
simulated_collector = SimulatedTowerCollector()
predictor = NetworkPredictor()
anomaly_detector = AnomalyDetector()

current_demo_scenario = "NORMAL"

def update_demo_scenario(scenario):
    """Callback to update active demo mode scenario."""
    global current_demo_scenario
    current_demo_scenario = scenario
    print(f"[Demo Mode] Active scenario changed to: {current_demo_scenario}")

def set_max_bandwidth(mbps):
    """Callback to update maximum bandwidth threshold."""
    global network_collector
    network_collector.set_max_bandwidth(mbps)
    print(f"[Config] Max bandwidth updated to: {mbps} Mbps")

def telemetry_background_loop():
    """
    Background worker thread running every 2 seconds.
    Collects real laptop network metrics + simulated hardware metrics,
    evaluates ML predictions & anomaly rules, and stores to SQLite.
    """
    print("[Telemetry Loop] Background collection loop started...")
    
    # Pre-warm collector with initial reading
    network_collector.get_network_metrics()
    time.sleep(0.5)

    while True:
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # 1. Collect Real-Time Laptop Network Metrics
            net_metrics = network_collector.get_network_metrics()

            # 2. Collect Real-Time Wi-Fi Signal Strength
            wifi_signal, wifi_status = get_wifi_signal_strength()

            # 3. Collect Simulated Hardware Sensors (tied to network load + demo scenario)
            sim_metrics = simulated_collector.get_simulated_metrics(net_metrics, current_demo_scenario)

            # Override Wi-Fi signal if demo scenario explicitly overrides it
            if sim_metrics.get("signal_override") is not None:
                wifi_signal = sim_metrics["signal_override"]

            # Combined Reading Dict
            raw_reading = {
                "timestamp": timestamp,
                "temperature": sim_metrics["temperature"],
                "power_consumption": sim_metrics["power_consumption"],
                "battery_voltage": sim_metrics["battery_voltage"],
                "bytes_sent": net_metrics["bytes_sent"],
                "bytes_recv": net_metrics["bytes_recv"],
                "upload_speed": net_metrics["upload_speed_kbps"],
                "download_speed": net_metrics["download_speed_kbps"],
                "throughput_mbps": net_metrics["throughput_mbps"],
                "total_traffic_mb": net_metrics["total_traffic_mb"],
                "bandwidth_utilization": net_metrics["bandwidth_utilization"],
                "signal_strength": wifi_signal,
                "connected_users": sim_metrics["connected_users"],
                "tower_load": sim_metrics["tower_load"],
                "is_demo_mode": 1 if current_demo_scenario != "NORMAL" else 0,
                "demo_scenario": current_demo_scenario
            }

            # 4. Evaluate Anomaly Rules & Overall Status
            overall_status, anomaly_status, active_alerts = anomaly_detector.evaluate_reading(raw_reading)
            raw_reading["tower_status"] = overall_status
            raw_reading["anomaly_status"] = anomaly_status

            # 5. Run ML Prediction Engine (Random Forest)
            predictions = predictor.predict(raw_reading)
            raw_reading["predicted_traffic"] = predictions["predicted_traffic_mbps"]
            raw_reading["congestion_risk"] = predictions["congestion_risk"]
            raw_reading["predicted_status"] = predictions["predicted_status"]

            # 6. Save Reading & Generated Alerts to Database
            db.insert_reading(raw_reading)
            for alert in active_alerts:
                db.insert_alert(alert)

        except Exception as e:
            print(f"[Telemetry Loop Error]: {e}")

        time.sleep(config.COLLECTION_INTERVAL_SECONDS)

@app.route("/")
def index():
    """Render main dashboard web interface."""
    return render_template("index.html", metadata=config.SYSTEM_METADATA)

if __name__ == "__main__":
    # Initialize SQLite tables
    db.init_db()

    # Launch background telemetry thread
    telemetry_thread = threading.Thread(target=telemetry_background_loop, daemon=True)
    telemetry_thread.start()

    print("\n========================================================")
    print("  INTELLIGENT TELECOM TOWER MONITORING & ALERT SYSTEM   ")
    print("========================================================")
    print("  Status: Server running on http://127.0.0.1:5000       ")
    print("========================================================\n")

    app.run(host="0.0.0.0", port=5000, debug=False)
