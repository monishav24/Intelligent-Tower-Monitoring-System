"""
Machine Learning Real-Time Predictor Module.
Loads pre-trained Random Forest model artifacts and performs inference on real-time metrics.
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pickle
import numpy as np
import pandas as pd
import config

class NetworkPredictor:
    def __init__(self):
        self.model_data = None
        self.ensure_model_exists()
        self.load_model()

    def ensure_model_exists(self):
        """Train model if pickle file does not exist yet."""
        if not os.path.exists(config.ML_MODEL_PATH):
            from ml.train_model import train_and_save_models
            train_and_save_models()

    def load_model(self):
        """Load pickled Random Forest model."""
        try:
            with open(config.ML_MODEL_PATH, "rb") as f:
                self.model_data = pickle.load(f)
        except Exception as e:
            print(f"[ML Predictor Error] Failed to load model: {e}")
            self.model_data = None

    def predict(self, reading):
        """
        Perform ML inference for future traffic, congestion risk, and predicted status.
        """
        if not self.model_data:
            self.ensure_model_exists()
            self.load_model()

        if not self.model_data:
            # Fallback estimation if model fails to load
            return {
                "predicted_traffic_mbps": round(reading.get("throughput_mbps", 0.0) * 1.15, 2),
                "congestion_risk": round(min(reading.get("bandwidth_utilization", 0.0) * 1.1, 100.0), 1),
                "predicted_status": "NORMAL",
                "confidence_score": 85.0
            }

        try:
            rf_traffic = self.model_data["rf_traffic"]
            rf_risk = self.model_data["rf_risk"]
            rf_status = self.model_data["rf_status"]
            features = self.model_data["features"]

            # Construct feature vector matching model training schema
            input_df = pd.DataFrame([{
                "connected_users": reading.get("connected_users", 40),
                "bandwidth_utilization": reading.get("bandwidth_utilization", 10.0),
                "upload_speed_kbps": reading.get("upload_speed_kbps", 50.0),
                "download_speed_kbps": reading.get("download_speed_kbps", 200.0),
                "throughput_mbps": reading.get("throughput_mbps", 1.5),
                "tower_load": reading.get("tower_load", 35.0),
                "temperature": reading.get("temperature", 35.0)
            }])[features]

            pred_traffic = float(rf_traffic.predict(input_df)[0])
            pred_risk = float(rf_risk.predict(input_df)[0])
            pred_status = str(rf_status.predict(input_df)[0])

            # Calculate prediction confidence score from classifier class probabilities
            status_probs = rf_status.predict_proba(input_df)[0]
            max_prob = float(np.max(status_probs))
            confidence_score = round(max_prob * 100.0, 1)

            # Cap bounds safely
            pred_traffic = round(max(pred_traffic, 0.1), 2)
            pred_risk = round(min(max(pred_risk, 0.0), 100.0), 1)

            return {
                "predicted_traffic_mbps": pred_traffic,
                "congestion_risk": pred_risk,
                "predicted_status": pred_status,
                "confidence_score": confidence_score
            }

        except Exception as e:
            print(f"[ML Predict Error]: {e}")
            return {
                "predicted_traffic_mbps": round(reading.get("throughput_mbps", 0.0) * 1.1, 2),
                "congestion_risk": round(reading.get("bandwidth_utilization", 0.0), 1),
                "predicted_status": "NORMAL",
                "confidence_score": 80.0
            }
