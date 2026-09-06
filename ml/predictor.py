"""
Real-Time Random Forest Predictor Module.
Infers future network traffic, congestion risk percentage, and predicted status.
Prioritizes DISCONNECTED status whenever network connectivity is lost.
"""
import os
import sys
import pickle
import pandas as pd
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

class NetworkPredictor:
    def __init__(self):
        self.model_payload = None
        self._ensure_and_load_model()

    def _ensure_and_load_model(self):
        """Auto-train model if pickle file is missing, then load into memory."""
        if not os.path.exists(config.ML_MODEL_PATH):
            from ml.train_model import train_and_save
            train_and_save()

        try:
            with open(config.ML_MODEL_PATH, "rb") as f:
                self.model_payload = pickle.load(f)
        except Exception as e:
            print(f"[ML Predictor Load Error]: {e}")
            self.model_payload = None

    def predict(self, reading):
        """
        Perform real-time prediction.
        Overrides predicted status to 'DISCONNECTED' if wifi_status is DISCONNECTED.
        """
        wifi_status = reading.get("wifi_status", "CONNECTED").upper()
        
        # Priority rule: If network disconnected, enforce DISCONNECTED status immediately
        if wifi_status == "DISCONNECTED" or reading.get("signal_strength", 100.0) == 0.0:
            return {
                "predicted_network_traffic": 0.0,
                "congestion_risk": 0.0,
                "predicted_status": "DISCONNECTED",
                "confidence_score": 100.0
            }

        if not self.model_payload:
            self._ensure_and_load_model()

        if not self.model_payload:
            return {
                "predicted_network_traffic": round(reading.get("throughput_mbps", 0.0) * 1.15, 2),
                "congestion_risk": round(reading.get("bandwidth_utilization", 0.0), 1),
                "predicted_status": "NORMAL",
                "confidence_score": 85.0
            }

        try:
            features = self.model_payload["features"]
            rf_traffic = self.model_payload["rf_traffic"]
            rf_risk = self.model_payload["rf_risk"]
            rf_status = self.model_payload["rf_status"]

            # Use temperature if available; fallback to 40°C if sensor unexposed
            temp_val = reading.get("system_temperature")
            if temp_val is None:
                temp_val = 40.0

            input_df = pd.DataFrame([{
                "connected_users": reading.get("connected_users", 40),
                "bandwidth_utilization": reading.get("bandwidth_utilization", 10.0),
                "upload_speed": reading.get("upload_speed", 50.0),
                "download_speed": reading.get("download_speed", 200.0),
                "throughput_mbps": reading.get("throughput_mbps", 1.5),
                "signal_strength": reading.get("signal_strength", 80.0),
                "tower_load": reading.get("tower_load", 35.0),
                "temperature": temp_val
            }])[features]

            pred_traffic = float(rf_traffic.predict(input_df)[0])
            pred_risk = float(rf_risk.predict(input_df)[0])
            pred_status = str(rf_status.predict(input_df)[0])

            status_probs = rf_status.predict_proba(input_df)[0]
            confidence_score = round(float(np.max(status_probs)) * 100.0, 1)

            return {
                "predicted_network_traffic": round(max(pred_traffic, 0.0), 2),
                "congestion_risk": round(min(max(pred_risk, 0.0), 100.0), 1),
                "predicted_status": pred_status,
                "confidence_score": confidence_score
            }

        except Exception as e:
            print(f"[ML Prediction Error]: {e}")
            return {
                "predicted_network_traffic": round(reading.get("throughput_mbps", 0.0), 2),
                "congestion_risk": round(reading.get("bandwidth_utilization", 0.0), 1),
                "predicted_status": "NORMAL",
                "confidence_score": 80.0
            }
