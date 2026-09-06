"""
Machine Learning Training Module.
Generates synthetic historical training data reflecting realistic diurnal telecom tower patterns.
Trains Random Forest models for Traffic Forecasting & Congestion Risk Classification.
Saves model artifacts for real-time inference.
"""
import os
import pickle
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
import config

def generate_synthetic_dataset(n_samples=1000):
    """
    Generate realistic synthetic training data for Random Forest model.
    """
    np.random.seed(42)

    # Time feature simulation (0 - 24 hours)
    hours = np.random.uniform(0, 24, n_samples)
    
    # Diurnal multiplier (peak traffic at 14:00 - 22:00)
    diurnal = np.sin((hours - 6) * np.pi / 12)
    diurnal = np.clip(diurnal, -0.5, 1.0)

    connected_users = np.clip(50 + diurnal * 120 + np.random.normal(0, 15, n_samples), 10, 350)
    bandwidth_utilization = np.clip(15 + diurnal * 45 + (connected_users / 350.0) * 30 + np.random.normal(0, 5, n_samples), 5, 98)
    upload_speed_kbps = bandwidth_utilization * 15.0 + np.random.normal(0, 50, n_samples)
    download_speed_kbps = bandwidth_utilization * 80.0 + np.random.normal(0, 200, n_samples)
    throughput_mbps = (upload_speed_kbps + download_speed_kbps) * 8.0 / 1024.0 / 1024.0
    
    tower_load = np.clip(20 + (connected_users / 350.0) * 50 + bandwidth_utilization * 0.3 + np.random.normal(0, 3, n_samples), 10, 99)
    temperature = np.clip(30 + tower_load * 0.2 + np.random.normal(0, 2, n_samples), 25, 60)

    # Future network traffic (target regression variable - next 10 mins throughput in Mbps)
    future_traffic = throughput_mbps * (1.0 + np.random.uniform(-0.1, 0.35, n_samples)) + (connected_users / 350.0) * 2.0

    # Congestion Risk (%) target (0 to 100)
    congestion_risk = np.clip((bandwidth_utilization * 0.6) + (tower_load * 0.4) + np.random.normal(0, 3, n_samples), 0, 100)

    # Target Classification Status: 0 = NORMAL, 1 = WARNING, 2 = CRITICAL
    target_status = []
    for risk, temp, util in zip(congestion_risk, temperature, bandwidth_utilization):
        if risk > 80 or temp > 50.0 or util > 90.0:
            target_status.append("CRITICAL")
        elif risk > 60 or temp > 40.0 or util > 70.0:
            target_status.append("WARNING")
        else:
            target_status.append("NORMAL")

    df = pd.DataFrame({
        "connected_users": connected_users,
        "bandwidth_utilization": bandwidth_utilization,
        "upload_speed_kbps": upload_speed_kbps,
        "download_speed_kbps": download_speed_kbps,
        "throughput_mbps": throughput_mbps,
        "tower_load": tower_load,
        "temperature": temperature,
        "future_traffic": future_traffic,
        "congestion_risk": congestion_risk,
        "target_status": target_status
    })

    return df

def train_and_save_models():
    """Train Random Forest Regressor & Classifier models and store artifact."""
    print("[ML] Generating synthetic training dataset...")
    df = generate_synthetic_dataset(config.SYNTHETIC_DATA_SAMPLES)

    features = [
        "connected_users",
        "bandwidth_utilization",
        "upload_speed_kbps",
        "download_speed_kbps",
        "throughput_mbps",
        "tower_load",
        "temperature"
    ]

    X = df[features]
    y_traffic = df["future_traffic"]
    y_risk = df["congestion_risk"]
    y_status = df["target_status"]

    print("[ML] Training Random Forest Regressor for Future Traffic...")
    rf_traffic = RandomForestRegressor(n_estimators=50, random_state=42)
    rf_traffic.fit(X, y_traffic)

    print("[ML] Training Random Forest Regressor for Congestion Risk...")
    rf_risk = RandomForestRegressor(n_estimators=50, random_state=42)
    rf_risk.fit(X, y_risk)

    print("[ML] Training Random Forest Classifier for Status Prediction...")
    rf_status = RandomForestClassifier(n_estimators=50, random_state=42)
    rf_status.fit(X, y_status)

    model_payload = {
        "features": features,
        "rf_traffic": rf_traffic,
        "rf_risk": rf_risk,
        "rf_status": rf_status
    }

    os.makedirs(os.path.dirname(config.ML_MODEL_PATH), exist_ok=True)
    with open(config.ML_MODEL_PATH, "wb") as f:
        pickle.dump(model_payload, f)

    print(f"[ML] Successfully trained and saved model artifacts to '{config.ML_MODEL_PATH}'.")

if __name__ == "__main__":
    train_and_save_models()
