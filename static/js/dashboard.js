/**
 * Intelligent Telecom Tower Monitoring Dashboard JavaScript
 * Real-time polling, Chart.js telemetry visualization, AI prediction, and Demo Mode interactions.
 */

// Global Chart Instances
let chartSpeeds, chartBandwidth, chartSignal, chartTemp, chartPower, chartLoad;

// Max data points shown in live sliding window
const MAX_HISTORICAL_POINTS = 25;

document.addEventListener('DOMContentLoaded', () => {
    initClock();
    initCharts();
    fetchTelemetryData();
    
    // Poll API every 2 seconds
    setInterval(fetchTelemetryData, 2000);
});

/**
 * Initialize live digital header clock.
 */
function initClock() {
    const clockEl = document.getElementById('live-clock');
    const updateTime = () => {
        const now = new Date();
        clockEl.textContent = now.toLocaleTimeString();
    };
    updateTime();
    setInterval(updateTime, 1000);
}

/**
 * Configure Chart.js global defaults and initialize 6 telemetry charts.
 */
function initCharts() {
    Chart.defaults.color = '#94a3b8';
    Chart.defaults.borderColor = 'rgba(255, 255, 255, 0.06)';
    Chart.defaults.font.family = 'Outfit, sans-serif';

    const commonOptions = {
        responsive: true,
        maintainAspectRatio: false,
        animation: { duration: 400 },
        plugins: {
            legend: { position: 'top', labels: { boxWidth: 12, padding: 10 } },
            tooltip: { mode: 'index', intersect: false }
        },
        scales: {
            x: { grid: { display: false }, ticks: { maxRotation: 0, autoSkip: true, maxTicksLimit: 6 } },
            y: { grid: { color: 'rgba(255, 255, 255, 0.05)' } }
        }
    };

    // 1. Speeds Chart (Upload & Download)
    const ctxSpeeds = document.getElementById('chart-speeds').getContext('2d');
    chartSpeeds = new Chart(ctxSpeeds, {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                {
                    label: 'Upload (KB/s)',
                    data: [],
                    borderColor: '#10b981',
                    backgroundColor: 'rgba(16, 185, 129, 0.1)',
                    fill: true,
                    tension: 0.3
                },
                {
                    label: 'Download (KB/s)',
                    data: [],
                    borderColor: '#06b6d4',
                    backgroundColor: 'rgba(6, 182, 212, 0.1)',
                    fill: true,
                    tension: 0.3
                }
            ]
        },
        options: commonOptions
    });

    // 2. Bandwidth Utilization Chart
    const ctxBw = document.getElementById('chart-bandwidth').getContext('2d');
    chartBandwidth = new Chart(ctxBw, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Usage (%)',
                data: [],
                borderColor: '#8b5cf6',
                backgroundColor: 'rgba(139, 92, 246, 0.15)',
                fill: true,
                tension: 0.3
            }]
        },
        options: {
            ...commonOptions,
            scales: { ...commonOptions.scales, y: { min: 0, max: 100 } }
        }
    });

    // 3. Wi-Fi Signal Strength Chart
    const ctxSignal = document.getElementById('chart-signal').getContext('2d');
    chartSignal = new Chart(ctxSignal, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Signal (%)',
                data: [],
                borderColor: '#f97316',
                backgroundColor: 'rgba(249, 115, 22, 0.15)',
                fill: true,
                tension: 0.3
            }]
        },
        options: {
            ...commonOptions,
            scales: { ...commonOptions.scales, y: { min: 0, max: 100 } }
        }
    });

    // 4. Temperature Chart
    const ctxTemp = document.getElementById('chart-temp').getContext('2d');
    chartTemp = new Chart(ctxTemp, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Temp (°C)',
                data: [],
                borderColor: '#ef4444',
                backgroundColor: 'rgba(239, 68, 68, 0.15)',
                fill: true,
                tension: 0.3
            }]
        },
        options: {
            ...commonOptions,
            scales: { ...commonOptions.scales, y: { min: 20, max: 70 } }
        }
    });

    // 5. Power & Battery Chart
    const ctxPower = document.getElementById('chart-power').getContext('2d');
    chartPower = new Chart(ctxPower, {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                {
                    label: 'Power Draw (W)',
                    data: [],
                    borderColor: '#eab308',
                    yAxisID: 'yPower',
                    tension: 0.3
                },
                {
                    label: 'Battery (V)',
                    data: [],
                    borderColor: '#14b8a6',
                    yAxisID: 'yBattery',
                    tension: 0.3
                }
            ]
        },
        options: {
            ...commonOptions,
            scales: {
                x: commonOptions.scales.x,
                yPower: { type: 'linear', position: 'left', title: { display: true, text: 'Watts' } },
                yBattery: { type: 'linear', position: 'right', title: { display: true, text: 'Volts' }, min: 9, max: 14 }
            }
        }
    });

    // 6. Tower Load & Connected Users Chart
    const ctxLoad = document.getElementById('chart-load').getContext('2d');
    chartLoad = new Chart(ctxLoad, {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                {
                    label: 'Tower Load (%)',
                    data: [],
                    borderColor: '#ec4899',
                    yAxisID: 'yLoad',
                    tension: 0.3
                },
                {
                    label: 'Users',
                    data: [],
                    borderColor: '#6366f1',
                    yAxisID: 'yUsers',
                    tension: 0.3
                }
            ]
        },
        options: {
            ...commonOptions,
            scales: {
                x: commonOptions.scales.x,
                yLoad: { type: 'linear', position: 'left', min: 0, max: 100 },
                yUsers: { type: 'linear', position: 'right', min: 0 }
            }
        }
    });
}

/**
 * Fetch latest telemetry reading & historical data from Flask API.
 */
async function fetchTelemetryData() {
    try {
        const [resLatest, resHistory] = await Promise.all([
            fetch('/api/latest').then(r => r.json()),
            fetch(`/api/history?limit=${MAX_HISTORICAL_POINTS}`).then(r => r.json())
        ]);

        if (resLatest.status === 'success' && resLatest.data) {
            updateDashboardCards(resLatest.data, resLatest.demo_scenario);
            updateAlertsFeed(resLatest.recent_alerts);
        }

        if (resHistory.status === 'success' && resHistory.data) {
            updateCharts(resHistory.data);
        }

    } catch (err) {
        console.error('Error fetching telemetry:', err);
    }
}

/**
 * Update 10 KPI metric cards, status pill, and AI prediction panel.
 */
function updateDashboardCards(data, demoScenario) {
    // KPI Updates
    document.getElementById('kpi-total-traffic').textContent = `${data.total_traffic_mb.toFixed(1)} MB`;
    document.getElementById('kpi-upload-speed').textContent = `${data.upload_speed.toFixed(1)} KB/s`;
    document.getElementById('kpi-download-speed').textContent = `${data.download_speed.toFixed(1)} KB/s`;
    document.getElementById('kpi-bandwidth').textContent = `${data.bandwidth_utilization.toFixed(1)} %`;
    document.getElementById('kpi-signal').textContent = `${Math.round(data.signal_strength)} %`;
    document.getElementById('kpi-temperature').textContent = `${data.temperature.toFixed(1)} °C`;
    document.getElementById('kpi-power').textContent = `${data.power_consumption.toFixed(1)} W`;
    document.getElementById('kpi-battery').textContent = `${data.battery_voltage.toFixed(2)} V`;
    document.getElementById('kpi-users').textContent = data.connected_users;
    document.getElementById('kpi-load').textContent = `${data.tower_load.toFixed(1)} %`;

    // Global Status Pill
    const pill = document.getElementById('global-status-pill');
    const pillText = document.getElementById('global-status-text');
    pill.className = 'status-pill';

    if (data.tower_status === 'CRITICAL') {
        pill.classList.add('critical');
        pillText.textContent = 'SYSTEM CRITICAL';
    } else if (data.tower_status === 'WARNING') {
        pill.classList.add('warning');
        pillText.textContent = 'SYSTEM WARNING';
    } else {
        pillText.textContent = 'SYSTEM NORMAL';
    }

    // AI Prediction Panel Updates
    document.getElementById('ai-pred-traffic').textContent = `${data.predicted_traffic.toFixed(2)} Mbps`;
    
    const riskPct = Math.min(Math.max(data.congestion_risk, 0), 100);
    const riskBar = document.getElementById('ai-risk-bar');
    const riskVal = document.getElementById('ai-risk-val');
    const riskLvl = document.getElementById('ai-risk-level');
    
    riskBar.style.width = `${riskPct}%`;
    riskVal.textContent = `${riskPct.toFixed(1)}%`;

    if (riskPct >= 80) {
        riskLvl.textContent = 'CRITICAL CONGESTION RISK';
        riskLvl.className = 'status-crit';
    } else if (riskPct >= 50) {
        riskLvl.textContent = 'HIGH CONGESTION RISK';
        riskLvl.className = 'status-warn';
    } else {
        riskLvl.textContent = 'LOW CONGESTION RISK';
        riskLvl.className = 'status-norm';
    }

    const predStatusEl = document.getElementById('ai-pred-status');
    predStatusEl.textContent = data.predicted_status;
    predStatusEl.className = data.predicted_status === 'CRITICAL' ? 'status-crit' : 
                            (data.predicted_status === 'WARNING' ? 'status-warn' : 'status-norm');

    // Update active scenario badge if changed
    document.getElementById('active-scenario-name').textContent = demoScenario || 'NORMAL';
}

/**
 * Update active alerts feed log.
 */
function updateAlertsFeed(alerts) {
    const listEl = document.getElementById('alerts-list');
    const countBadge = document.getElementById('alerts-count');

    if (!alerts || alerts.length === 0) {
        countBadge.textContent = '0 Alerts';
        listEl.innerHTML = `
            <div class="no-alerts-msg">
                <i class="fa-solid fa-shield-halved"></i>
                <p>No active anomalies detected. System operating within normal thresholds.</p>
            </div>
        `;
        return;
    }

    countBadge.textContent = `${alerts.length} Active`;
    listEl.innerHTML = alerts.map(a => `
        <div class="alert-item ${a.severity}">
            <div>
                <strong style="color: ${a.severity === 'CRITICAL' ? '#ef4444' : '#eab308'}">[${a.severity}]</strong>
                <span class="alert-msg">${a.message}</span>
            </div>
            <span class="alert-time">${a.timestamp.split(' ')[1] || a.timestamp}</span>
        </div>
    `).join('');
}

/**
 * Push historical data series to Chart.js instances.
 */
function updateCharts(history) {
    const labels = history.map(h => h.timestamp ? h.timestamp.split(' ')[1] : '');

    // Speeds
    chartSpeeds.data.labels = labels;
    chartSpeeds.data.datasets[0].data = history.map(h => h.upload_speed);
    chartSpeeds.data.datasets[1].data = history.map(h => h.download_speed);
    chartSpeeds.update();

    // Bandwidth
    chartBandwidth.data.labels = labels;
    chartBandwidth.data.datasets[0].data = history.map(h => h.bandwidth_utilization);
    chartBandwidth.update();

    // Signal
    chartSignal.data.labels = labels;
    chartSignal.data.datasets[0].data = history.map(h => h.signal_strength);
    chartSignal.update();

    // Temp
    chartTemp.data.labels = labels;
    chartTemp.data.datasets[0].data = history.map(h => h.temperature);
    chartTemp.update();

    // Power & Battery
    chartPower.data.labels = labels;
    chartPower.data.datasets[0].data = history.map(h => h.power_consumption);
    chartPower.data.datasets[1].data = history.map(h => h.battery_voltage);
    chartPower.update();

    // Load & Users
    chartLoad.data.labels = labels;
    chartLoad.data.datasets[0].data = history.map(h => h.tower_load);
    chartLoad.data.datasets[1].data = history.map(h => h.connected_users);
    chartLoad.update();
}

/**
 * Trigger Demo Mode Scenario via POST request.
 */
async function triggerDemoScenario(scenario) {
    try {
        const buttons = document.querySelectorAll('.btn-demo');
        buttons.forEach(btn => btn.classList.remove('active'));

        // Find clicked button and activate
        event.currentTarget.classList.add('active');

        const res = await fetch('/api/demo-mode', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ scenario })
        });
        
        const data = await res.json();
        if (data.status === 'success') {
            document.getElementById('active-scenario-name').textContent = scenario;
            // Immediate refresh
            fetchTelemetryData();
        }
    } catch (err) {
        console.error('Failed to set demo scenario:', err);
    }
}
