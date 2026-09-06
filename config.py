"""
Central Configuration Module for Intelligent Telecom Tower Monitoring System.
Contains thresholds, sampling parameters, paths, and offline system metadata.
"""
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Database Settings
DATABASE_PATH = os.path.join(BASE_DIR, "data", "telecom_monitoring.db")

# Sampling Interval (Seconds)
COLLECTION_INTERVAL_SECONDS = 2.0

# Network Configuration
DEFAULT_MAX_BANDWIDTH_MBPS = 100.0  # Configurable prototype capacity

# Anomaly Detection Thresholds
THRESHOLDS = {
    "temperature": {
        "warning": 60.0,   # °C
        "critical": 80.0   # °C
    },
    "battery_voltage": {
        "warning": 11.5,   # V
        "critical": 10.8   # V
    },
    "bandwidth_utilization": {
        "warning": 70.0,   # %
        "critical": 90.0   # %
    },
    "signal_strength": {
        "excellent": 80.0, # %
        "good": 60.0,      # %
        "fair": 40.0,      # %
        "weak": 20.0,      # %
        "critical": 10.0,  # %
        "disconnected": 0.0
    },
    "power_consumption": {
        "warning": 150.0,  # W
        "critical": 220.0  # W
    },
    "cpu_usage": {
        "warning": 80.0,   # %
        "critical": 95.0   # %
    },
    "ram_usage": {
        "warning": 85.0,   # %
        "critical": 95.0   # %
    },
    "traffic_spike_multiplier": 2.5
}

# Machine Learning Paths
ML_MODEL_PATH = os.path.join(BASE_DIR, "models", "rf_telecom_model.pkl")
SYNTHETIC_SAMPLES_COUNT = 1000

# Presentation Metadata
SYSTEM_METADATA = {
    "title": "INTELLIGENT TELECOM TOWER MONITORING AND ALERT SYSTEM",
    "description": "Laptop-Based Real-Time Network and System Monitoring Prototype with Simulated Telecom Tower Parameters",
    "completion": "Software Prototype (~75% Completion)",
    "realtime_parameters": [
        "Network Traffic (Bytes Sent/Recv)",
        "Upload & Download Speeds (KB/s & Mbps)",
        "Bandwidth Utilization (%)",
        "Wi-Fi Signal Strength (%) & SSID",
        "CPU Usage (%)",
        "RAM Usage (%)",
        "Battery % & Charging Status",
        "System Uptime & Network Interface Status"
    ],
    "simulated_parameters": [
        "Tower Power Consumption (W)",
        "Tower Battery Voltage (V)",
        "Connected Users Count",
        "Tower Load (%)"
    ],
    "future_hardware": [
        "ESP32 Microcontroller",
        "DHT22 Temperature Sensor",
        "INA219 Power/Current Sensor",
        "Voltage Divider Sensor Module"
    ]
}
