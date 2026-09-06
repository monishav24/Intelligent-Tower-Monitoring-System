"""
SQLite Database module for storing time-series tower readings and alerts.
"""
import sqlite3
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from datetime import datetime
import config

def get_db_connection():
    """Establish connection to SQLite database."""
    os.makedirs(os.path.dirname(config.DATABASE_PATH), exist_ok=True)
    conn = sqlite3.connect(config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database tables if they do not exist."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Table for time-series sensor and network readings
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tower_readings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        temperature REAL NOT NULL,
        power_consumption REAL NOT NULL,
        battery_voltage REAL NOT NULL,
        bytes_sent INTEGER NOT NULL,
        bytes_recv INTEGER NOT NULL,
        upload_speed REAL NOT NULL,
        download_speed REAL NOT NULL,
        total_traffic_mb REAL NOT NULL,
        bandwidth_utilization REAL NOT NULL,
        signal_strength REAL NOT NULL,
        connected_users INTEGER NOT NULL,
        tower_load REAL NOT NULL,
        tower_status TEXT NOT NULL,
        anomaly_status TEXT NOT NULL,
        predicted_traffic REAL,
        congestion_risk REAL,
        predicted_status TEXT,
        is_demo_mode INTEGER DEFAULT 0,
        demo_scenario TEXT DEFAULT 'NORMAL'
    )
    """)

    # Table for system alerts log
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS alerts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        severity TEXT NOT NULL,
        parameter TEXT NOT NULL,
        message TEXT NOT NULL,
        value REAL,
        threshold REAL
    )
    """)

    conn.commit()
    conn.close()

def insert_reading(data):
    """Insert a new reading dictionary into database."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO tower_readings (
        timestamp, temperature, power_consumption, battery_voltage,
        bytes_sent, bytes_recv, upload_speed, download_speed,
        total_traffic_mb, bandwidth_utilization, signal_strength,
        connected_users, tower_load, tower_status, anomaly_status,
        predicted_traffic, congestion_risk, predicted_status,
        is_demo_mode, demo_scenario
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data.get("timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        data.get("temperature", 0.0),
        data.get("power_consumption", 0.0),
        data.get("battery_voltage", 0.0),
        data.get("bytes_sent", 0),
        data.get("bytes_recv", 0),
        data.get("upload_speed", 0.0),
        data.get("download_speed", 0.0),
        data.get("total_traffic_mb", 0.0),
        data.get("bandwidth_utilization", 0.0),
        data.get("signal_strength", 0.0),
        data.get("connected_users", 0),
        data.get("tower_load", 0.0),
        data.get("tower_status", "NORMAL"),
        data.get("anomaly_status", "NORMAL"),
        data.get("predicted_traffic", 0.0),
        data.get("congestion_risk", 0.0),
        data.get("predicted_status", "NORMAL"),
        1 if data.get("is_demo_mode") else 0,
        data.get("demo_scenario", "NORMAL")
    ))

    conn.commit()
    conn.close()

def insert_alert(alert):
    """Insert a generated alert into alerts table."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO alerts (timestamp, severity, parameter, message, value, threshold)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (
        alert.get("timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        alert.get("severity", "WARNING"),
        alert.get("parameter", "SYSTEM"),
        alert.get("message", ""),
        alert.get("value", 0.0),
        alert.get("threshold", 0.0)
    ))

    conn.commit()
    conn.close()

def get_latest_reading():
    """Retrieve the most recent reading from database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tower_readings ORDER BY id DESC LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_history(limit=50):
    """Retrieve recent readings for time-series charts."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tower_readings ORDER BY id DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    # Return chronologically sorted (oldest first for plotting)
    return [dict(r) for r in reversed(rows)]

def get_recent_alerts(limit=20):
    """Retrieve active and recent alerts."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM alerts ORDER BY id DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]
