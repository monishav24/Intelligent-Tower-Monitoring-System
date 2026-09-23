"""
Live 3-Algorithm Machine Learning Comparison Engine with Naive Baseline.
Compares Random Forest, Gradient Boosting, and XGBoost Regressors alongside a Naive Persistence Baseline
on live historical telemetry stored in SQLite.

KEY ENHANCEMENTS:
- Removed system_temperature from ML features (fake constant fallback removed as per prompt).
- Calculates next-interval predictions for the current latest snapshot across all 3 models.
- Generates dynamic reason text explaining why the winning model was selected.
- Strict temporal split before target shifting with 1-record boundary gap.
- Strict numeric type validation before model training.
"""
import os
import sys
import time
from datetime import datetime
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import xgboost as xgb

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import database.database as db

MINIMUM_VALID_RECORDS = 100
DEFAULT_WINDOW_SIZE = 200

# VALIDATED REAL TELEMETRY FEATURES (Removed fake temperature fallback)
FEATURE_COLUMNS = [
    "bandwidth_utilization",
    "upload_speed",
    "download_speed",
    "traffic_delta",
    "signal_strength",
    "cpu_usage",
    "ram_usage",
    "power_consumption",
    "battery_voltage",
    "connected_client_count",
    "tower_load"
]

class AlgorithmComparisonEngine:
    """
    Evaluates Random Forest, Gradient Boosting, XGBoost, and Naive Persistence Baseline on live telemetry history.
    """

    @staticmethod
    def evaluate_live_data(min_records=MINIMUM_VALID_RECORDS, window_size=DEFAULT_WINDOW_SIZE):
        """
        Fetch latest stored telemetry readings, sanitize types, perform temporal split,
        train 3 regressors, evaluate naive persistence baseline, calculate single-step prediction for latest reading,
        and rank models with dynamic win rationale.
        """
        # 1. Fetch raw historical telemetry from SQLite
        raw_history = db.get_history(limit=window_size)
        available_count = len(raw_history)

        # Minimum data requirement check
        if available_count < min_records:
            return {
                "status": "insufficient_data",
                "message": f"Insufficient data for model comparison ({available_count} valid records available; minimum {min_records} required).",
                "min_records_required": min_records,
                "available_records": available_count,
                "data_source_info": "Uses telemetry generated/stored by existing monitoring pipeline. No synthetic comparison data introduced.",
                "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

        try:
            # 2. Construct chronological DataFrame
            df = pd.DataFrame(raw_history)

            # Ensure total_network_traffic is present
            if "total_network_traffic" not in df.columns:
                df["total_network_traffic"] = 0.0

            # Feature Engineering: Compute interval traffic delta instead of raw cumulative traffic
            df["traffic_delta"] = df["total_network_traffic"].diff().fillna(0.0)

            # 3. EXPLICIT NUMERIC SANITIZATION FOR EVERY FEATURE COLUMN
            for col in FEATURE_COLUMNS:
                if col not in df.columns:
                    df[col] = 0.0
                df[col] = pd.to_numeric(df[col], errors="coerce")

            # Replace infinite values with NaN
            df.replace([np.inf, -np.inf], np.nan, inplace=True)

            # Drop rows with NaN in required feature columns or target
            df = df.dropna(subset=FEATURE_COLUMNS + ["bandwidth_utilization"]).reset_index(drop=True)

            n_total = len(df)
            if n_total < min_records:
                return {
                    "status": "insufficient_data",
                    "message": f"Insufficient valid records after numeric sanitization ({n_total} records remaining; minimum {min_records} required).",
                    "min_records_required": min_records,
                    "available_records": n_total,
                    "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }

            # Target Statistics
            target_series = df["bandwidth_utilization"]
            target_stats = {
                "mean": round(float(target_series.mean()), 4),
                "std": round(float(target_series.std()), 4),
                "min": round(float(target_series.min()), 4),
                "max": round(float(target_series.max()), 4),
                "unique_values_count": int(target_series.nunique())
            }

            # 4. TEMPORAL SPLIT BEFORE TARGET SHIFTING (STRICT NO DATA LEAKAGE)
            split_idx = int(n_total * 0.8)
            train_raw = df.iloc[:split_idx].copy()
            test_raw = df.iloc[split_idx:].copy()

            if len(train_raw) < 10 or len(test_raw) < 5:
                return {
                    "status": "insufficient_data",
                    "message": "Insufficient data points after temporal train/test split.",
                    "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }

            # Construct Training pairs: X_train at T, y_train at T+1 strictly within train_raw
            X_train = train_raw[FEATURE_COLUMNS].iloc[:-1].reset_index(drop=True)
            y_train = train_raw["bandwidth_utilization"].iloc[1:].reset_index(drop=True)

            # Construct Test pairs: X_test at T, y_test at T+1 strictly within test_raw
            X_test = test_raw[FEATURE_COLUMNS].iloc[:-1].reset_index(drop=True)
            y_test = test_raw["bandwidth_utilization"].iloc[1:].reset_index(drop=True)

            # Naive Persistence Baseline: Predicts y_{t+1} using bandwidth_utilization at t
            y_naive = test_raw["bandwidth_utilization"].iloc[:-1].reset_index(drop=True)

            test_timestamps = test_raw["timestamp"].iloc[:-1].reset_index(drop=True)

            # Extract window feature series for input charts (Upload, Download, Bandwidth, CPU, RAM, Signal)
            history_series = {
                "timestamps": [str(ts).split(" ")[1] if " " in str(ts) else str(ts) for ts in test_raw["timestamp"]],
                "upload_speed": [round(float(v), 2) for v in test_raw["upload_speed"]],
                "download_speed": [round(float(v), 2) for v in test_raw["download_speed"]],
                "bandwidth_utilization": [round(float(v), 2) for v in test_raw["bandwidth_utilization"]],
                "cpu_usage": [round(float(v), 2) for v in test_raw["cpu_usage"]],
                "ram_usage": [round(float(v), 2) for v in test_raw["ram_usage"]],
                "signal_strength": [round(float(v), 2) for v in test_raw["signal_strength"]]
            }

            # Extract LATEST SINGLE READING for Current ML Input card display
            latest_row = df.iloc[-1]
            current_inputs = {
                "upload_speed": round(float(latest_row["upload_speed"]), 2),
                "download_speed": round(float(latest_row["download_speed"]), 2),
                "bandwidth_utilization": round(float(latest_row["bandwidth_utilization"]), 2),
                "traffic_delta": round(float(latest_row.get("traffic_delta", 0.0)), 2),
                "signal_strength": round(float(latest_row["signal_strength"]), 2),
                "cpu_usage": round(float(latest_row["cpu_usage"]), 2),
                "ram_usage": round(float(latest_row["ram_usage"]), 2),
                "power_consumption": round(float(latest_row["power_consumption"]), 1),
                "battery_voltage": round(float(latest_row["battery_voltage"]), 2),
                "connected_client_count": int(latest_row["connected_client_count"]),
                "tower_load": round(float(latest_row["tower_load"]), 1),
                "timestamp": str(latest_row["timestamp"]).split(" ")[1] if " " in str(latest_row["timestamp"]) else str(latest_row["timestamp"])
            }

            # 5. STRICT NUMERIC DTYPE VALIDATION BEFORE TRAINING
            non_num_train = [c for c in X_train.columns if not pd.api.types.is_numeric_dtype(X_train[c])]
            non_num_test = [c for c in X_test.columns if not pd.api.types.is_numeric_dtype(X_test[c])]

            if non_num_train:
                raise ValueError(f"Non-numeric columns found in X_train: {non_num_train}")
            if non_num_test:
                raise ValueError(f"Non-numeric columns found in X_test: {non_num_test}")

            # 6. Train & Time 3 Regressors

            # Latest single reading feature vector for next-interval prediction card
            X_latest = df[FEATURE_COLUMNS].iloc[[-1]]

            # Algorithm 1: Random Forest Regressor
            t0 = time.perf_counter()
            rf_model = RandomForestRegressor(n_estimators=50, random_state=42)
            rf_model.fit(X_train, y_train)
            t_rf = time.perf_counter() - t0
            pred_rf = rf_model.predict(X_test)
            next_pred_rf = float(rf_model.predict(X_latest)[0])

            # Algorithm 2: Gradient Boosting Regressor
            t0 = time.perf_counter()
            gb_model = GradientBoostingRegressor(n_estimators=50, random_state=42)
            gb_model.fit(X_train, y_train)
            t_gb = time.perf_counter() - t0
            pred_gb = gb_model.predict(X_test)
            next_pred_gb = float(gb_model.predict(X_latest)[0])

            # Algorithm 3: XGBoost Regressor
            t0 = time.perf_counter()
            xgb_model = xgb.XGBRegressor(n_estimators=50, random_state=42, verbosity=0)
            xgb_model.fit(X_train, y_train)
            t_xgb = time.perf_counter() - t0
            pred_xgb = xgb_model.predict(X_test)
            next_pred_xgb = float(xgb_model.predict(X_latest)[0])

            # 7. Evaluate Metrics
            def calculate_metrics(y_true, y_pred, duration=0.0):
                mae = float(mean_absolute_error(y_true, y_pred))
                rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
                r2 = float(r2_score(y_true, y_pred))
                return {
                    "mae": round(mae, 4),
                    "rmse": round(rmse, 4),
                    "r2": round(r2, 4),
                    "train_time_sec": round(duration, 4),
                    "predictions": [round(float(p), 2) for p in y_pred]
                }

            rf_metrics = calculate_metrics(y_test, pred_rf, t_rf)
            gb_metrics = calculate_metrics(y_test, pred_gb, t_gb)
            xgb_metrics = calculate_metrics(y_test, pred_xgb, t_xgb)
            naive_metrics = calculate_metrics(y_test, y_naive, 0.0001)

            # 8. Transparent Model Ranking Logic & Dynamic Win Rationale
            model_candidates = [
                {"name": "Random Forest", "metrics": rf_metrics},
                {"name": "Gradient Boosting", "metrics": gb_metrics},
                {"name": "XGBoost", "metrics": xgb_metrics}
            ]

            sorted_candidates = sorted(
                model_candidates,
                key=lambda m: (m["metrics"]["rmse"], m["metrics"]["mae"], -m["metrics"]["r2"])
            )

            best_model_info = sorted_candidates[0]
            winning_name = best_model_info["name"]
            winning_r2 = best_model_info["metrics"]["r2"]
            winning_rmse = best_model_info["metrics"]["rmse"]
            winning_mae = best_model_info["metrics"]["mae"]

            # Dynamic Win Reason Generation
            min_rmse = min(m["metrics"]["rmse"] for m in model_candidates)
            min_mae = min(m["metrics"]["mae"] for m in model_candidates)

            if winning_rmse == min_rmse and winning_mae == min_mae:
                win_reason = "Lowest RMSE & Lowest MAE on current evaluation window"
            elif winning_rmse == min_rmse:
                win_reason = "Lowest RMSE on current evaluation window"
            else:
                win_reason = "Best combined metric ranking on current test window"

            is_weak_fit = (winning_r2 < 0.0)
            performance_warning = None
            if is_weak_fit:
                performance_warning = "No model currently provides a strong fit for this evaluation window (R² < 0)."

            start_time_str = str(df["timestamp"].iloc[0])
            end_time_str = str(df["timestamp"].iloc[-1])

            chart_timestamps = []
            for ts_val in test_timestamps:
                ts_str = str(ts_val)
                chart_timestamps.append(ts_str.split(" ")[1] if " " in ts_str else ts_str)

            return {
                "status": "success",
                "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "evaluation_window": {
                    "start_time": start_time_str,
                    "end_time": end_time_str,
                    "total_records": n_total,
                    "train_records": len(X_train),
                    "test_records": len(X_test),
                    "sampling_interval": "~2 seconds",
                    "window_description": f"Next available 2-second monitoring interval bandwidth utilization forecast ({n_total} records)"
                },
                "data_source_info": "Uses telemetry generated/stored by existing monitoring pipeline. No additional synthetic comparison data introduced.",
                "prediction_target": "Next available 2-second monitoring interval bandwidth utilization (%)",
                "target_statistics": target_stats,
                "current_inputs": current_inputs,
                "input_history_series": history_series,
                "next_interval_predictions": {
                    "Random Forest": round(max(next_pred_rf, 0.0), 2),
                    "Gradient Boosting": round(max(next_pred_gb, 0.0), 2),
                    "XGBoost": round(max(next_pred_xgb, 0.0), 2),
                    "target_label": "Next available monitoring interval bandwidth utilization (%)"
                },
                "best_model": {
                    "algorithm": winning_name,
                    "rmse": winning_rmse,
                    "mae": winning_mae,
                    "r2": winning_r2,
                    "train_time_sec": best_model_info["metrics"]["train_time_sec"],
                    "win_reason": win_reason,
                    "is_weak_fit": is_weak_fit,
                    "performance_warning": performance_warning
                },
                "models": {
                    "Random Forest": rf_metrics,
                    "Gradient Boosting": gb_metrics,
                    "XGBoost": xgb_metrics
                },
                "naive_baseline": {
                    "name": "Naive Persistence Baseline",
                    "mae": naive_metrics["mae"],
                    "rmse": naive_metrics["rmse"],
                    "r2": naive_metrics["r2"],
                    "predictions": naive_metrics["predictions"]
                },
                "test_series": {
                    "timestamps": chart_timestamps,
                    "actual": [round(float(a), 2) for a in y_test]
                }
            }

        except Exception as e:
            print(f"[Algorithm Comparison Engine Error]: {e}")
            return {
                "status": "error",
                "message": f"Comparison evaluation failed: {str(e)}",
                "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
