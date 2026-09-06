# INTELLIGENT TELECOM TOWER MONITORING AND ALERT SYSTEM

> **ECE Final-Year Project Prototype (Approx. 75% Completion)**  
> *Software-Integrated Prototype with Real-Time Laptop Data Acquisition & Simulated IoT Sensor Telemetry*

---

## 📌 Project Overview

The **Intelligent Telecom Tower Monitoring and Alert System** is a software-hardware integrated framework designed to continuously monitor telecom tower health and network performance, predict network congestion using machine learning, detect abnormal hardware and environment conditions, and trigger instant visual alerts.

---

## ⚠️ Important Presentation Context (75% Prototype Status)

This software application represents **approximately 75% completion** of the full final-year project.

- **Real-Time Data Source (Laptop Host)**:
  - **Network Traffic**: Bytes sent, bytes received, upload speed, download speed, and total traffic via Python `psutil`.
  - **Bandwidth Utilization (%)**: Derived from live host throughput vs configured maximum network bandwidth.
  - **Wi-Fi Signal Strength (%)**: Captured dynamically from Windows `netsh wlan show interfaces`.

- **Simulated Hardware Parameters (To Be Replaced by ESP32)**:
  - **Temperature (°C)**
  - **Power Consumption (W)**
  - **Battery Voltage (V)**
  - **Connected Users & Tower Load (%)**

> *Note: Physical IoT sensors (ESP32 + DHT22 + INA219 + Voltage Sensor) will replace the currently simulated tower parameters during the final 25% hardware integration phase.*

---

## 🏗️ System Architecture

```
Laptop Network Telemetry (psutil & netsh)  +  Simulated ESP32 Sensors
                                 │
                                 ▼
                     Python Data Collector Engine
                                 │
                                 ▼
                          Flask REST API
                                 │
                                 ▼
                     SQLite Time-Series Database
                                 │
                                 ▼
                Machine Learning & Anomaly Engine
           (Random Forest Forecast + Rule-Based Rules)
                                 │
                                 ▼
                 Real-Time Web Monitoring Dashboard
               (Chart.js + Dynamic Demo Scenario Switcher)
```

---

## 🚀 Key Features

1. **Real-Time Telemetry Collection**:
   - Collects live network data from host laptop every 2 seconds.
   - Extracts exact Wi-Fi signal percentage using Windows Native CLI (`netsh`).

2. **Realistic Sensor Simulation & Trends**:
   - Generates realistic, non-random physical sensor trends.
   - Temperature smoothly scales with tower load; power draw dynamically tracks load; battery voltage demonstrates realistic float charging/discharging.

3. **Machine Learning Traffic & Congestion Predictor**:
   - Random Forest Regressor & Classifier trained on synthetic historical diurnal tower data.
   - Predicts future network traffic (Mbps), calculates congestion risk percentage, classifies tower status (`NORMAL`, `WARNING`, `CRITICAL`), and computes prediction confidence.

4. **Multi-Threshold Anomaly Detection Engine**:
   - **Temperature**: Warning (>40°C), Critical (>50°C).
   - **Battery Voltage**: Warning (<11.5V), Critical (<10.8V).
   - **Bandwidth Usage**: Warning (>70%), Critical (>90%).
   - **Wi-Fi Signal**: Warning (<40%), Critical (<20%).
   - **Power Draw**: Warning (>150W), Critical (>220W).
   - **Statistical Traffic Spike Detection**: Detects sudden throughput jumps (>2.5x rolling average).

5. **Interactive Demonstration Mode**:
   - Instant scenario switcher buttons on dashboard:
     - `Normal Operation`
     - `High Traffic`
     - `Network Congestion`
     - `Weak Signal`
     - `Thermal Overheat`
     - `Power Failure`

---

## 💻 Installation & Run Guide

### 1. Prerequisites
- Python 3.9+ installed on Windows

### 2. Clone & Setup Workspace
```bash
git clone https://github.com/monishav24/Intelligent-Tower-Monitoring-System.git
cd Intelligent-Tower-Monitoring-System
```

### 3. Create & Activate Virtual Environment
```bash
python -m venv .venv
.venv\Scripts\activate
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. Launch Application
```bash
python app.py
```

### 6. Open Web Dashboard
Navigate to `http://127.0.0.1:5000` in your web browser.

---

## 🎯 How to Demonstrate Tomorrow (Evaluator Walkthrough)

1. **Header & Data Source Disclaimer**:
   - Point out the header banner explicitly clarifying that real network data is collected from your laptop, while tower physical sensors are currently simulated.

2. **Real Laptop Telemetry**:
   - Open a browser tab and download/stream a file or load a video.
   - Watch the **Upload Speed**, **Download Speed**, and **Bandwidth Utilization** KPI cards and charts update live on the dashboard!

3. **Demonstrating AI Traffic Prediction**:
   - Show the **AI Traffic Forecast & Congestion Engine** card. Point out the predicted traffic (Mbps), Congestion Risk %, predicted status, and RF Confidence Score.

4. **Demonstrating Anomaly Detection (Demo Mode Scenarios)**:
   - Click **`High Traffic`**: Observe connected users increase, tower load rise, and bandwidth usage grow.
   - Click **`Network Congestion`**: Watch Congestion Risk jump to >90% and trigger a `CRITICAL` alert badge!
   - Click **`Weak Signal`**: Watch Wi-Fi signal drop to ~18% and trigger a `Weak Signal Warning`.
   - Click **`Thermal Overheat`**: Temperature surges to ~56°C, triggering a `CRITICAL Thermal Overheating` alert!
   - Click **`Power Failure`**: Battery voltage drops below 10.8V, triggering a `CRITICAL Power Failure` alert!
   - Click **`Normal Operation`**: Everything smoothly recovers back to normal.

---

## 🔮 Hardware Integration Roadmap (Remaining 25%)

The final hardware phase will integrate physical sensors via ESP32 Wi-Fi/MQTT telemetry:

1. **ESP32 Microcontroller**: Serves as the edge node collecting sensor data and transmitting JSON payloads over HTTP/MQTT to Flask API.
2. **DHT22 Sensor**: Measures ambient and cabinet temperature (°C) & humidity.
3. **INA219 I2C Sensor**: Measures DC current and power consumption (W) of the tower power system.
4. **Voltage Divider Module**: Monitors 12V backup battery pack voltage levels in real-time.

---

## 📄 License
Project developed for ECE Final-Year Engineering Curriculum.