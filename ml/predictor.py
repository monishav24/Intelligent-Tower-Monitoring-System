"""
Live Multi-Target Predictor Module.
Loads trained active model from disk registry (multi_model_registry.pkl)
and generates real-time predictions for all 5 ML parameters:
1. Traffic
2. Delay
3. Throughput
4. Propagation Time
5. RAM Usage
"""
import os
import sys
import pickle
import pandas as pd
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from ml.algorithm_comparison import MODEL_REGISTRY_PATH, FEATURE_COLUMNS, TARGET_COLUMNS

class NetworkPredictor:
    def __init__(self):
        self.selected_model = None
        self.selected_model_name = "Random Forest"
        self.feature_columns = FEATURE_COLUMNS
        self.load_selected_model()

    def load_selected_model(self):
        """Load trained fixed selected model from disk registry if available."""
        if os.path.exists(MODEL_REGISTRY_PATH):
            try:
                with open(MODEL_REGISTRY_PATH, "rb") as f:
                    registry = pickle.load(f)
                selected_name = registry.get("selected_model_name") or registry.get("best_algorithm") or registry.get("active_model_name", "Random Forest")
                models_dict = registry.get("models", {})
                if selected_name in models_dict:
                    self.selected_model = models_dict[selected_name]
                    self.selected_model_name = selected_name
                    self.feature_columns = registry.get("feature_columns", FEATURE_COLUMNS)
                    return True
            except Exception as e:
                print(f"[NetworkPredictor Load Warning]: {e}")
        return False

    def load_active_model(self):
        """Backward compatibility alias for load_selected_model."""
        return self.load_selected_model()

    def predict(self, snapshot):
        """
        Predict 5 parameters from current telemetry snapshot using the fixed selected model.
        Returns dictionary containing predicted_traffic, predicted_delay, predicted_throughput,
        predicted_propagation_time, predicted_ram_usage, selected_model, best_algorithm, congestion_risk, predicted_status.
        """
        # Load fixed selected model if available
        self.load_selected_model()

        # Prepare feature vector matching training feature columns
        timestamp_str = snapshot.get("timestamp", "")
        hour = 12
        minute = 0
        day_of_week = 0
        if timestamp_str and ":" in str(timestamp_str):
            try:
                dt = pd.to_datetime(timestamp_str)
                hour = int(dt.hour)
                minute = int(dt.minute)
                day_of_week = int(dt.dayofweek)
            except Exception:
                pass

        row_dict = {
            "traffic": float(snapshot.get("traffic", snapshot.get("total_network_traffic", 0.0)) or 0.0),
            "delay": float(snapshot.get("delay", snapshot.get("delay_ms", 1.0)) or 1.0),
            "throughput": float(snapshot.get("throughput", snapshot.get("throughput_mbps", 0.0)) or 0.0),
            "propagation_time": float(snapshot.get("propagation_time", snapshot.get("propagation_time_ms", 0.5)) or 0.5),
            "ram_usage": float(snapshot.get("ram_usage", snapshot.get("cpu_usage", 50.0)) or 50.0),
            "temperature": float(snapshot.get("temperature", snapshot.get("system_temperature", 28.4)) or 28.4),
            "hour": hour,
            "minute": minute,
            "day_of_week": day_of_week
        }

        X_df = pd.DataFrame([row_dict])[self.feature_columns]

        if self.selected_model is not None:
            try:
                preds = self.selected_model.predict(X_df)[0]
                pred_traffic = round(max(float(preds[0]), 0.0), 2)
                pred_delay = round(max(float(preds[1]), 0.1), 2)
                pred_throughput = round(max(float(preds[2]), 0.0), 2)
                pred_prop = round(max(float(preds[3]), 0.05), 2)
                pred_ram = round(min(max(float(preds[4]), 0.0), 100.0), 1)
            except Exception as e:
                print(f"[NetworkPredictor Inference Error]: {e}")
                pred_traffic = round(row_dict["traffic"] * 1.05, 2)
                pred_delay = round(row_dict["delay"] * 1.02, 2)
                pred_throughput = round(row_dict["throughput"] * 1.01, 2)
                pred_prop = round(pred_delay / 2.0, 2)
                pred_ram = round(min(row_dict["ram_usage"] * 1.02, 100.0), 1)
        else:
            # Fallback estimates if no model trained yet
            pred_traffic = round(row_dict["traffic"] * 1.05, 2)
            pred_delay = round(row_dict["delay"] * 1.02, 2)
            pred_throughput = round(row_dict["throughput"] * 1.01, 2)
            pred_prop = round(pred_delay / 2.0, 2)
            pred_ram = round(min(row_dict["ram_usage"] * 1.02, 100.0), 1)

        # Calculate congestion risk & status
        congestion_risk = round(min(max((pred_ram * 0.4 + (pred_delay / 100.0) * 30.0), 0.0), 100.0), 1)
        if congestion_risk >= 80.0 or pred_ram >= 90.0:
            predicted_status = "CRITICAL"
        elif congestion_risk >= 50.0 or pred_ram >= 80.0:
            predicted_status = "WARNING"
        else:
            predicted_status = "NORMAL"

        return {
            "predicted_traffic": pred_traffic,
            "predicted_network_traffic": pred_traffic,
            "predicted_delay": pred_delay,
            "predicted_throughput": pred_throughput,
            "predicted_propagation_time": pred_prop,
            "predicted_ram_usage": pred_ram,
            "selected_model": self.selected_model_name,
            "best_algorithm": self.selected_model_name,
            "active_model": self.selected_model_name,  # Backward compatibility
            "congestion_risk": congestion_risk,
            "predicted_status": predicted_status
        }
