"""
Unified Background Monitoring Service.
Orchestrates telemetry data collection, simulated parameters, anomaly evaluation,
ML prediction, and database persistence in a daemon thread.
Manages Demo Mode scenario overrides and resets to live monitoring.
"""
import threading
import time
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
import database.database as db
from collector.network_collector import NetworkCollector
from collector.wifi_collector import get_wifi_info
from collector.system_health import get_system_health
from collector.temperature_collector import TemperatureCollector
from collector.hotspot_monitor import get_hotspot_status
from collector.simulated_tower import SimulatedTowerCollector
from ml.predictor import NetworkPredictor
from services.anomaly_detection import AnomalyDetector
from services.alert_service import AlertService

class MonitoringService:
    def __init__(self):
        self.net_collector = NetworkCollector()
        self.temp_collector = TemperatureCollector()
        self.sim_collector = SimulatedTowerCollector()
        self.predictor = NetworkPredictor()
        self.anomaly_detector = AnomalyDetector()
        self.alert_service = AlertService()

        self.demo_scenario = "NORMAL"
        self.is_demo_mode = False
        self.running = False
        self.thread = None

    def set_demo_scenario(self, scenario):
        """
        Switch demonstration scenario override.
        Scenarios: NORMAL, HIGH_TRAFFIC, NETWORK_CONGESTION, WEAK_SIGNAL, HIGH_TEMPERATURE, POWER_ANOMALY, NETWORK_DISCONNECTED
        """
        sc = scenario.upper()
        if sc == "NORMAL" or sc == "RESET":
            self.reset_demo_mode()
            return

        self.demo_scenario = sc
        self.is_demo_mode = True

        if sc == "HIGH_TEMPERATURE":
            self.temp_collector.enable_demo_temperature("CRITICAL")
        elif sc == "HIGH_TRAFFIC":
            self.temp_collector.enable_demo_temperature("HIGH")
        else:
            self.temp_collector.disable_demo_temperature()

        print(f"[Monitoring Service] Active Demo Mode Scenario: {self.demo_scenario}")

    def reset_demo_mode(self):
        """Reset Demo Mode and return to pure live monitoring."""
        self.demo_scenario = "NORMAL"
        self.is_demo_mode = False
        self.temp_collector.disable_demo_temperature()
        print("[Monitoring Service] Returned to LIVE monitoring mode.")

    def set_max_bandwidth(self, mbps):
        """Update maximum bandwidth threshold."""
        self.net_collector.set_max_bandwidth(mbps)

    def start(self):
        """Start background collection loop in daemon thread."""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._run_loop, daemon=True)
            self.thread.start()
            print("[Monitoring Service] Telemetry daemon thread started.")

    def _run_loop(self):
        # Warmup initial counter
        self.net_collector.get_metrics()
        time.sleep(0.5)

        while self.running:
            try:
                ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                # 1. Real Laptop Network Data
                net_data = self.net_collector.get_metrics()

                # 2. Real Laptop Wi-Fi Signal & State
                wifi_data = get_wifi_info()

                # Handle Demo Mode Signal Override if applicable
                if self.is_demo_mode and self.demo_scenario == "WEAK_SIGNAL":
                    wifi_data["signal_strength"] = 18.0
                    wifi_data["wifi_status"] = "CONNECTED"
                    wifi_data["connection_quality"] = "WEAK"
                elif self.is_demo_mode and self.demo_scenario == "NETWORK_DISCONNECTED":
                    wifi_data["signal_strength"] = 0.0
                    wifi_data["wifi_status"] = "DISCONNECTED"
                    wifi_data["connection_quality"] = "DISCONNECTED"

                # 3. Real Laptop System Health Data
                sys_health = get_system_health()

                # 4. Laptop Temperature Data (Real or Fallback / Demo)
                temp_data = self.temp_collector.get_temperature()
                sys_health["system_temperature"] = temp_data["temperature"]
                sys_health["temperature_source"] = temp_data["source"]

                # 5. Mobile Hotspot Data
                hotspot_data = get_hotspot_status()

                # 6. Simulated Tower Sensors (Tied to network load + active scenario)
                sim_data = self.sim_collector.get_metrics(net_data, self.demo_scenario)

                # Combined Snapshot Object
                snapshot = {
                    "timestamp": ts,
                    "bytes_sent": net_data["bytes_sent"],
                    "bytes_recv": net_data["bytes_recv"],
                    "upload_speed": net_data["upload_speed"],
                    "download_speed": net_data["download_speed"],
                    "throughput_mbps": net_data["throughput_mbps"],
                    "total_network_traffic": net_data["total_network_traffic"],
                    "bandwidth_utilization": net_data["bandwidth_utilization"],
                    "signal_strength": wifi_data["signal_strength"],
                    "wifi_status": wifi_data["wifi_status"],
                    "ssid": wifi_data["ssid"],
                    "cpu_usage": sys_health["cpu_usage"],
                    "ram_usage": sys_health["ram_usage"],
                    "battery_percentage": sys_health["battery_percentage"],
                    "battery_status": sys_health["battery_status"],
                    "system_temperature": sys_health["system_temperature"],
                    "temperature_source": sys_health["temperature_source"],
                    "power_consumption": sim_data["power_consumption"],
                    "battery_voltage": sim_data["battery_voltage"],
                    "connected_users": sim_data["connected_users"],
                    "tower_load": sim_data["tower_load"],
                    "data_source": "Laptop Real-Time + Simulated Sensors",
                    "is_demo_mode": 1 if self.is_demo_mode else 0,
                    "demo_scenario": self.demo_scenario,
                    "hotspot_status": hotspot_data["hotspot_status"],
                    "hotspot_interface": hotspot_data["interface_name"],
                    "hotspot_traffic_mb": net_data["total_network_traffic"],
                    "hotspot_client_count": hotspot_data["client_count"],
                    "hotspot_client_details_status": hotspot_data["client_details_status"]
                }

                # 7. Evaluate Anomaly Rules & Priority Status
                overall_status, anomaly_status, active_alerts = self.anomaly_detector.evaluate(snapshot)
                snapshot["overall_status"] = overall_status
                snapshot["anomaly_status"] = anomaly_status

                # 8. ML Traffic Prediction & Congestion Engine
                predictions = self.predictor.predict(snapshot)
                snapshot["predicted_network_traffic"] = predictions["predicted_network_traffic"]
                snapshot["congestion_risk"] = predictions["congestion_risk"]
                snapshot["predicted_status"] = predictions["predicted_status"]

                # 9. Store Snapshot & Generated Alerts to Database
                db.insert_telemetry_snapshot(snapshot)
                self.alert_service.log_alerts(active_alerts)

            except Exception as e:
                print(f"[Monitoring Service Loop Error]: {e}")

            time.sleep(config.COLLECTION_INTERVAL_SECONDS)
