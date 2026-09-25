"""
Unified Background Monitoring Service.
Orchestrates real-time network, delay/latency ping measurement, estimated propagation time (RTT/2),
live Windows ARP hotspot client scanning, internet connectivity checking, laptop system health,
hardware ESP32 temperature collector, multi-target ML predictions, and SQLite persistence.
Inserts a NEW SQLite row on every collection cycle (2 seconds).
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
from collector.delay_collector import DelayCollector
from collector.hotspot_clients import get_connected_hotspot_clients
from collector.internet_checker import check_internet_connectivity
from collector.simulated_tower import SimulatedTowerCollector
from collector.esp32_collector import ESP32Collector
from collector.esp32_serial_collector import ESP32SerialCollector
from ml.predictor import NetworkPredictor
from services.anomaly_detection import AnomalyDetector
from services.alert_service import AlertService

class MonitoringService:
    def __init__(self):
        self.net_collector = NetworkCollector()
        self.delay_collector = DelayCollector()
        self.temp_collector = TemperatureCollector()
        self.sim_collector = SimulatedTowerCollector()
        self.esp32_collector = ESP32Collector()
        self.esp32_serial_collector = ESP32SerialCollector(self.esp32_collector)
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
            print("[Monitoring Service] Telemetry daemon thread started (2.0s interval).")
            self.esp32_serial_collector.start()

    def stop(self):
        """Stop background collection and serial reader threads."""
        self.running = False
        if hasattr(self, 'esp32_serial_collector'):
            self.esp32_serial_collector.stop()

    def _run_loop(self):
        # Warmup network collector
        self.net_collector.get_metrics()
        time.sleep(0.5)

        while self.running:
            try:
                ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                # 1. Real Laptop Network Data (Fresh Measurement)
                net_data = self.net_collector.get_metrics()

                # 2. Live Ping Latency & Estimated Propagation Time (RTT / 2)
                delay_metrics = self.delay_collector.measure_delay()

                # 3. Real Laptop Wi-Fi Signal & State
                wifi_data = get_wifi_info()

                # 4. Non-Blocking Internet Connectivity Check
                internet_status = check_internet_connectivity()

                # 5. Live Windows Hotspot Client Device Collector (ARP Scanning)
                hotspot_client_data = get_connected_hotspot_clients()
                real_client_count = hotspot_client_data["connected_client_count"]

                # Handle Demo Mode Overrides
                if self.is_demo_mode and self.demo_scenario == "WEAK_SIGNAL":
                    wifi_data["signal_strength"] = 18.0
                    wifi_data["wifi_status"] = "CONNECTED"
                elif self.is_demo_mode and self.demo_scenario == "NETWORK_DISCONNECTED":
                    wifi_data["signal_strength"] = 0.0
                    wifi_data["wifi_status"] = "DISCONNECTED"
                    internet_status = "OFFLINE"

                # 6. Real Laptop System Health Data (Fresh Measurement)
                sys_health = get_system_health()

                # 7. Temperature Collector (ESP32 or Laptop Fallback)
                temp_data = self.temp_collector.get_temperature()
                raw_temp = temp_data.get("temperature")
                temp_source = temp_data.get("source", "Host Laptop Fallback")

                # 8. Simulated Tower Metrics
                sim_data = self.sim_collector.get_metrics(net_data, real_client_count, self.demo_scenario)

                # 9. Real ESP32 Hardware Check
                esp32_telemetry = self.esp32_collector.get_telemetry()
                is_esp32_online = esp32_telemetry.get("is_online", False)

                if is_esp32_online and esp32_telemetry.get("temperature") is not None:
                    raw_temp = esp32_telemetry["temperature"]
                    temp_source = "ESP32 Temperature Sensor (DHT22/DS18B20)"
                    data_source_str = "ESP32 IoT Hardware"
                else:
                    data_source_str = "Host Laptop"

                # Safely parse numeric parameters without throwing TypeError on None
                traffic_val = round(float(net_data.get("total_network_traffic", 0.0) or 0.0), 2)
                delay_val = round(float(delay_metrics.get("delay_ms", 1.0) or 1.0), 2)
                throughput_val = round(float(net_data.get("throughput_mbps", 0.0) or 0.0), 3)
                prop_val = round(float(delay_metrics.get("propagation_time_ms", 0.5) or 0.5), 2)
                ram_val = round(float(sys_health.get("ram_usage", 0.0) or 0.0), 1)

                if raw_temp is not None:
                    try:
                        temp_val = round(float(raw_temp), 1)
                    except (ValueError, TypeError):
                        temp_val = None
                else:
                    temp_val = None

                # Combined Snapshot Object
                snapshot = {
                    "timestamp": ts,

                    # 5 ML Parameters
                    "traffic": traffic_val,
                    "delay": delay_val,
                    "delay_ms": delay_val,
                    "throughput": throughput_val,
                    "throughput_mbps": throughput_val,
                    "propagation_time": prop_val,
                    "propagation_time_ms": prop_val,
                    "ram_usage": ram_val,

                    # Hardware Sensor (Temperature Sensor ONLY)
                    "temperature": temp_val,
                    "system_temperature": temp_val,
                    "temperature_source": temp_source,

                    "bytes_sent": net_data["bytes_sent"],
                    "bytes_recv": net_data["bytes_recv"],
                    "upload_speed": net_data["upload_speed"],
                    "download_speed": net_data["download_speed"],
                    "total_network_traffic": traffic_val,
                    "bandwidth_utilization": net_data["bandwidth_utilization"],
                    "signal_strength": wifi_data["signal_strength"],
                    "wifi_status": wifi_data["wifi_status"],
                    "ssid": wifi_data["ssid"],
                    "internet_status": internet_status,
                    "cpu_usage": sys_health["cpu_usage"],
                    "battery_percentage": sys_health["battery_percentage"],
                    "battery_status": sys_health["battery_status"],
                    "power_consumption": sim_data["power_consumption"],
                    "battery_voltage": sim_data["battery_voltage"],
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
                    "hotspot_traffic_mb": traffic_val,
                    "connection_status": hotspot_client_data["connection_status"]
                }

                # Evaluate Anomaly Rules
                overall_status, anomaly_status, active_alerts, detected_scenario = self.anomaly_detector.evaluate(snapshot)

                if not self.is_demo_mode:
                    active_scenario = detected_scenario
                    self.demo_scenario = detected_scenario
                else:
                    active_scenario = self.demo_scenario

                snapshot["overall_status"] = overall_status
                snapshot["anomaly_status"] = anomaly_status
                snapshot["active_scenario"] = active_scenario
                snapshot["demo_scenario"] = active_scenario

                # Multi-Target ML Predictions
                predictions = self.predictor.predict(snapshot)
                snapshot["predicted_traffic"] = predictions.get("predicted_traffic", 0.0)
                snapshot["predicted_network_traffic"] = predictions.get("predicted_traffic", 0.0)
                snapshot["predicted_delay"] = predictions.get("predicted_delay", 0.0)
                snapshot["predicted_throughput"] = predictions.get("predicted_throughput", 0.0)
                snapshot["predicted_propagation_time"] = predictions.get("predicted_propagation_time", 0.0)
                snapshot["predicted_ram_usage"] = predictions.get("predicted_ram_usage", 0.0)
                snapshot["active_model"] = predictions.get("active_model", "Random Forest")
                snapshot["congestion_risk"] = predictions.get("congestion_risk", 0.0)
                snapshot["predicted_status"] = predictions.get("predicted_status", "NORMAL")

                # Insert NEW Row into SQLite
                row_id = db.insert_telemetry_snapshot(snapshot)
                self.alert_service.log_alerts(active_alerts)

                # Logging
                print(f"[COLLECTOR] New measurement at {ts} | traffic={traffic_val}MB delay={delay_val}ms throughput={throughput_val}Mbps prop={prop_val}ms ram={ram_val}% temp={temp_val}")
                print(f"[DATABASE] INSERTED telemetry row id={row_id}")

            except Exception as e:
                print(f"[Monitoring Service Loop Error]: {e}")
                import traceback
                traceback.print_exc()

            time.sleep(config.COLLECTION_INTERVAL_SECONDS)
