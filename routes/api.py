"""
Flask REST API Routes for Intelligent Telecom Tower Monitoring System.
Exposes JSON endpoints for real-time telemetry, historical chart data, ML predictions, alerts, and demo mode.
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from flask import Blueprint, jsonify, request
import database.database as db
import config

api_bp = Blueprint("api", __name__)

# Global runtime state for demo mode and bandwidth setting
current_demo_scenario = "NORMAL"

@api_bp.route("/api/latest", methods=["GET"])
def get_latest():
    """Retrieve the latest real-time reading, ML prediction, and active status."""
    latest = db.get_latest_reading()
    alerts = db.get_recent_alerts(limit=5)
    
    if not latest:
        return jsonify({"status": "no_data", "message": "Collector warming up..."}), 200

    return jsonify({
        "status": "success",
        "data": latest,
        "recent_alerts": alerts,
        "demo_scenario": current_demo_scenario,
        "system_info": config.SYSTEM_METADATA
    })

@api_bp.route("/api/history", methods=["GET"])
def get_history():
    """Retrieve historical time-series data points for live Chart.js rendering."""
    limit = request.args.get("limit", default=30, type=int)
    limit = min(max(limit, 5), 200)
    history = db.get_history(limit=limit)
    return jsonify({
        "status": "success",
        "count": len(history),
        "data": history
    })

@api_bp.route("/api/prediction", methods=["GET"])
def get_prediction():
    """Retrieve ML traffic forecast, congestion risk, and confidence metrics."""
    latest = db.get_latest_reading()
    if not latest:
        return jsonify({"status": "no_data"}), 200

    return jsonify({
        "status": "success",
        "predicted_traffic_mbps": latest.get("predicted_traffic", 0.0),
        "congestion_risk_pct": latest.get("congestion_risk", 0.0),
        "predicted_status": latest.get("predicted_status", "NORMAL"),
        "current_throughput_mbps": latest.get("upload_speed", 0.0) + latest.get("download_speed", 0.0),
        "timestamp": latest.get("timestamp")
    })

@api_bp.route("/api/alerts", methods=["GET"])
def get_alerts():
    """Retrieve recent alerts log."""
    limit = request.args.get("limit", default=20, type=int)
    alerts = db.get_recent_alerts(limit=limit)
    return jsonify({
        "status": "success",
        "count": len(alerts),
        "alerts": alerts
    })

@api_bp.route("/api/demo-mode", methods=["POST"])
def set_demo_mode():
    """
    Switch demonstration scenario.
    Supported scenarios: NORMAL, HIGH_TRAFFIC, NETWORK_CONGESTION, WEAK_SIGNAL, HIGH_TEMPERATURE, POWER_FAILURE
    """
    global current_demo_scenario
    req_data = request.get_json(silent=True) or {}
    scenario = req_data.get("scenario", "NORMAL").upper()
    
    valid_scenarios = [
        "NORMAL", "HIGH_TRAFFIC", "NETWORK_CONGESTION",
        "WEAK_SIGNAL", "HIGH_TEMPERATURE", "POWER_FAILURE"
    ]

    if scenario not in valid_scenarios:
        return jsonify({"status": "error", "message": f"Invalid scenario. Choose from {valid_scenarios}"}), 400

    current_demo_scenario = scenario
    
    # Import app background collector if needed to update scenario immediately
    from app import update_demo_scenario
    update_demo_scenario(scenario)

    return jsonify({
        "status": "success",
        "active_scenario": current_demo_scenario,
        "message": f"Demonstration mode switched to '{current_demo_scenario}'"
    })

@api_bp.route("/api/config/bandwidth", methods=["POST"])
def set_bandwidth():
    """Update maximum bandwidth threshold in Mbps."""
    req_data = request.get_json(silent=True) or {}
    mbps = req_data.get("max_bandwidth_mbps")
    if not mbps or float(mbps) <= 0:
        return jsonify({"status": "error", "message": "Provide valid positive max_bandwidth_mbps"}), 400

    from app import set_max_bandwidth
    set_max_bandwidth(float(mbps))

    return jsonify({
        "status": "success",
        "max_bandwidth_mbps": float(mbps),
        "message": f"Maximum bandwidth updated to {mbps} Mbps"
    })

@api_bp.route("/api/status", methods=["GET"])
def get_system_status():
    """Return overall architecture status and project completion breakdown."""
    return jsonify({
        "project_title": config.SYSTEM_METADATA["title"],
        "completion": config.SYSTEM_METADATA["completion_status"],
        "realtime_parameters": [
            "Network Traffic (Bytes Sent/Recv)",
            "Upload Speed (KB/s & Mbps)",
            "Download Speed (KB/s & Mbps)",
            "Bandwidth Utilization (%)",
            "Wi-Fi Signal Strength (%)"
        ],
        "simulated_parameters": [
            "Tower Temperature (°C)",
            "Battery Voltage (V)",
            "Power Consumption (W)",
            "Connected Users (Count)",
            "Tower Load (%)"
        ],
        "hardware_roadmap": config.SYSTEM_METADATA["future_hardware"]
    })
