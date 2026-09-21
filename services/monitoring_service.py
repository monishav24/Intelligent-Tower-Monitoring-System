"""
Unified Background Monitoring Service.
Orchestrates real-time network, live Windows ARP hotspot client scanning,
internet connectivity checking, laptop system health, simulated tower parameters,
ML prediction, and SQLite database persistence.
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
from collector.hotspot_clients import get_connected_hotspot_clients
from collector.internet_checker import check_internet_connectivity
from collector.simulated_tower import SimulatedTowerCollector
from collector.esp32_collector import ESP32Collector
from ml.predictor import NetworkPredictor
from services.anomaly_detection import AnomalyDetector
from services.alert_service import AlertService

class MonitoringService:
    def __init__(self):
        self.net_collector = NetworkCollector()
        self.temp_collector = TemperatureCollector()
        self.sim_collector = SimulatedTowerCollector()
        self.esp32_collector = ESP32Collector()
        self.predictor = NetworkPredictor()
        self.anomaly_detector = AnomalyDetector()
        self.alert_service = AlertService()

        self.demo_scenario = "NORMAL"
        self.is_demo_mode = False
        self.running = False
        self.thread = None

    def set_demo_scenario(self, scenario):
        """Switch demonstration scenario override."""
        sc = scenario.upper()
        if sc == "RESET":
            self.reset_demo_mode()
            return

        self.demo_scenario = sc
        self.is_demo_mode = True
        self.sim_collector.battery_voltage = 12.60

        if sc == "HIGH_TEMPERATURE":
            self.temp_collector.enable_demo_temperature("CRITICAL")
        elif sc == "HIGH_TRAFFIC":
            self.temp_collector.enable_demo_temperature("HIGH")
        else:
            self.temp_collector.disable_demo_temperature()

        print(f"[Monitoring Service] Active Demo Mode Scenario: {self.demo_scenario}")

    def reset_demo_mode(self):
        """Reset Demo Mode and return to live monitoring."""
        self.demo_scenario = "NORMAL"
        self.is_demo_mode = False
        self.temp_collector.disable_demo_temperature()
        self.sim_collector.battery_voltage = 12.60
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
        self.net_collector.get_metrics()
        time.sleep(0.5)

        while self.running:
            try:
                ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                # 1. Real Laptop Network Data
                net_data = self.net_collector.get_metrics()

                # 2. Real Laptop Wi-Fi Signal & State
                wifi_data = get_wifi_info()

                # 3. Non-Blocking Internet Connectivity Check
                internet_status = check_internet_connectivity()

                # 4. Live Windows Hotspot Client Device Collector (ARP Scanning)
                hotspot_client_data = get_connected_hotspot_clients()
                real_client_count = hotspot_client_data["connected_client_count"]

                # Handle Demo Mode Signal & Disconnect Overrides
                if self.is_demo_mode and self.demo_scenario == "WEAK_SIGNAL":
                    wifi_data["signal_strength"] = 18.0
                    wifi_data["wifi_status"] = "CONNECTED"
                    wifi_data["connection_quality"] = "WEAK"
                elif self.is_demo_mode and self.demo_scenario == "NETWORK_DISCONNECTED":
                    wifi_data["signal_strength"] = 0.0
                    wifi_data["wifi_status"] = "DISCONNECTED"
                    wifi_data["connection_quality"] = "DISCONNECTED"
                    internet_status = "OFFLINE"

                # 5. Real Laptop System Health Data
                sys_health = get_system_health()

                # 6. Laptop Temperature Data (Fallback)
                temp_data = self.temp_collector.get_temperature()
                sys_health["system_temperature"] = temp_data["temperature"]
                sys_health["temperature_source"] = temp_data["source"]

                # 7. Simulated Tower Sensors (Tied to real hotspot device count + throughput + active scenario)
                sim_data = self.sim_collector.get_metrics(net_data, real_client_count, self.demo_scenario)

                # 8. Real ESP32 IoT Hardware Telemetry Check & Fallback
                esp32_telemetry = self.esp32_collector.get_telemetry()
                is_esp32_online = esp32_telemetry.get("is_online", False)

                if is_esp32_online:
                    # ESP32 ONLINE: Use real hardware sensor values
                    if esp32_telemetry.get("temperature") is not None:
                        sys_health["system_temperature"] = esp32_telemetry["temperature"]
                        sys_health["temperature_source"] = "ESP32 IoT Hardware"
                    
                    power_val = esp32_telemetry.get("power_w") if esp32_telemetry.get("power_w") is not None else sim_data["power_consumption"]
                    voltage_val = esp32_telemetry.get("voltage") if esp32_telemetry.get("voltage") is not None else sim_data["battery_voltage"]
                    humidity_val = esp32_telemetry.get("humidity")
                    data_source_str = "ESP32 IoT Hardware"
                else:
                    # ESP32 OFFLINE: Fallback to host laptop and tower sensors
                    power_val = sim_data["power_consumption"]
                    voltage_val = sim_data["battery_voltage"]
                    humidity_val = None
                    data_source_str = "Host Laptop"
                    if not sys_health.get("temperature_source") or "Unavailable" in sys_health.get("temperature_source", ""):
                        sys_health["temperature_source"] = "Host Laptop"

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
                    "internet_status": internet_status,
                    "cpu_usage": sys_health["cpu_usage"],
                    "ram_usage": sys_health["ram_usage"],
                    "battery_percentage": sys_health["battery_percentage"],
                    "battery_status": sys_health["battery_status"],
                    "system_temperature": sys_health["system_temperature"],
                    "temperature_source": sys_health["temperature_source"],
                    "power_consumption": power_val,
                    "battery_voltage": voltage_val,
                    "humidity": humidity_val,
                    "connected_client_count": sim_data["connected_hotspot_devices"],
                    "client_ip_list": hotspot_client_data["client_ip_list"],
                    "client_details": hotspot_client_data["client_details"],
                    "tower_load": sim_data["tower_load"],
                    "data_source": data_source_str,
                    "esp32_online": 1 if is_esp32_online else 0,
                    "is_demo_mode": 1 if self.is_demo_mode else 0,
                    "is_manual_override": 1 if self.is_demo_mode else 0,
                    "demo_scenario": self.demo_scenario,
                    "hotspot_status": hotspot_client_data["hotspot_active"],
                    "hotspot_interface": "Windows Hotspot Interface",
                    "hotspot_traffic_mb": net_data["total_network_traffic"],
                    "connection_status": hotspot_client_data["connection_status"]
                }

                # 8. Evaluate Anomaly Rules & Automatic Scenario Classification
                overall_status, anomaly_status, active_alerts, detected_scenario = self.anomaly_detector.evaluate(snapshot)
                
                # If manual override is NOT active, automatically set active scenario from real-time analysis
                if not self.is_demo_mode:
                    active_scenario = detected_scenario
                    self.demo_scenario = detected_scenario
                else:
                    active_scenario = self.demo_scenario

                snapshot["overall_status"] = overall_status
                snapshot["anomaly_status"] = anomaly_status
                snapshot["active_scenario"] = active_scenario
                snapshot["demo_scenario"] = active_scenario


                # 9. ML Traffic Prediction Engine
                predictions = self.predictor.predict(snapshot)
                snapshot["predicted_network_traffic"] = predictions["predicted_network_traffic"]
                snapshot["congestion_risk"] = predictions["congestion_risk"]
                snapshot["predicted_status"] = predictions["predicted_status"]

                # 10. Store Snapshot & Generated Alerts to Database
                db.insert_telemetry_snapshot(snapshot)
                self.alert_service.log_alerts(active_alerts)

            except Exception as e:
                print(f"[Monitoring Service Loop Error]: {e}")

            time.sleep(config.COLLECTION_INTERVAL_SECONDS)
