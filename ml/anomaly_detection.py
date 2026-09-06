"""
Rule-Based and Statistical Anomaly Detection Engine.
Evaluates physical hardware parameters, network bandwidth utilization, signal strength,
and traffic spikes to classify tower operational status and generate actionable alerts.
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from datetime import datetime
import config

class AnomalyDetector:
    def __init__(self):
        self.recent_throughputs = []
        self.max_history = 10

    def evaluate_reading(self, reading):
        """
        Evaluate full sensor reading against thresholds and detect anomalies.
        """
        alerts = []
        status_scores = [] # "NORMAL", "WARNING", "CRITICAL"

        temp = reading.get("temperature", 35.0)
        battery = reading.get("battery_voltage", 12.5)
        bw_util = reading.get("bandwidth_utilization", 10.0)
        signal = reading.get("signal_strength", 80.0)
        power = reading.get("power_consumption", 120.0)
        tower_load = reading.get("tower_load", 30.0)
        throughput = reading.get("throughput_mbps", 0.0)
        timestamp = reading.get("timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        th = config.THRESHOLDS

        # 1. TEMPERATURE ANOMALY CHECK
        if temp >= th["temperature"]["critical"]:
            alerts.append({
                "timestamp": timestamp,
                "severity": "CRITICAL",
                "parameter": "Temperature",
                "message": f"Critical Thermal Overheating Detected! ({temp}°C > {th['temperature']['critical']}°C)",
                "value": temp,
                "threshold": th["temperature"]["critical"]
            })
            status_scores.append("CRITICAL")
        elif temp >= th["temperature"]["warning"]:
            alerts.append({
                "timestamp": timestamp,
                "severity": "WARNING",
                "parameter": "Temperature",
                "message": f"High Temperature Warning ({temp}°C > {th['temperature']['warning']}°C)",
                "value": temp,
                "threshold": th["temperature"]["warning"]
            })
            status_scores.append("WARNING")

        # 2. BATTERY VOLTAGE ANOMALY CHECK
        if battery <= th["battery_voltage"]["critical"]:
            alerts.append({
                "timestamp": timestamp,
                "severity": "CRITICAL",
                "parameter": "Battery Voltage",
                "message": f"Critical Low Battery Voltage / Power Depletion! ({battery}V < {th['battery_voltage']['critical']}V)",
                "value": battery,
                "threshold": th["battery_voltage"]["critical"]
            })
            status_scores.append("CRITICAL")
        elif battery <= th["battery_voltage"]["warning"]:
            alerts.append({
                "timestamp": timestamp,
                "severity": "WARNING",
                "parameter": "Battery Voltage",
                "message": f"Battery Voltage Low Warning ({battery}V < {th['battery_voltage']['warning']}V)",
                "value": battery,
                "threshold": th["battery_voltage"]["warning"]
            })
            status_scores.append("WARNING")

        # 3. BANDWIDTH UTILIZATION ANOMALY CHECK
        if bw_util >= th["bandwidth_utilization"]["critical"]:
            alerts.append({
                "timestamp": timestamp,
                "severity": "CRITICAL",
                "parameter": "Bandwidth Utilization",
                "message": f"Network Congestion Saturation! ({bw_util}% >= {th['bandwidth_utilization']['critical']}%)",
                "value": bw_util,
                "threshold": th["bandwidth_utilization"]["critical"]
            })
            status_scores.append("CRITICAL")
        elif bw_util >= th["bandwidth_utilization"]["warning"]:
            alerts.append({
                "timestamp": timestamp,
                "severity": "WARNING",
                "parameter": "Bandwidth Utilization",
                "message": f"High Bandwidth Utilization Detected ({bw_util}% >= {th['bandwidth_utilization']['warning']}%)",
                "value": bw_util,
                "threshold": th["bandwidth_utilization"]["warning"]
            })
            status_scores.append("WARNING")

        # 4. SIGNAL STRENGTH ANOMALY CHECK
        if signal <= th["signal_strength"]["critical"]:
            alerts.append({
                "timestamp": timestamp,
                "severity": "CRITICAL",
                "parameter": "Wi-Fi Signal",
                "message": f"Critical Signal Degradation / Tower Disconnection ({signal}% <= {th['signal_strength']['critical']}%)",
                "value": signal,
                "threshold": th["signal_strength"]["critical"]
            })
            status_scores.append("CRITICAL")
        elif signal <= th["signal_strength"]["warning"]:
            alerts.append({
                "timestamp": timestamp,
                "severity": "WARNING",
                "parameter": "Wi-Fi Signal",
                "message": f"Weak Wi-Fi Signal Strength ({signal}% <= {th['signal_strength']['warning']}%)",
                "value": signal,
                "threshold": th["signal_strength"]["warning"]
            })
            status_scores.append("WARNING")

        # 5. POWER CONSUMPTION ANOMALY CHECK
        if power >= th["power_consumption"]["critical"]:
            alerts.append({
                "timestamp": timestamp,
                "severity": "CRITICAL",
                "parameter": "Power Consumption",
                "message": f"Abnormal Power Surge / Current Drain ({power}W >= {th['power_consumption']['critical']}W)",
                "value": power,
                "threshold": th["power_consumption"]["critical"]
            })
            status_scores.append("CRITICAL")
        elif power >= th["power_consumption"]["warning"]:
            alerts.append({
                "timestamp": timestamp,
                "severity": "WARNING",
                "parameter": "Power Consumption",
                "message": f"Elevated Power Draw ({power}W >= {th['power_consumption']['warning']}W)",
                "value": power,
                "threshold": th["power_consumption"]["warning"]
            })
            status_scores.append("WARNING")

        # 6. TRAFFIC SPIKE ANOMALY CHECK (Statistical)
        if len(self.recent_throughputs) >= 5:
            avg_throughput = sum(self.recent_throughputs) / len(self.recent_throughputs)
            if avg_throughput > 0.05 and throughput >= (avg_throughput * 2.5):
                alerts.append({
                    "timestamp": timestamp,
                    "severity": "WARNING",
                    "parameter": "Network Traffic Spike",
                    "message": f"Sudden Traffic Spike Detected! ({round(throughput, 2)} Mbps vs recent avg {round(avg_throughput, 2)} Mbps)",
                    "value": round(throughput, 2),
                    "threshold": round(avg_throughput * 2.5, 2)
                })
                status_scores.append("WARNING")

        # Maintain throughput rolling window
        self.recent_throughputs.append(throughput)
        if len(self.recent_throughputs) > self.max_history:
            self.recent_throughputs.pop(0)

        # Determine overall tower status
        if "CRITICAL" in status_scores:
            overall_status = "CRITICAL"
        elif "WARNING" in status_scores:
            overall_status = "WARNING"
        else:
            overall_status = "NORMAL"

        anomaly_status = "ANOMALY_DETECTED" if len(alerts) > 0 else "NORMAL"

        return overall_status, anomaly_status, alerts
