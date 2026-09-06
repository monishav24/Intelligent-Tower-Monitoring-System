"""
Anomaly Detection & Intelligent Status Evaluation Engine.
Evaluates multi-parameter thresholds, statistical traffic spikes, and network disconnect/reconnect events.
Enforces intelligent overall status priority: DISCONNECTED > CRITICAL > WARNING > NORMAL.
"""
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

class AnomalyDetector:
    def __init__(self):
        self.recent_throughputs = []
        self.max_history = 10
        self.was_disconnected = False

    def evaluate(self, reading):
        """
        Evaluate full sensor reading against thresholds.
        Returns overall_status, anomaly_status, and active_alerts list.
        """
        alerts = []
        status_ranks = [] # DISCONNECTED, CRITICAL, WARNING, NORMAL

        ts = reading.get("timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        th = config.THRESHOLDS

        wifi_status = reading.get("wifi_status", "CONNECTED").upper()
        signal = reading.get("signal_strength", 80.0)
        bw_util = reading.get("bandwidth_utilization", 10.0)
        temp = reading.get("system_temperature")
        battery_v = reading.get("battery_voltage", 12.5)
        power_w = reading.get("power_consumption", 120.0)
        throughput = reading.get("throughput_mbps", 0.0)

        # 1. DISCONNECTION & AUTO-RECOVERY CHECK
        if wifi_status == "DISCONNECTED" or signal == 0.0:
            status_ranks.append("DISCONNECTED")
            if not self.was_disconnected:
                alerts.append({
                    "timestamp": ts,
                    "severity": "CRITICAL",
                    "parameter": "Network Connection",
                    "message": "CRITICAL: Network Connection Lost",
                    "status": "ACTIVE"
                })
                self.was_disconnected = True
        else:
            if self.was_disconnected:
                alerts.append({
                    "timestamp": ts,
                    "severity": "INFO",
                    "parameter": "Network Connection",
                    "message": "INFO: Network Connection Restored",
                    "status": "ACTIVE"
                })
                self.was_disconnected = False

        # 2. BANDWIDTH UTILIZATION CHECK
        if bw_util >= th["bandwidth_utilization"]["critical"]:
            alerts.append({
                "timestamp": ts,
                "severity": "CRITICAL",
                "parameter": "Bandwidth Utilization",
                "message": f"Critical Bandwidth Saturation! ({bw_util}% >= {th['bandwidth_utilization']['critical']}%)",
                "status": "ACTIVE"
            })
            status_ranks.append("CRITICAL")
        elif bw_util >= th["bandwidth_utilization"]["warning"]:
            alerts.append({
                "timestamp": ts,
                "severity": "WARNING",
                "parameter": "Bandwidth Utilization",
                "message": f"High Bandwidth Utilization Warning ({bw_util}% >= {th['bandwidth_utilization']['warning']}%)",
                "status": "ACTIVE"
            })
            status_ranks.append("WARNING")

        # 3. SIGNAL STRENGTH CHECK (If connected)
        if wifi_status != "DISCONNECTED" and signal > 0:
            if signal <= th["signal_strength"]["critical"]:
                alerts.append({
                    "timestamp": ts,
                    "severity": "CRITICAL",
                    "parameter": "Wi-Fi Signal",
                    "message": f"Critical Signal Loss Detected! ({signal}% <= {th['signal_strength']['critical']}%)",
                    "status": "ACTIVE"
                })
                status_ranks.append("CRITICAL")
            elif signal <= th["signal_strength"]["weak"]:
                alerts.append({
                    "timestamp": ts,
                    "severity": "WARNING",
                    "parameter": "Wi-Fi Signal",
                    "message": f"Weak Wi-Fi Signal Strength Warning ({signal}% <= {th['signal_strength']['weak']}%)",
                    "status": "ACTIVE"
                })
                status_ranks.append("WARNING")

        # 4. TEMPERATURE CHECK (If available)
        if temp is not None:
            if temp >= th["temperature"]["critical"]:
                alerts.append({
                    "timestamp": ts,
                    "severity": "CRITICAL",
                    "parameter": "Temperature",
                    "message": f"Critical Overheating Alert! ({temp}°C >= {th['temperature']['critical']}°C)",
                    "status": "ACTIVE"
                })
                status_ranks.append("CRITICAL")
            elif temp >= th["temperature"]["warning"]:
                alerts.append({
                    "timestamp": ts,
                    "severity": "WARNING",
                    "parameter": "Temperature",
                    "message": f"High System Temperature Warning ({temp}°C >= {th['temperature']['warning']}°C)",
                    "status": "ACTIVE"
                })
                status_ranks.append("WARNING")

        # 5. SIMULATED BATTERY VOLTAGE CHECK
        if battery_v <= th["battery_voltage"]["critical"]:
            alerts.append({
                "timestamp": ts,
                "severity": "CRITICAL",
                "parameter": "Battery Voltage",
                "message": f"Critical Power Failure / Low Battery Voltage! ({battery_v}V <= {th['battery_voltage']['critical']}V)",
                "status": "ACTIVE"
            })
            status_ranks.append("CRITICAL")
        elif battery_v <= th["battery_voltage"]["warning"]:
            alerts.append({
                "timestamp": ts,
                "severity": "WARNING",
                "parameter": "Battery Voltage",
                "message": f"Battery Voltage Low Warning ({battery_v}V <= {th['battery_voltage']['warning']}V)",
                "status": "ACTIVE"
            })
            status_ranks.append("WARNING")

        # 6. SIMULATED POWER CONSUMPTION CHECK
        if power_w >= th["power_consumption"]["critical"]:
            alerts.append({
                "timestamp": ts,
                "severity": "CRITICAL",
                "parameter": "Power Consumption",
                "message": f"Abnormal Power Surge Alert! ({power_w}W >= {th['power_consumption']['critical']}W)",
                "status": "ACTIVE"
            })
            status_ranks.append("CRITICAL")
        elif power_w >= th["power_consumption"]["warning"]:
            alerts.append({
                "timestamp": ts,
                "severity": "WARNING",
                "parameter": "Power Consumption",
                "message": f"Elevated Power Draw Warning ({power_w}W >= {th['power_consumption']['warning']}W)",
                "status": "ACTIVE"
            })
            status_ranks.append("WARNING")

        # 7. TRAFFIC SPIKE ANOMALY CHECK
        if len(self.recent_throughputs) >= 5:
            avg_throughput = sum(self.recent_throughputs) / len(self.recent_throughputs)
            spike_threshold = avg_throughput * th["traffic_spike_multiplier"]
            if avg_throughput > 0.05 and throughput >= spike_threshold:
                alerts.append({
                    "timestamp": ts,
                    "severity": "WARNING",
                    "parameter": "Network Traffic Spike",
                    "message": f"WARNING: Abnormal Network Traffic Spike Detected ({round(throughput, 2)} Mbps vs avg {round(avg_throughput, 2)} Mbps)",
                    "status": "ACTIVE"
                })
                status_ranks.append("WARNING")

        self.recent_throughputs.append(throughput)
        if len(self.recent_throughputs) > self.max_history:
            self.recent_throughputs.pop(0)

        # Enforce Overall Status Priority: DISCONNECTED > CRITICAL > WARNING > NORMAL
        if "DISCONNECTED" in status_ranks:
            overall_status = "DISCONNECTED"
        elif "CRITICAL" in status_ranks:
            overall_status = "CRITICAL"
        elif "WARNING" in status_ranks:
            overall_status = "WARNING"
        else:
            overall_status = "NORMAL"

        anomaly_status = "ANOMALY_DETECTED" if len(alerts) > 0 else "NORMAL"

        return overall_status, anomaly_status, alerts
