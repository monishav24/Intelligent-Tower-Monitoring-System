"""
Flask REST API Blueprint module exposing JSON telemetry endpoints for dashboard, ML, system health, and demo mode controls.
"""
import os
import sys
from flask import Blueprint, jsonify, request

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import database.database as db
import config

api_bp = Blueprint("api", __name__)

monitoring_service_instance = None

def init_api_service(service):
    """Bind global monitoring service reference."""
    global monitoring_service_instance
    monitoring_service_instance = service

@api_bp.route("/api/latest", methods=["GET"])
def get_latest():
    """Retrieve full latest telemetry snapshot."""
    snapshot = db.get_latest_snapshot()
    alerts = db.get_active_alerts(limit=5)
    if not snapshot:
        return jsonify({"status": "no_data", "message": "Telemetry collector warming up..."}), 200

    return jsonify({
        "status": "success",
        "data": snapshot,
        "recent_alerts": alerts,
        "system_metadata": config.SYSTEM_METADATA
    })

@api_bp.route("/api/history", methods=["GET"])
def get_history():
    """Retrieve time-series points for Chart.js rendering."""
    limit = request.args.get("limit", default=30, type=int)
    limit = min(max(limit, 5), 200)
    history = db.get_history(limit=limit)
    return jsonify({
        "status": "success",
        "count": len(history),
        "data": history
    })

@api_bp.route("/api/network", methods=["GET"])
def get_network_metrics():
    """Retrieve real-time laptop network parameters."""
    snapshot = db.get_latest_snapshot()
    if not snapshot:
        return jsonify({"status": "no_data"}), 200

    return jsonify({
        "status": "success",
        "bytes_sent": snapshot.get("bytes_sent"),
        "bytes_recv": snapshot.get("bytes_recv"),
        "upload_speed_kbps": snapshot.get("upload_speed"),
        "download_speed_kbps": snapshot.get("download_speed"),
        "total_network_traffic_mb": snapshot.get("total_network_traffic"),
        "bandwidth_utilization_pct": snapshot.get("bandwidth_utilization"),
        "signal_strength_pct": snapshot.get("signal_strength"),
        "wifi_status": snapshot.get("wifi_status"),
        "ssid": snapshot.get("ssid"),
        "internet_status": snapshot.get("internet_status", "ONLINE")
    })

@api_bp.route("/api/system-health", methods=["GET"])
def get_system_health():
    """Retrieve laptop host CPU, RAM, Battery, and Temperature parameters."""
    snapshot = db.get_latest_snapshot()
    if not snapshot:
        return jsonify({"status": "no_data"}), 200

    return jsonify({
        "status": "success",
        "cpu_usage_pct": snapshot.get("cpu_usage"),
        "ram_usage_pct": snapshot.get("ram_usage"),
        "battery_percentage": snapshot.get("battery_percentage"),
        "battery_status": snapshot.get("battery_status"),
        "system_temperature": snapshot.get("system_temperature"),
        "temperature_source": snapshot.get("temperature_source"),
        "node_label": "System Health"
    })

@api_bp.route("/api/tower", methods=["GET"])
def get_tower_metrics():
    """Retrieve physical telecom tower parameters."""
    snapshot = db.get_latest_snapshot()
    if not snapshot:
        return jsonify({"status": "no_data"}), 200

    return jsonify({
        "status": "success",
        "power_consumption_w": snapshot.get("power_consumption"),
        "battery_voltage_v": snapshot.get("battery_voltage"),
        "connected_client_count": snapshot.get("connected_client_count"),
        "tower_load_pct": snapshot.get("tower_load"),
        "data_source": snapshot.get("data_source", "Telecom Tower Sensors")
    })


@api_bp.route("/api/hotspot", methods=["GET"])
def get_hotspot_metrics():
    """Retrieve Mobile Hotspot status, connected client devices count, and client IP addresses."""
    snapshot = db.get_latest_snapshot()
    if not snapshot:
        return jsonify({"status": "no_data"}), 200

    return jsonify({
        "status": "success",
        "hotspot_status": snapshot.get("hotspot_status"),
        "interface_name": snapshot.get("hotspot_interface"),
        "connected_client_count": snapshot.get("connected_client_count"),
        "client_ip_list": snapshot.get("client_ip_list", []),
        "client_details_status": snapshot.get("hotspot_client_details_status")
    })

@api_bp.route("/api/prediction", methods=["GET"])
def get_prediction():
    """Retrieve Random Forest ML forecast and congestion risk."""
    snapshot = db.get_latest_snapshot()
    if not snapshot:
        return jsonify({"status": "no_data"}), 200

    return jsonify({
        "status": "success",
        "predicted_network_traffic_mbps": snapshot.get("predicted_network_traffic"),
        "congestion_risk_pct": snapshot.get("congestion_risk"),
        "predicted_status": snapshot.get("predicted_status"),
        "model_type": "Random Forest Regressor & Classifier"
    })

@api_bp.route("/api/alerts", methods=["GET"])
def get_alerts():
    """Retrieve active system alerts log."""
    limit = request.args.get("limit", default=20, type=int)
    alerts = db.get_active_alerts(limit=limit)
    return jsonify({
        "status": "success",
        "count": len(alerts),
        "alerts": alerts
    })

@api_bp.route("/api/status", methods=["GET"])
def get_system_status():
    """Retrieve overall architecture status, internet status, and completion metadata."""
    snapshot = db.get_latest_snapshot()
    overall = snapshot.get("overall_status") if snapshot else "NORMAL"
    internet = snapshot.get("internet_status") if snapshot else "ONLINE"
    hotspot = snapshot.get("hotspot_status") if snapshot else "INACTIVE"
    return jsonify({
        "status": "success",
        "overall_status": overall,
        "internet_status": internet,
        "local_monitoring_status": "ACTIVE",
        "hotspot_status": hotspot,
        "project_title": config.SYSTEM_METADATA["title"],
        "completion_status": config.SYSTEM_METADATA["completion"]
    })

@api_bp.route("/api/demo-mode", methods=["POST"])
def set_demo_mode():
    """
    Switch Demonstration Mode Scenario.
    Scenarios: NORMAL, HIGH_TRAFFIC, NETWORK_CONGESTION, WEAK_SIGNAL, HIGH_TEMPERATURE, POWER_ANOMALY, NETWORK_DISCONNECTED
    """
    req = request.get_json(silent=True) or {}
    scenario = req.get("scenario", "NORMAL").upper()

    valid_scenarios = [
        "NORMAL", "HIGH_TRAFFIC", "NETWORK_CONGESTION",
        "WEAK_SIGNAL", "HIGH_TEMPERATURE", "POWER_ANOMALY", "NETWORK_DISCONNECTED"
    ]

    if scenario not in valid_scenarios:
        return jsonify({"status": "error", "message": f"Invalid scenario. Supported: {valid_scenarios}"}), 400

    if monitoring_service_instance:
        monitoring_service_instance.set_demo_scenario(scenario)

    return jsonify({
        "status": "success",
        "active_scenario": scenario,
        "message": f"Demo mode switched to '{scenario}'"
    })

@api_bp.route("/api/demo-mode/reset", methods=["POST"])
def reset_demo_mode():
    """Reset Demo Mode and return to live monitoring."""
    if monitoring_service_instance:
        monitoring_service_instance.reset_demo_mode()

    return jsonify({
        "status": "success",
        "message": "Returned to LIVE monitoring mode."
    })

@api_bp.route("/api/esp32/telemetry", methods=["POST"])
def receive_esp32_telemetry():
    """
    Receive real hardware telemetry payload from ESP32 IoT node.
    Accepts JSON with temperature, humidity, voltage, current, power.
    Returns current system overall status and hardware control instructions (LEDs, Buzzer).
    """
    data = request.get_json(silent=True) or {}
    if not data:
        return jsonify({"status": "error", "message": "Missing JSON payload"}), 400

    if monitoring_service_instance and hasattr(monitoring_service_instance, "esp32_collector"):
        success = monitoring_service_instance.esp32_collector.update_telemetry(data)
        if not success:
            return jsonify({"status": "error", "message": "Invalid telemetry payload format"}), 400

    snapshot = db.get_latest_snapshot()
    overall = snapshot.get("overall_status", "NORMAL") if snapshot else "NORMAL"

    # Actuator control flags for ESP32 hardware
    green_led = (overall == "NORMAL")
    red_led = (overall in ("WARNING", "CRITICAL", "DISCONNECTED"))
    buzzer = (overall in ("CRITICAL", "DISCONNECTED"))

    return jsonify({
        "status": "success",
        "message": "ESP32 telemetry processed successfully",
        "overall_status": overall,
        "control": {
            "green_led": green_led,
            "red_led": red_led,
            "buzzer": buzzer
        }
    })

@api_bp.route("/api/esp32/status", methods=["GET"])
def get_esp32_status():
    """Retrieve ESP32 IoT hardware node connectivity and latest sensor metrics."""
    if monitoring_service_instance and hasattr(monitoring_service_instance, "esp32_collector"):
        telemetry = monitoring_service_instance.esp32_collector.get_telemetry()
        return jsonify({
            "status": "success",
            "esp32_online": telemetry["is_online"],
            "data": telemetry
        })
    return jsonify({"status": "error", "message": "Monitoring service not initialized"}), 500
