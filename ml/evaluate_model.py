"""
Empirical Evaluation Script for Random Forest Telecom Models.
Calculates exact evaluation metrics (MAE, RMSE, R² Score for Regressors; Accuracy, Precision, Recall, F1-Score for Classifier).
Does NOT invent accuracy figures.
"""
import os
import sys
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score, accuracy_score, classification_report

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from ml.generate_training_data import generate_synthetic_data

def evaluate():
    print("=========================================================================")
    print("   RANDOM FOREST MODEL EMPIRICAL EVALUATION REPORT")
    print("=========================================================================\n")

    # Generate synthetic dataset (same seed as training generator)
    df = generate_synthetic_data(config.SYNTHETIC_SAMPLES_COUNT, seed=42)

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

    # 80/20 Train-Test Split
    X_train, X_test, y_tr_train, y_tr_test, y_rk_train, y_rk_test, y_st_train, y_st_test = train_test_split(
        X, y_traffic, y_risk, y_status, test_size=0.2, random_state=42
    )

    # 1. Regressor: Traffic Forecast
    rf_traffic = RandomForestRegressor(n_estimators=50, random_state=42)
    rf_traffic.fit(X_train, y_tr_train)
    pred_traffic = rf_traffic.predict(X_test)

    mae_tr = mean_absolute_error(y_tr_test, pred_traffic)
    rmse_tr = np.sqrt(mean_squared_error(y_tr_test, pred_traffic))
    r2_tr = r2_score(y_tr_test, pred_traffic)

    print("1. TRAFFIC FORECAST REGRESSOR METRICS:")
    print(f"   - MAE:  {mae_tr:.4f} Mbps")
    print(f"   - RMSE: {rmse_tr:.4f} Mbps")
    print(f"   - R²:   {r2_tr:.4f}\n")

    # 2. Regressor: Congestion Risk
    rf_risk = RandomForestRegressor(n_estimators=50, random_state=42)
    rf_risk.fit(X_train, y_rk_train)
    pred_risk = rf_risk.predict(X_test)

    mae_rk = mean_absolute_error(y_rk_test, pred_risk)
    rmse_rk = np.sqrt(mean_squared_error(y_rk_test, pred_risk))
    r2_rk = r2_score(y_rk_test, pred_risk)

    print("2. CONGESTION RISK REGRESSOR METRICS:")
    print(f"   - MAE:  {mae_rk:.4f} %")
    print(f"   - RMSE: {rmse_rk:.4f} %")
    print(f"   - R²:   {r2_rk:.4f}\n")

    # 3. Classifier: Predicted Status
    rf_status = RandomForestClassifier(n_estimators=50, random_state=42)
    rf_status.fit(X_train, y_st_train)
    pred_status = rf_status.predict(X_test)

    acc_st = accuracy_score(y_st_test, pred_status)

    print("3. PREDICTED STATUS CLASSIFIER METRICS:")
    print(f"   - Accuracy: {acc_st * 100.0:.2f} %")
    print("\n   Detailed Classification Report:")
    print(classification_report(y_st_test, pred_status, digits=4))

    print("=========================================================================")
    print("   FEATURE IMPORTANCE ANALYSIS:")
    print("=========================================================================")
    for feat, imp in zip(features, rf_status.feature_importances_):
        print(f"   - {feat:25s}: {imp * 100.0:.2f}%")
    print("=========================================================================\n")

if __name__ == "__main__":
    evaluate()
