"""
Configuration module for Intelligent Telecom Tower Monitoring and Alert System.
Defines dynamic thresholds, polling intervals, hardware configuration, and demo modes.
"""
import os

# Base Directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Database Configuration
DATABASE_PATH = os.path.join(BASE_DIR, "data", "tower_monitoring.db")

# Collection Interval (in seconds)
COLLECTION_INTERVAL_SECONDS = 2.0

# Network Bandwidth Configuration (Default Max Bandwidth in Mbps)
DEFAULT_MAX_BANDWIDTH_MBPS = 100.0  # 100 Mbps standard reference

# Anomaly Thresholds
THRESHOLDS = {
    "temperature": {
        "warning": 40.0,   # °C
        "critical": 50.0   # °C
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
        "warning": 40.0,   # %
        "critical": 20.0   # %
    },
    "power_consumption": {
        "warning": 150.0,  # W
        "critical": 220.0  # W
    },
    "tower_load": {
        "warning": 75.0,   # %
        "critical": 90.0   # %
    }
}

# Machine Learning Configuration
ML_MODEL_PATH = os.path.join(BASE_DIR, "ml", "models", "rf_predictor.pkl")
SYNTHETIC_DATA_SAMPLES = 1000

# Presentation Metadata
SYSTEM_METADATA = {
    "title": "INTELLIGENT TELECOM TOWER MONITORING AND ALERT SYSTEM",
    "completion_status": "Software Prototype (75% Completion)",
    "realtime_source": "Laptop Network Data (psutil & netsh)",
    "simulated_source": "ESP32 Sensor Simulation (Temperature, Power, Voltage, Tower Load)",
    "future_hardware": ["ESP32 Microcontroller", "DHT22 Temperature Sensor", "INA219 Current/Power Sensor", "Voltage Divider Sensor"]
}
