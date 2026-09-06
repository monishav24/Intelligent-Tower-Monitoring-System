"""
Synthetic Training Dataset Generator for Telecom Tower Machine Learning Models.
Generates realistic historical diurnal traffic and congestion records.
Clearly separated from real-time laptop telemetry.
"""
import numpy as np
import pandas as pd

def generate_synthetic_data(n_samples=1000, seed=42):
    """
    Generate realistic synthetic training dataframe.
    """
    np.random.seed(seed)

    # Hour of day (0-24)
    hours = np.random.uniform(0, 24, n_samples)
    diurnal = np.sin((hours - 7) * np.pi / 12)
    diurnal = np.clip(diurnal, -0.4, 1.0)

    connected_users = np.clip(40 + diurnal * 140 + np.random.normal(0, 15, n_samples), 10, 400)
    bandwidth_utilization = np.clip(15 + diurnal * 40 + (connected_users / 400.0) * 35 + np.random.normal(0, 5, n_samples), 5, 99)
    upload_speed = bandwidth_utilization * 12.0 + np.random.normal(0, 40, n_samples)
    download_speed = bandwidth_utilization * 75.0 + np.random.normal(0, 150, n_samples)
    throughput_mbps = (upload_speed + download_speed) * 8.0 / 1024.0 / 1024.0
    signal_strength = np.clip(85 - (bandwidth_utilization * 0.1) + np.random.normal(0, 8, n_samples), 10, 100)
    tower_load = np.clip(20 + (connected_users / 400.0) * 55 + bandwidth_utilization * 0.25 + np.random.normal(0, 3, n_samples), 10, 99)
    temperature = np.clip(35 + tower_load * 0.25 + np.random.normal(0, 3, n_samples), 25, 85)

    # Future network traffic (Mbps)
    future_traffic = throughput_mbps * (1.0 + np.random.uniform(-0.1, 0.35, n_samples)) + (connected_users / 400.0) * 2.5

    # Congestion risk percentage (0 to 100)
    congestion_risk = np.clip((bandwidth_utilization * 0.55) + (tower_load * 0.45) + np.random.normal(0, 3, n_samples), 0, 100)

    # Predicted Status Classification: NORMAL, WARNING, CRITICAL
    predicted_status = []
    for risk, temp, util, sig in zip(congestion_risk, temperature, bandwidth_utilization, signal_strength):
        if risk >= 80 or temp >= 80.0 or util >= 90.0 or sig < 20.0:
            predicted_status.append("CRITICAL")
        elif risk >= 60 or temp >= 60.0 or util >= 70.0 or sig < 40.0:
            predicted_status.append("WARNING")
        else:
            predicted_status.append("NORMAL")

    df = pd.DataFrame({
        "connected_users": connected_users,
        "bandwidth_utilization": bandwidth_utilization,
        "upload_speed": upload_speed,
        "download_speed": download_speed,
        "throughput_mbps": throughput_mbps,
        "signal_strength": signal_strength,
        "tower_load": tower_load,
        "temperature": temperature,
        "hour_of_day": hours,
        "future_network_traffic": future_traffic,
        "congestion_risk": congestion_risk,
        "predicted_status": predicted_status
    })

    return df
