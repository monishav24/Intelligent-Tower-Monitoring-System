"""
SQLite Database module managing time-series readings, system health, simulated tower parameters,
hotspot data, ML predictions, and alerts.
Guarantees every telemetry cycle inserts a NEW row with autoincremented ID and timestamp.
"""
import sqlite3
import os
import sys
import json
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

def get_db():
    """Create SQLite database connection."""
    os.makedirs(os.path.dirname(config.DATABASE_PATH), exist_ok=True)
    conn = sqlite3.connect(config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize all SQLite tables according to specification with schema migration."""
    conn = get_db()
    c = conn.cursor()

    # 1. Real-Time Telemetry & Network Readings Table
    c.execute("""
    CREATE TABLE IF NOT EXISTS tower_readings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        bytes_sent INTEGER NOT NULL,
        bytes_recv INTEGER NOT NULL,
        upload_speed REAL NOT NULL,
        download_speed REAL NOT NULL,
        total_network_traffic REAL NOT NULL,
        traffic REAL DEFAULT 0.0,
        delay REAL DEFAULT 0.0,
        throughput REAL DEFAULT 0.0,
        propagation_time REAL DEFAULT 0.0,
        ram_usage REAL DEFAULT 0.0,
        temperature REAL,
        bandwidth_utilization REAL NOT NULL,
        signal_strength REAL NOT NULL,
        wifi_status TEXT NOT NULL,
        ssid TEXT NOT NULL,
        internet_status TEXT DEFAULT 'ONLINE'
    )
    """)

    # Schema migration checks for existing database tables
    existing_cols = [row[1] for row in c.execute("PRAGMA table_info(tower_readings)").fetchall()]
    new_cols = {
        "traffic": "REAL DEFAULT 0.0",
        "delay": "REAL DEFAULT 0.0",
        "throughput": "REAL DEFAULT 0.0",
        "propagation_time": "REAL DEFAULT 0.0",
        "ram_usage": "REAL DEFAULT 0.0",
        "temperature": "REAL"
    }
    for col, col_def in new_cols.items():
        if col not in existing_cols:
            try:
                c.execute(f"ALTER TABLE tower_readings ADD COLUMN {col} {col_def}")
            except Exception as e:
                print(f"[DB Migration Warning] Could not add column {col}: {e}")

    # 2. Laptop System Health Readings
    c.execute("""
    CREATE TABLE IF NOT EXISTS system_health (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        cpu_usage REAL NOT NULL,
        ram_usage REAL NOT NULL,
        battery_percentage REAL,
        battery_status TEXT,
        system_temperature REAL,
        temperature_source TEXT NOT NULL
    )
    """)

    # 3. Simulated Tower Parameters
    c.execute("""
    CREATE TABLE IF NOT EXISTS simulated_tower (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        power_consumption REAL NOT NULL,
        battery_voltage REAL NOT NULL,
        connected_users INTEGER NOT NULL,
        tower_load REAL NOT NULL
    )
    """)

    # 4. System Status Summary
    c.execute("""
    CREATE TABLE IF NOT EXISTS system_status (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        overall_status TEXT NOT NULL,
        anomaly_status TEXT NOT NULL,
        data_source TEXT NOT NULL,
        is_demo_mode INTEGER DEFAULT 0,
        demo_scenario TEXT DEFAULT 'NORMAL'
    )
    """)

    # 5. ML Predictions Table
    c.execute("""
    CREATE TABLE IF NOT EXISTS predictions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        predicted_network_traffic REAL NOT NULL,
        predicted_traffic REAL DEFAULT 0.0,
        predicted_delay REAL DEFAULT 0.0,
        predicted_throughput REAL DEFAULT 0.0,
        predicted_propagation_time REAL DEFAULT 0.0,
        predicted_ram_usage REAL DEFAULT 0.0,
        active_model TEXT DEFAULT 'Random Forest',
        congestion_risk REAL NOT NULL,
        predicted_status TEXT NOT NULL
    )
    """)

    pred_cols = [row[1] for row in c.execute("PRAGMA table_info(predictions)").fetchall()]
    new_pred_cols = {
        "predicted_traffic": "REAL DEFAULT 0.0",
        "predicted_delay": "REAL DEFAULT 0.0",
        "predicted_throughput": "REAL DEFAULT 0.0",
        "predicted_propagation_time": "REAL DEFAULT 0.0",
        "predicted_ram_usage": "REAL DEFAULT 0.0",
        "active_model": "TEXT DEFAULT 'Random Forest'"
    }
    for col, col_def in new_pred_cols.items():
        if col not in pred_cols:
            try:
                c.execute(f"ALTER TABLE predictions ADD COLUMN {col} {col_def}")
            except Exception as e:
                print(f"[DB Migration Warning] Could not add column {col} to predictions: {e}")

    # 6. System Alerts Log
    c.execute("""
    CREATE TABLE IF NOT EXISTS alerts (
        alert_id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        severity TEXT NOT NULL,
        parameter TEXT NOT NULL,
        message TEXT NOT NULL,
        status TEXT DEFAULT 'ACTIVE'
    )
    """)

    # 7. Mobile Hotspot Data
    c.execute("""
    CREATE TABLE IF NOT EXISTS hotspot_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        hotspot_status TEXT NOT NULL,
        interface_name TEXT,
        total_traffic_mb REAL NOT NULL,
        upload_speed REAL NOT NULL,
        download_speed REAL NOT NULL,
        client_count INTEGER,
        client_ip_list TEXT,
        client_details_status TEXT NOT NULL
    )
    """)

    conn.commit()
    conn.close()

def insert_telemetry_snapshot(reading):
    """Insert a unified telemetry snapshot into SQLite tables as a NEW row."""
    conn = get_db()
    c = conn.cursor()

    ts = reading.get("timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    # Extract 5 ML parameters + 1 Hardware Temperature
    traffic_val = reading.get("traffic", reading.get("total_network_traffic", 0.0))
    delay_val = reading.get("delay", reading.get("delay_ms", 0.0))
    throughput_val = reading.get("throughput", reading.get("throughput_mbps", 0.0))
    prop_val = reading.get("propagation_time", reading.get("propagation_time_ms", 0.0))
    ram_val = reading.get("ram_usage", 0.0)
    temp_val = reading.get("temperature", reading.get("system_temperature"))

    # Network & Telemetry Table
    c.execute("""
    INSERT INTO tower_readings (
        timestamp, bytes_sent, bytes_recv, upload_speed, download_speed,
        total_network_traffic, traffic, delay, throughput, propagation_time,
        ram_usage, temperature, bandwidth_utilization, signal_strength,
        wifi_status, ssid, internet_status
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        ts, reading.get("bytes_sent", 0), reading.get("bytes_recv", 0),
        reading.get("upload_speed", 0.0), reading.get("download_speed", 0.0),
        reading.get("total_network_traffic", 0.0), traffic_val, delay_val,
        throughput_val, prop_val, ram_val, temp_val,
        reading.get("bandwidth_utilization", 0.0), reading.get("signal_strength", 0.0),
        reading.get("wifi_status", "UNKNOWN"), reading.get("ssid", "N/A"),
        reading.get("internet_status", "ONLINE")
    ))
    inserted_id = c.lastrowid

    # System Health
    c.execute("""
    INSERT INTO system_health (timestamp, cpu_usage, ram_usage, battery_percentage, battery_status, system_temperature, temperature_source)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        ts, reading.get("cpu_usage", 0.0), ram_val,
        reading.get("battery_percentage"), reading.get("battery_status", "N/A"),
        temp_val, reading.get("temperature_source", "ESP32 / Host Laptop")
    ))

    # Simulated Tower
    c.execute("""
    INSERT INTO simulated_tower (timestamp, power_consumption, battery_voltage, connected_users, tower_load)
    VALUES (?, ?, ?, ?, ?)
    """, (
        ts, reading.get("power_consumption", 0.0), reading.get("battery_voltage", 0.0),
        reading.get("connected_client_count", 0), reading.get("tower_load", 0.0)
    ))

    # System Status
    c.execute("""
    INSERT INTO system_status (timestamp, overall_status, anomaly_status, data_source, is_demo_mode, demo_scenario)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (
        ts, reading.get("overall_status", "NORMAL"), reading.get("anomaly_status", "NORMAL"),
        reading.get("data_source", "Laptop Hybrid"), 1 if reading.get("is_demo_mode") else 0,
        reading.get("demo_scenario", "NORMAL")
    ))

    # Predictions
    c.execute("""
    INSERT INTO predictions (
        timestamp, predicted_network_traffic, predicted_traffic, predicted_delay,
        predicted_throughput, predicted_propagation_time, predicted_ram_usage,
        active_model, congestion_risk, predicted_status
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        ts, reading.get("predicted_traffic", reading.get("predicted_network_traffic", 0.0)),
        reading.get("predicted_traffic", 0.0), reading.get("predicted_delay", 0.0),
        reading.get("predicted_throughput", 0.0), reading.get("predicted_propagation_time", 0.0),
        reading.get("predicted_ram_usage", 0.0), reading.get("active_model", "Random Forest"),
        reading.get("congestion_risk", 0.0), reading.get("predicted_status", "NORMAL")
    ))

    # Hotspot
    client_ips_json = json.dumps(reading.get("client_ip_list", []))
    c.execute("""
    INSERT INTO hotspot_data (timestamp, hotspot_status, interface_name, total_traffic_mb, upload_speed, download_speed, client_count, client_ip_list, client_details_status)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        ts, reading.get("hotspot_status", "ACTIVE"), reading.get("hotspot_interface", "N/A"),
        reading.get("hotspot_traffic_mb", 0.0), reading.get("upload_speed", 0.0),
        reading.get("download_speed", 0.0), reading.get("connected_client_count", 0),
        client_ips_json, reading.get("connection_status", "Real-Time Hotspot Device Scanning")
    ))

    conn.commit()
    conn.close()
    return inserted_id

def insert_alert(alert):
    """Insert an alert entry into database."""
    conn = get_db()
    c = conn.cursor()
    c.execute("""
    INSERT INTO alerts (timestamp, severity, parameter, message, status)
    VALUES (?, ?, ?, ?, ?)
    """, (
        alert.get("timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        alert.get("severity", "WARNING"),
        alert.get("parameter", "SYSTEM"),
        alert.get("message", ""),
        alert.get("status", "ACTIVE")
    ))
    conn.commit()
    conn.close()

def get_latest_snapshot():
    """Query newest SQLite row. Zero object caching."""
    conn = get_db()
    c = conn.cursor()

    c.execute("SELECT * FROM tower_readings ORDER BY id DESC LIMIT 1")
    tr_row = c.fetchone()
    if not tr_row:
        conn.close()
        return None
    tr = dict(tr_row)

    c.execute("SELECT * FROM system_health ORDER BY id DESC LIMIT 1")
    sh_row = c.fetchone()
    sh = dict(sh_row) if sh_row else {}

    c.execute("SELECT * FROM simulated_tower ORDER BY id DESC LIMIT 1")
    st_row = c.fetchone()
    st = dict(st_row) if st_row else {}

    c.execute("SELECT * FROM system_status ORDER BY id DESC LIMIT 1")
    ss_row = c.fetchone()
    ss = dict(ss_row) if ss_row else {}

    c.execute("SELECT * FROM predictions ORDER BY id DESC LIMIT 1")
    pr_row = c.fetchone()
    pr = dict(pr_row) if pr_row else {}

    c.execute("SELECT * FROM hotspot_data ORDER BY id DESC LIMIT 1")
    hd_row = c.fetchone()
    hd = dict(hd_row) if hd_row else {}

    conn.close()

    # Parse JSON client_ip_list
    client_ips = []
    if hd.get("client_ip_list"):
        try:
            client_ips = json.loads(hd["client_ip_list"])
        except Exception:
            client_ips = []

    # Extract values from tables
    raw_internet = tr.get("internet_status")
    if not raw_internet or str(raw_internet).strip().upper() in ("NONE", "NULL", ""):
        raw_internet = "ONLINE"

    raw_cc = st.get("connected_users")
    if raw_cc is None or str(raw_cc).strip().upper() in ("NONE", "NULL", ""):
        raw_cc = hd.get("client_count", 0)
    try:
        raw_cc = int(raw_cc)
    except Exception:
        raw_cc = 0

    raw_temp = tr.get("temperature")
    if raw_temp is None:
        raw_temp = sh.get("system_temperature")

    if raw_temp is not None:
        try:
            raw_temp = round(float(raw_temp), 1)
        except Exception:
            raw_temp = None

    raw_hotspot = hd.get("hotspot_status")
    if not raw_hotspot or str(raw_hotspot).strip().upper() in ("NONE", "NULL", ""):
        raw_hotspot = "ACTIVE"
    elif str(raw_hotspot).strip().upper() in ("TRUE", "ON", "1"):
        raw_hotspot = "ACTIVE"

    # 5 ML Parameters + 1 Hardware Temperature
    traffic = round(float(tr.get("traffic", tr.get("total_network_traffic", 0.0)) or 0.0), 2)
    delay = round(float(tr.get("delay", 0.0) or 0.0), 2)
    throughput = round(float(tr.get("throughput", tr.get("download_speed", 0.0)) or 0.0), 3)
    propagation_time = round(float(tr.get("propagation_time", delay / 2.0) or 0.0), 2)
    ram_usage = round(float(tr.get("ram_usage", sh.get("ram_usage", 0.0)) or 0.0), 1)

    snapshot = {
        "id": tr.get("id"),
        "timestamp": tr.get("timestamp"),
        "bytes_sent": tr.get("bytes_sent", 0),
        "bytes_recv": tr.get("bytes_recv", 0),
        "upload_speed": tr.get("upload_speed", 0.0),
        "download_speed": tr.get("download_speed", 0.0),
        "total_network_traffic": tr.get("total_network_traffic", 0.0),
        "bandwidth_utilization": tr.get("bandwidth_utilization", 0.0),
        "signal_strength": tr.get("signal_strength", 0.0),
        "wifi_status": tr.get("wifi_status", "ACTIVE"),
        "ssid": tr.get("ssid", "N/A"),
        "internet_status": raw_internet,

        # 5 ML Parameters
        "traffic": traffic,
        "delay": delay,
        "delay_ms": delay,
        "throughput": throughput,
        "throughput_mbps": throughput,
        "propagation_time": propagation_time,
        "propagation_time_ms": propagation_time,
        "ram_usage": ram_usage,

        # Hardware Sensor (Temperature Sensor ONLY)
        "temperature": raw_temp,
        "system_temperature": raw_temp,
        "temperature_source": sh.get("temperature_source", "Temperature Sensor"),

        "cpu_usage": sh.get("cpu_usage", 0.0),
        "battery_percentage": sh.get("battery_percentage"),
        "battery_status": sh.get("battery_status", "N/A"),

        "power_consumption": st.get("power_consumption", 0.0),
        "battery_voltage": st.get("battery_voltage", 0.0),
        "connected_client_count": raw_cc,
        "connected_users": raw_cc,
        "tower_load": st.get("tower_load", 0.0),

        "overall_status": ss.get("overall_status", "NORMAL"),
        "anomaly_status": ss.get("anomaly_status", "NORMAL"),
        "data_source": ss.get("data_source", "ESP32 / Host"),
        "esp32_online": 1 if "ESP32" in str(ss.get("data_source", "")) else 0,
        "is_demo_mode": bool(ss.get("is_demo_mode", 0)),
        "is_manual_override": bool(ss.get("is_demo_mode", 0)),
        "demo_scenario": ss.get("demo_scenario", "NORMAL"),
        "active_scenario": ss.get("demo_scenario", "NORMAL"),

        # Predictions
        "predicted_network_traffic": pr.get("predicted_network_traffic", 0.0),
        "predicted_traffic": pr.get("predicted_traffic", pr.get("predicted_network_traffic", 0.0)),
        "predicted_delay": pr.get("predicted_delay", 0.0),
        "predicted_throughput": pr.get("predicted_throughput", 0.0),
        "predicted_propagation_time": pr.get("predicted_propagation_time", 0.0),
        "predicted_ram_usage": pr.get("predicted_ram_usage", 0.0),
        "active_model": pr.get("active_model", "Random Forest"),
        "congestion_risk": pr.get("congestion_risk", 0.0),
        "predicted_status": pr.get("predicted_status", "NORMAL"),

        "hotspot_status": raw_hotspot,
        "hotspot_interface": hd.get("interface_name", "N/A"),
        "client_ip_list": client_ips,
        "hotspot_client_details_status": hd.get("client_details_status", "Real-Time Hotspot Device Scanning")
    }

    return snapshot

def get_history(limit=30):
    """Query chronologically ordered history points for charts."""
    conn = get_db()
    c = conn.cursor()
    c.execute("""
    SELECT 
        tr.id, tr.timestamp, tr.upload_speed, tr.download_speed, tr.total_network_traffic,
        tr.traffic, tr.delay, tr.throughput, tr.propagation_time, tr.ram_usage, tr.temperature,
        tr.bandwidth_utilization, tr.signal_strength, tr.wifi_status, COALESCE(tr.internet_status, 'ONLINE') AS internet_status,
        sh.cpu_usage, sh.system_temperature,
        st.power_consumption, st.battery_voltage, COALESCE(st.connected_users, 0) AS connected_client_count, st.tower_load,
        ss.overall_status
    FROM tower_readings tr
    LEFT JOIN system_health sh ON tr.id = sh.id
    LEFT JOIN simulated_tower st ON tr.id = st.id
    LEFT JOIN system_status ss ON tr.id = ss.id
    ORDER BY tr.id DESC LIMIT ?
    """, (limit,))
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in reversed(rows)]

def get_telemetry_diagnostic():
    """Diagnostic helper returning row count, latest vs previous timestamps, and latency seconds."""
    conn = get_db()
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM tower_readings")
    row_count = c.fetchone()[0]

    c.execute("SELECT id, timestamp, traffic, delay, throughput, propagation_time, ram_usage, temperature FROM tower_readings ORDER BY id DESC LIMIT 2")
    rows = c.fetchall()
    conn.close()

    if not rows:
        return {
            "row_count": 0,
            "latest_timestamp": None,
            "previous_timestamp": None,
            "seconds_since_latest": None,
            "is_live": False,
            "latest_telemetry": None
        }

    latest = dict(rows[0])
    prev = dict(rows[1]) if len(rows) > 1 else None

    latest_ts_str = latest["timestamp"]
    prev_ts_str = prev["timestamp"] if prev else None

    sec_since = None
    try:
        latest_dt = datetime.strptime(latest_ts_str, "%Y-%m-%d %H:%M:%S")
        sec_since = round((datetime.now() - latest_dt).total_seconds(), 1)
    except Exception:
        pass

    return {
        "row_count": row_count,
        "latest_timestamp": latest_ts_str,
        "previous_timestamp": prev_ts_str,
        "seconds_since_latest": sec_since,
        "is_live": (sec_since is not None and sec_since <= 6.0),
        "latest_telemetry": latest
    }

def get_active_alerts(limit=20):
    """Query recent active alerts."""
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM alerts ORDER BY alert_id DESC LIMIT ?", (limit,))
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]
