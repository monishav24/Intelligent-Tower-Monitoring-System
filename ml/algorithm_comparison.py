"""
Live 3-Algorithm Machine Learning Comparison Engine & Model Selection.
Compairs Random Forest, Gradient Boosting, and Extra Trees Regressors
on ONE common real telemetry dataset from SQLite.

Key Specifications Enforced:
1. Exactly 3 ML Algorithms:
   - Random Forest (RandomForestRegressor)
   - Gradient Boosting (MultiOutputRegressor wrapping GradientBoostingRegressor)
   - Extra Trees (ExtraTreesRegressor)
2. One Common Real Telemetry Dataset from SQLite.
3. 5 Multi-Output Prediction Targets:
   ['traffic', 'delay', 'throughput', 'propagation_time', 'ram_usage']
4. Shared Preprocessing & Chronological Train/Test Split (80% / 20%).
5. Target-level & Overall Metric Calculation: MAE, RMSE, R².
6. Documented 10-Point Composite Performance Score:
   Score = 10 * (0.4 * max(0, R²_avg) + 0.3 * 1/(1 + MAE_avg) + 0.3 * 1/(1 + RMSE_avg))
7. Dynamic Top Performer Selection & Automatic Model Switching.
8. Persistence of models and active model metadata to disk.
"""
import os
import sys
import time
import pickle
from datetime import datetime
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor, ExtraTreesRegressor
from sklearn.multioutput import MultiOutputRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
import database.database as db

MINIMUM_VALID_RECORDS = 50
DEFAULT_WINDOW_SIZE = 200

MODEL_REGISTRY_PATH = os.path.join(config.BASE_DIR, "models", "multi_model_registry.pkl")

# 5 MULTI-OUTPUT PREDICTION TARGETS
TARGET_COLUMNS = [
    "traffic",
    "delay",
    "throughput",
    "propagation_time",
    "ram_usage"
]

# INPUT FEATURES AVAILABLE AT PREDICTION TIME (Temperature is a hardware feature, NOT a target)
FEATURE_COLUMNS = [
    "traffic",
    "delay",
    "throughput",
    "propagation_time",
    "ram_usage",
    "temperature",
    "hour",
    "minute",
    "day_of_week"
]

class AlgorithmComparisonEngine:
    """
    Evaluates Random Forest, Gradient Boosting, and Extra Trees on a single common SQLite dataset.
    """

    @staticmethod
    def evaluate_live_data(min_records=MINIMUM_VALID_RECORDS, window_size=DEFAULT_WINDOW_SIZE):
        """
        Fetch stored telemetry history from SQLite, preprocess, perform chronological 80/20 split,
        train all 3 algorithms on the SAME dataset and SAME split for all 5 targets,
        evaluate MAE/RMSE/R², calculate 10-point composite scores, dynamically determine winner, and persist.
        """
        raw_history = db.get_history(limit=window_size)
        available_count = len(raw_history)

        if available_count < min_records:
            return {
                "status": "insufficient_data",
                "message": f"Insufficient live telemetry for reliable model training ({available_count} valid records available; minimum {min_records} required). Continue collecting telemetry before training.",
                "min_records_required": min_records,
                "available_records": available_count,
                "data_source_info": "Uses live historical telemetry stored in SQLite. No synthetic data used.",
                "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

        try:
            df = pd.DataFrame(raw_history)

            # Ensure columns exist with fallbacks
            if "traffic" not in df.columns:
                df["traffic"] = df.get("total_network_traffic", 0.0)
            if "delay" not in df.columns:
                df["delay"] = 1.0
            if "throughput" not in df.columns:
                df["throughput"] = df.get("download_speed", 0.0)
            if "propagation_time" not in df.columns:
                df["propagation_time"] = df["delay"] / 2.0
            if "ram_usage" not in df.columns:
                df["ram_usage"] = 50.0
            if "temperature" not in df.columns:
                df["temperature"] = df.get("system_temperature", 28.4)

            # Feature Engineering: Extract Time Features
            df["timestamp_dt"] = pd.to_datetime(df["timestamp"], errors="coerce")
            df["hour"] = df["timestamp_dt"].dt.hour.fillna(12).astype(int)
            df["minute"] = df["timestamp_dt"].dt.minute.fillna(0).astype(int)
            df["day_of_week"] = df["timestamp_dt"].dt.dayofweek.fillna(0).astype(int)

            # Preprocessing: Sanitize numeric types
            all_required_cols = list(set(FEATURE_COLUMNS + TARGET_COLUMNS))
            for col in all_required_cols:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors="coerce")
                else:
                    df[col] = 0.0

            df.replace([np.inf, -np.inf], np.nan, inplace=True)
            df.ffill(inplace=True)
            df.bfill(inplace=True)
            df.fillna(0.0, inplace=True)

            n_total = len(df)
            if n_total < min_records:
                return {
                    "status": "insufficient_data",
                    "message": f"Insufficient valid records after preprocessing ({n_total} remaining; minimum {min_records} required). Continue collecting telemetry before training.",
                    "min_records_required": min_records,
                    "available_records": n_total,
                    "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }

            # Chronological 80/20 Train/Test Split
            split_idx = int(n_total * 0.8)
            train_df = df.iloc[:split_idx].copy()
            test_df = df.iloc[split_idx:].copy()

            if len(train_df) < 10 or len(test_df) < 5:
                return {
                    "status": "insufficient_data",
                    "message": "Insufficient data points after chronological train/test split.",
                    "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }

            # Prepare X and Y for multi-output regression (Predicting T+1 from T)
            X_train = train_df[FEATURE_COLUMNS].iloc[:-1].reset_index(drop=True)
            Y_train = train_df[TARGET_COLUMNS].iloc[1:].reset_index(drop=True)

            X_test = test_df[FEATURE_COLUMNS].iloc[:-1].reset_index(drop=True)
            Y_test = test_df[TARGET_COLUMNS].iloc[1:].reset_index(drop=True)

            test_timestamps = [str(ts).split(" ")[1] if " " in str(ts) else str(ts) for ts in test_df["timestamp"].iloc[1:]]

            # Latest Reading Feature Vector for Live Prediction
            latest_row = df.iloc[[-1]][FEATURE_COLUMNS]

            # -------------------------------------------------------------
            # Train the 3 ML Algorithms on the EXACT SAME Dataset & Split
            # -------------------------------------------------------------

            # 1. Random Forest
            t0 = time.perf_counter()
            rf_model = RandomForestRegressor(n_estimators=50, random_state=42)
            rf_model.fit(X_train, Y_train)
            t_rf = time.perf_counter() - t0
            pred_rf = rf_model.predict(X_test)
            live_pred_rf = rf_model.predict(latest_row)[0]

            # 2. Gradient Boosting
            t0 = time.perf_counter()
            gb_model = MultiOutputRegressor(GradientBoostingRegressor(n_estimators=50, random_state=42))
            gb_model.fit(X_train, Y_train)
            t_gb = time.perf_counter() - t0
            pred_gb = gb_model.predict(X_test)
            live_pred_gb = gb_model.predict(latest_row)[0]

            # 3. Extra Trees
            t0 = time.perf_counter()
            et_model = ExtraTreesRegressor(n_estimators=50, random_state=42)
            et_model.fit(X_train, Y_train)
            t_et = time.perf_counter() - t0
            pred_et = et_model.predict(X_test)
            live_pred_et = et_model.predict(latest_row)[0]

            # Evaluate Per-Target and Overall Metrics for each Algorithm
            algorithms = {
                "Random Forest": {"model": rf_model, "pred": pred_rf, "live": live_pred_rf, "time": t_rf},
                "Gradient Boosting": {"model": gb_model, "pred": pred_gb, "live": live_pred_gb, "time": t_gb},
                "Extra Trees": {"model": et_model, "pred": pred_et, "live": live_pred_et, "time": t_et}
            }

            model_metrics = {}
            for name, algo_info in algorithms.items():
                preds_matrix = algo_info["pred"]
                live_vector = algo_info["live"]
                target_evals = {}
                mae_list, rmse_list, r2_list = [], [], []

                for i, target_name in enumerate(TARGET_COLUMNS):
                    y_true = Y_test[target_name].values
                    y_pred = preds_matrix[:, i]
                    mae = float(mean_absolute_error(y_true, y_pred))
                    rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
                    r2 = float(r2_score(y_true, y_pred))

                    target_evals[target_name] = {
                        "mae": round(mae, 4),
                        "rmse": round(rmse, 4),
                        "r2": round(r2, 4),
                        "predictions": [round(float(p), 2) for p in y_pred],
                        "actual": [round(float(a), 2) for a in y_true]
                    }
                    mae_list.append(mae)
                    rmse_list.append(rmse)
                    r2_list.append(r2)

                avg_mae = float(np.mean(mae_list))
                avg_rmse = float(np.mean(rmse_list))
                avg_r2 = float(np.mean(r2_list))

                model_metrics[name] = {
                    "targets": target_evals,
                    "avg_mae": round(avg_mae, 4),
                    "avg_rmse": round(avg_rmse, 4),
                    "avg_r2": round(avg_r2, 4),
                    "train_time_sec": round(algo_info["time"], 4),
                    "live_predictions": {
                        "traffic": round(max(float(live_vector[0]), 0.0), 2),
                        "delay": round(max(float(live_vector[1]), 0.1), 2),
                        "throughput": round(max(float(live_vector[2]), 0.0), 2),
                        "propagation_time": round(max(float(live_vector[3]), 0.05), 2),
                        "ram_usage": round(min(max(float(live_vector[4]), 0.0), 100.0), 1)
                    }
                }

            # Calculate Documented Composite Overall Performance Scores on a 0 - 10 Point Scale
            overall_scores = {}
            for name, m in model_metrics.items():
                r2_norm = max(0.0, m["avg_r2"])
                mae_norm = 1.0 / (1.0 + m["avg_mae"])
                rmse_norm = 1.0 / (1.0 + m["avg_rmse"])
                score = round(10.0 * (0.4 * r2_norm + 0.3 * mae_norm + 0.3 * rmse_norm), 2)
                overall_scores[name] = score
                m["overall_score"] = score

            # Dynamically Determine Top-Performing Algorithm
            sorted_winners = sorted(overall_scores.items(), key=lambda item: item[1], reverse=True)
            active_model_name = sorted_winners[0][0]
            top_score = sorted_winners[0][1]

            active_live_predictions = model_metrics[active_model_name]["live_predictions"]

            # Save Trained Models & Metadata Registry to Disk
            os.makedirs(os.path.dirname(MODEL_REGISTRY_PATH), exist_ok=True)
            registry_payload = {
                "models": {name: algo_info["model"] for name, algo_info in algorithms.items()},
                "active_model_name": active_model_name,
                "overall_scores": overall_scores,
                "model_metrics": model_metrics,
                "last_training": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "feature_columns": FEATURE_COLUMNS,
                "target_columns": TARGET_COLUMNS,
                "score_scale": 10
            }
            with open(MODEL_REGISTRY_PATH, "wb") as f:
                pickle.dump(registry_payload, f)

            # Prepare Parameter Comparison Charts Data (Actual vs RF vs GB vs ET)
            parameter_comparison_series = {}
            for target_name in TARGET_COLUMNS:
                actual_vals = [round(float(a), 2) for a in Y_test[target_name].values]
                rf_vals = model_metrics["Random Forest"]["targets"][target_name]["predictions"]
                gb_vals = model_metrics["Gradient Boosting"]["targets"][target_name]["predictions"]
                et_vals = model_metrics["Extra Trees"]["targets"][target_name]["predictions"]

                parameter_comparison_series[target_name] = {
                    "timestamps": test_timestamps,
                    "actual": actual_vals,
                    "rf_predictions": rf_vals,
                    "gb_predictions": gb_vals,
                    "et_predictions": et_vals
                }

            start_time_str = str(df["timestamp"].iloc[0])
            end_time_str = str(df["timestamp"].iloc[-1])

            return {
                "status": "success",
                "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "active_model": active_model_name,
                "score_scale": 10,
                "overall_scores": overall_scores,
                "top_performer": {
                    "algorithm": active_model_name,
                    "score": top_score,
                    "score_scale": 10,
                    "status": "ACTIVE"
                },
                "dataset_info": {
                    "source": "Live SQLite Telemetry",
                    "total_samples": n_total,
                    "train_samples": len(X_train),
                    "test_samples": len(X_test),
                    "parameters": TARGET_COLUMNS,
                    "hardware_sensor": "Temperature Sensor",
                    "last_training": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "start_time": start_time_str,
                    "end_time": end_time_str
                },
                "models": model_metrics,
                "parameter_comparison": parameter_comparison_series,
                "live_predictions": active_live_predictions
            }

        except Exception as e:
            print(f"[Algorithm Comparison Engine Error]: {e}")
            import traceback
            traceback.print_exc()
            return {
                "status": "error",
                "message": f"Comparison evaluation failed: {str(e)}",
                "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
