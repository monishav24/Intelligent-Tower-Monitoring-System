# INTELLIGENT TELECOM TOWER MONITORING AND ALERT SYSTEM

> **ECE Final-Year Project Prototype (~75% Completion)**  
> *Laptop-Based Real-Time Network and System Monitoring Prototype with Simulated Telecom Tower Parameters*

---

## 📌 1. Project Overview

The **Intelligent Telecom Tower Monitoring and Alert System** is a software-hardware integrated engineering solution designed to continuously monitor telecom tower infrastructure and network telemetry, predict network congestion using Random Forest machine learning models, detect multi-threshold anomalies, and generate instant visual & database alerts.

---

## 🎯 2. Problem Statement & Prototype Description

Telecom tower infrastructure requires 24/7 continuous health monitoring to prevent sudden power outages, hardware thermal failure, bandwidth congestion, and network disconnections.

During the current project evaluation phase prior to ESP32 hardware deployment:
- **Laptop Environment**: Acts as a **small-scale prototype network node and monitoring server**.
- **Real-Time Laptop Telemetry**: Collects actual host laptop network traffic, upload/download speeds, bandwidth usage %, Wi-Fi signal %, CPU %, RAM %, battery level, and temperature (where exposed by Windows ACPI/WMI).
- **Simulated Prototype Data**: Parameters that require physical IoT sensors (Power consumption, Battery voltage, Connected users, Tower load) are dynamically simulated with realistic physical trends and explicitly labeled as **SIMULATED PROTOTYPE DATA**.

> *Note: This project strictly represents a software-integrated prototype (~75% completion). It does NOT falsely claim that the host laptop is a physical cellular tower.*

---

## 🏗️ 3. System Architecture

```
                    INTERNET (Optional)
                            │
                            ▼
                LAPTOP NETWORK INTERFACE
                            │
            ┌───────────────┴───────────────┐
            ▼                               ▼
  REAL-TIME NETWORK DATA           MOBILE HOTSPOT DATA
  (psutil & netsh wlan)            (Shared Interface Data)
            │                               │
            └───────────────┬───────────────┘
                            ▼
                   SYSTEM HEALTH DATA
               (CPU, RAM, Battery, Temp)
                            │
                            ▼
                 PYTHON DATA COLLECTOR
                            │
                            ▼
                      FLASK API
                            │
                            ▼
                 SQLITE TIME-SERIES DB
                            │
            ┌───────────────┴───────────────┐
            ▼                               ▼
      ML PREDICTION                 ANOMALY DETECTION
 (Random Forest Forecast)      (Multi-Threshold + Disconnect)
            │                               │
            └───────────────┬───────────────┘
                            ▼
             REAL-TIME WEB DASHBOARD (100% Offline)
                            │
                            ▼
                     ALERT MANAGEMENT
```

---

## 📊 4. Real Data vs. Simulated Data Breakdown

| Monitored Parameter | Data Source | Label in Dashboard | Sensor Replacement in Final Phase |
| :--- | :--- | :--- | :--- |
| **Bytes Sent & Received** | Host Laptop (`psutil`) | Real-Time Laptop Data | ESP32 Network Gateway |
| **Upload / Download Speed** | Host Laptop (`psutil`) | Real-Time Laptop Data | Network Gateway Telemetry |
| **Bandwidth Utilization (%)** | Host Laptop Throughput Formula | Real-Time Laptop Data | Gateway Bandwidth Monitor |
| **Wi-Fi Signal Strength (%)** | Windows CLI (`netsh wlan`) | Real-Time Laptop Data | ESP32 Wi-Fi Telemetry |
| **Wi-Fi SSID & Quality** | Windows CLI (`netsh wlan`) | Real-Time Laptop Data | Cellular RSSI Sensor |
| **CPU & RAM Usage (%)** | Host Laptop (`psutil`) | Prototype Node System Health | ESP32 CPU/RAM Status |
| **Battery % & Charging** | Host Laptop (`psutil`) | Prototype Node System Health | Battery Management System |
| **Laptop Temperature (°C)** | Windows WMI / Demo Mode | Host / Demo Temperature | **DHT22 Temperature Sensor** |
| **Mobile Hotspot Traffic** | Windows Interface Traffic | Real-Time Laptop Data | Shared Tower Telemetry |
| **Tower Power Draw (W)** | Dynamic Trend Simulator | **SIMULATED PROTOTYPE DATA** | **INA219 Current/Power Sensor** |
| **Tower Battery Voltage (V)** | Dynamic Trend Simulator | **SIMULATED PROTOTYPE DATA** | **Voltage Divider Module** |
| **Connected Users Count** | Dynamic Trend Simulator | **SIMULATED PROTOTYPE DATA** | ESP32 Access Point Gateway |
| **Tower Load (%)** | Dynamic Trend Simulator | **SIMULATED PROTOTYPE DATA** | Tower Microcontroller |

---

## ⚡ 5. Features & Capabilities

1. **Real-Time Network & Health Collection**:
   - Collects live host network telemetry every 2 seconds.
   - Formats raw data dynamically into human-readable scales (B, KB, MB, GB, Mbps).
   - Monitors Windows Wi-Fi state, signal percentage (0-100%), and SSID.

2. **100% Local Offline Capability (Zero Internet/CDN Dependencies)**:
   - Flask web server runs locally on `http://127.0.0.1:5000`.
   - SQLite time-series database operates 100% offline.
   - Bundles local Chart.js library under `static/vendor/chart.min.js` so graphs render perfectly without Wi-Fi or internet.

3. **Network Disconnection & Auto-Recovery Engine**:
   - Automatically detects Wi-Fi disconnections without server or dashboard crashes.
   - Signal drops to 0%, status becomes `DISCONNECTED`, and emits `"CRITICAL: Network Connection Lost"`.
   - Upon reconnecting, automatically logs `"INFO: Network Connection Restored"` and resumes signal tracking.

4. **Random Forest Machine Learning Engine**:
   - Trained on 1,000 synthetic diurnal telecom records.
   - Predicts future network traffic (Mbps), calculates congestion risk %, classifies predicted status (`NORMAL`, `WARNING`, `CRITICAL`, `DISCONNECTED`), and outputs model confidence %.

5. **Multi-Threshold Anomaly Detection**:
   - **Bandwidth Utilization**: Warning (≥70%), Critical (≥90%).
   - **Wi-Fi Signal Strength**: Weak Warning (≤40%), Critical Signal Loss (≤20%), Disconnected (0%).
   - **Laptop Temperature**: Warning (≥60°C), Critical (≥80°C).
   - **Battery Voltage**: Warning (≤11.5V), Critical Depletion (≤10.8V).
   - **Power Consumption**: Warning (≥150W), Critical Surge (≥220W).
   - **Traffic Spike Detection**: Detects sudden throughput jumps (≥2.5x rolling average).

6. **Interactive Demonstration Control Panel**:
   - Instant scenario switcher buttons:
     - `🟢 Normal Operation`
     - `📈 High Network Traffic`
     - `⚠️ Network Congestion`
     - `📶 Weak Signal`
     - `🔥 High Temperature`
     - `⚡ Power Anomaly`
     - `❌ Network Disconnected`
     - `🔄 RETURN TO LIVE MONITORING`

---

## 💻 6. Installation & How to Run

### Prerequisites
- Windows 10 or 11
- Python 3.9, 3.10, 3.11, or 3.12 installed

### Step-by-Step Launch
1. Open PowerShell and navigate to the project directory:
   ```powershell
   cd C:\Users\mv240\.gemini\antigravity-ide\scratch\telecom_tower_monitoring
   ```

2. Activate the virtual environment:
   ```powershell
   .venv\Scripts\activate
   ```

3. Install required Python packages:
   ```powershell
   pip install -r requirements.txt
   ```

4. Launch the local application server:
   ```powershell
   python app.py
   ```

5. Open your web browser and navigate to:
   **`http://127.0.0.1:5000`**

---

## 🌐 7. How Offline Mode Works

- **Zero Cloud / CDN Dependencies**: All JS, CSS, and Chart rendering libraries are loaded locally from `static/vendor/chart.min.js`.
- **Offline Server**: Flask and SQLite run locally on `127.0.0.1`.
- **Wi-Fi Disconnect Test**: You can turn off Wi-Fi or disconnect from internet completely during evaluation; the dashboard, database, and telemetry loop will continue running seamlessly!

---

## 🎮 8. How Demo Mode Works (Tomorrow's Presentation Guide)

1. **Live Network Demonstration**:
   - Stream a video or download a file on your laptop. Watch the **Upload Speed**, **Download Speed**, and **Bandwidth Utilization** KPI cards and charts update live!

2. **Network Disconnection Demonstration**:
   - Turn OFF Wi-Fi on your laptop or click the **`❌ Network Disconnected`** demo button.
   - The status pill immediately turns grey with **`NETWORK DISCONNECTED`**, signal becomes `0%`, ML status prioritizes **`DISCONNECTED`**, and a critical alert `"CRITICAL: Network Connection Lost"` appears in the alerts feed!
   - Turn Wi-Fi back ON or click **`🔄 RETURN TO LIVE MONITORING`**; the system auto-recovers and emits `"INFO: Network Connection Restored"`.

3. **Anomaly & AI Forecast Demonstration**:
   - Click **`📈 High Network Traffic`**: Connected users and tower load rise.
   - Click **`⚠️ Network Congestion`**: Congestion risk jumps >90%, triggering a `CRITICAL` congestion alert.
   - Click **`🔥 High Temperature`**: Temperature surges above 80°C, triggering a `CRITICAL Overheating` alert.
   - Click **`⚡ Power Anomaly`**: Power draw surges to 245W and battery voltage drops to 10.3V, triggering power alerts.

---

## 🔮 9. Hardware Integration Roadmap (Remaining 25%)

The final 25% hardware phase will integrate physical sensors via ESP32 microcontrollers:
1. **ESP32 Microcontroller**: Edgenode collecting sensor telemetry and transmitting JSON payloads over HTTP/MQTT to Flask API.
2. **DHT22 Sensor**: Measures ambient temperature (°C) and humidity.
3. **INA219 I2C Sensor**: Measures DC current and power consumption (W).
4. **Voltage Divider Module**: Monitors 12V backup battery pack voltage levels in real-time.

---

## 📄 10. License & Credits
Developed for ECE Final-Year Engineering Curriculum.
