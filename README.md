# INTELLIGENT TELECOM TOWER MONITORING AND ALERT SYSTEM

> **ECE Final-Year Project Specifications & Implementation Manual**  
> *Real-Time Network Telemetry, Single Physical Temperature Sensor, 3-Algorithm Multi-Target AI Benchmark, and Offline System*

---

## 📌 1. System Overview

The **Intelligent Telecom Tower Monitoring and Alert System** is a production-grade software-hardware monitoring platform. It combines real-time network and system telemetry collection, ESP32 IoT temperature hardware integration, multi-target machine learning forecasting across 3 regressors (**Random Forest**, **Gradient Boosting**, **Extra Trees**), dynamic top-performer selection, and an offline web dashboard with real-time Chart.js visualizations.

---

## 🏗️ 2. Hardware vs. Software Telemetry Architecture

The system clearly separates physical hardware sensing from network/software telemetry:

```
┌─────────────────────────┐
│     HARDWARE LAYER      │
│  Temperature Sensor     │ (DHT22 / DS18B20 via ESP32 / Host Fallback)
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────┐
│                 SOFTWARE / NETWORK TELEMETRY                │
│  1. Traffic (MB)                                            │
│  2. Delay / Latency (ms)                                    │
│  3. Throughput (Mbps)                                       │
│  4. Propagation Time (ms) - Estimated from RTT/2            │
│  5. RAM Usage (%)                                           │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ▼
                    SQLITE TIME-SERIES DB
                             │
                             ▼
                   ONE COMMON REAL DATASET
                   (Same Chronological 80/20 Split)
                             │
            ┌────────────────┼────────────────┐
            ▼                ▼                ▼
     Random Forest   Gradient Boosting   Extra Trees
            │                │                │
            └────────────────┼────────────────┘
                             ▼
                 Multi-Output Evaluation
                  (MAE, RMSE, R² Metrics)
                             │
                             ▼
                Composite Performance Score
                 (Higher R², Lower MAE/RMSE)
                             │
                             ▼
                   Dynamic Winner Selection
                             │
                             ▼
                      ACTIVE MODEL
                             │
                             ▼
             Live 5-Parameter Multi-Target Predictions
```

> [!IMPORTANT]
> - **Only ONE Physical Hardware Sensor**: Temperature Sensor (DHT22/DS18B20 on ESP32 or Host Laptop Fallback). No unnecessary physical sensors (humidity, voltage, current, etc.) are included in the hardware layer.
> - **5 ML Telemetry Parameters**: Traffic, Delay, Throughput, Propagation Time, and RAM Usage are software/network parameters.
> - **Estimated Propagation Time**: Propagation time is calculated as `RTT / 2` (where RTT is measured round-trip ping delay in ms). It is an estimated network metric, not a direct physical layer measurement.

---

## 📊 3. Monitored Telemetry & Data Provenance

| Monitored Parameter | Category | Data Source / Method | Role in ML System |
| :--- | :--- | :--- | :--- |
| **Temperature (°C)** | Hardware Layer | ESP32 Temperature Sensor (or Host Fallback) | ML Input Feature / Live Display |
| **Traffic (MB)** | Software Telemetry | Host Laptop Network Interface (`psutil`) | Prediction Target #1 & ML Feature |
| **Delay (ms)** | Software Telemetry | Live ICMP Ping Latency Collector | Prediction Target #2 & ML Feature |
| **Throughput (Mbps)** | Software Telemetry | Real-Time Bandwidth Measurement | Prediction Target #3 & ML Feature |
| **Propagation Time (ms)** | Software Telemetry | Estimated from Measured Latency (`RTT / 2`) | Prediction Target #4 & ML Feature |
| **RAM Usage (%)** | Software Telemetry | System Health Monitor (`psutil`) | Prediction Target #5 & ML Feature |

---

## 🧠 4. Machine Learning & Algorithm Comparison Engine

### 4.1 Exactly 3 ML Regressors
1. **Random Forest** (`RandomForestRegressor(n_estimators=50, random_state=42)`)
2. **Gradient Boosting** (`MultiOutputRegressor(GradientBoostingRegressor(n_estimators=50, random_state=42))`)
3. **Extra Trees** (`ExtraTreesRegressor(n_estimators=50, random_state=42)`)

### 4.2 Single Common Real Telemetry Dataset
- All 3 algorithms train on the **exact same prepared dataset** queried from historical telemetry stored in SQLite (`tower_readings`).
- **No synthetic data** is used for production ML model comparison or evaluation. If SQLite records $< 50$, the system displays:
  > *"Insufficient live telemetry for reliable model training. Continue collecting telemetry before training."*
- **Train/Test Split**: Chronological 80% Training / 20% Testing split applied identically across all 3 models.

### 4.3 Multi-Output Prediction Architecture
Each algorithm simultaneously predicts all 5 target parameters:
$$\mathbf{Y} = [\text{Traffic}, \text{Delay}, \text{Throughput}, \text{Propagation Time}, \text{RAM Usage}]$$

### 4.4 Composite Performance Score
For each algorithm $m$, evaluation metrics (MAE, RMSE, $R^2$) are calculated across all 5 target parameters. Metrics are normalized into a documented 0 to 10 Composite Performance Score:

$$\text{Score}(m) = 10 \times \left(0.4 \times \max(0, R^2_{\text{avg}}) + 0.3 \times \frac{1}{1 + \text{MAE}_{\text{avg}}} + 0.3 \times \frac{1}{1 + \text{RMSE}_{\text{avg}}}\right)$$

- **Dynamic Winner Selection**: The algorithm with the highest composite score is dynamically determined and designated as the **ACTIVE MODEL**. No hard-coded winners.
- **Automatic Prediction Engine Switching**: The prediction engine automatically switches to the ACTIVE MODEL to generate live 5-parameter forecasts displayed on the dashboard.

---

## ⚡ 5. Dashboard Visualizations & Features

1. **Hardware Temperature Card**: Displays live Temperature Sensor reading (e.g. `28.4 °C`) from ESP32 or fallback.
2. **Live Telemetry KPI Cards**: Real-time Traffic, Delay (ms), Throughput (Mbps), Propagation Time (ms), and RAM Usage (%).
3. **Live ML Predictions Dashboard**: Real-time predictions for all 5 parameters from the selected ACTIVE MODEL.
4. **Overall 3-Algorithm Comparison Graph**: Bar chart comparing composite performance scores for Random Forest, Gradient Boosting, and Extra Trees.
5. **Top-Performer Card**: Displays winning model name dynamically with composite score and `● ACTIVE` status badge.
6. **Detailed Model Performance Table**: Tables MAE, RMSE, $R^2$, overall score, and status (`ACTIVE` vs `Evaluated`) for every model and target.
7. **5 Separate Parameter Comparison Line Graphs**:
   - **Graph 1 — Traffic**: Actual vs RF vs GB vs ET
   - **Graph 2 — Delay**: Actual vs RF vs GB vs ET
   - **Graph 3 — Throughput**: Actual vs RF vs GB vs ET
   - **Graph 4 — Propagation Time**: Actual vs RF vs GB vs ET
   - **Graph 5 — RAM Usage**: Actual vs RF vs GB vs ET
8. **Retrain Models Button**: Triggers instant on-demand retraining, re-evaluation, winner selection, and active model switching.

---

## 🔌 6. REST API Reference

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/api/latest` | `GET` | Returns full latest telemetry snapshot (5 parameters + Hardware Temperature) |
| `/api/history` | `GET` | Returns time-series points for Chart.js rendering |
| `/api/model-comparison` | `GET` | Returns 3-algorithm benchmark, overall scores, dynamic winner, and parameter comparison series |
| `/api/ml/retrain` | `POST`/`GET` | Triggers 3-model retraining on SQLite history and updates active winning model |
| `/api/prediction` | `GET` | Returns live 5-parameter predictions from active model |
| `/api/esp32/telemetry` | `POST` | Ingests ESP32 Temperature Sensor readings and returns actuator flags |
| `/api/demo-mode` | `POST` | Switches interactive test scenario |

---

## 💻 7. Installation & How to Run

### Step-by-Step Launch
1. Open PowerShell and navigate to the project root:
   ```powershell
   cd C:\Users\mv240\.gemini\antigravity-ide\scratch\Intelligent-Tower-Monitoring-System
   ```
2. Activate virtual environment:
   ```powershell
   .venv\Scripts\activate
   ```
3. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```
4. Run verification and test suite:
   ```powershell
   python test_comparison.py
   python verify_final.py
   ```
5. Launch local application server:
   ```powershell
   python app.py
   ```
6. Open dashboard in browser:
   **`http://127.0.0.1:5000`**

---

## 📄 8. Credits & Project Metadata
Developed for ECE Final-Year Engineering Curriculum.
