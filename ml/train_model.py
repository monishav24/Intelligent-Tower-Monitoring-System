"""
Random Forest Model Trainer.
Trains Random Forest Regressors for Traffic & Risk forecasting, and Random Forest Classifier for Status prediction.
Saves model payload artifact to disk.
"""
import os
import sys
import pickle
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from ml.generate_training_data import generate_synthetic_data

def train_and_save():
    """Train Random Forest model payload and persist pickle file."""
    print("[ML] Generating synthetic dataset...")
    df = generate_synthetic_data(config.SYNTHETIC_SAMPLES_COUNT)

    features = [
        "connected_users",
        "bandwidth_utilization",
        "upload_speed",
        "download_speed",
        "throughput_mbps",
        "signal_strength",
        "tower_load",
        "temperature"
    ]

    X = df[features]
    y_traffic = df["future_network_traffic"]
    y_risk = df["congestion_risk"]
    y_status = df["predicted_status"]

    print("[ML] Training Random Forest Regressor (Traffic)...")
    rf_traffic = RandomForestRegressor(n_estimators=50, random_state=42)
    rf_traffic.fit(X, y_traffic)

    print("[ML] Training Random Forest Regressor (Congestion Risk)...")
    rf_risk = RandomForestRegressor(n_estimators=50, random_state=42)
    rf_risk.fit(X, y_risk)

    print("[ML] Training Random Forest Classifier (Status)...")
    rf_status = RandomForestClassifier(n_estimators=50, random_state=42)
    rf_status.fit(X, y_status)

    payload = {
        "features": features,
        "rf_traffic": rf_traffic,
        "rf_risk": rf_risk,
        "rf_status": rf_status
    }

    os.makedirs(os.path.dirname(config.ML_MODEL_PATH), exist_ok=True)
    with open(config.ML_MODEL_PATH, "wb") as f:
        pickle.dump(payload, f)

    print(f"[ML] Model artifacts successfully saved to '{config.ML_MODEL_PATH}'.")

if __name__ == "__main__":
    train_and_save()
