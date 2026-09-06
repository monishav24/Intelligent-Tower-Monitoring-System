/**
 * Intelligent Telecom Tower Monitoring Dashboard JavaScript
 * 100% Offline-First Execution, Real-Time Polling, Local Chart.js Graphs & Demo Mode Controls
 */

let chartSpeeds, chartBandwidth, chartSignal, chartSys, chartTemp, chartLoad, chartPower, chartTraffic;

const MAX_HISTORY_POINTS = 25;

document.addEventListener('DOMContentLoaded', () => {
    startClock();
    initOfflineCharts();
    fetchTelemetry();
    
    // Poll local REST API every 2 seconds
    setInterval(fetchTelemetry, 2000);
});

/**
 * Header digital clock ticker.
 */
function startClock() {
    const clockEl = document.getElementById('live-clock');
    const update = () => {
        const now = new Date();
        clockEl.textContent = now.toLocaleTimeString();
    };
    update();
    setInterval(update, 1000);
}

/**
 * Initialize 8 Chart.js multi-series graphs using local vendor library.
 */
function initOfflineCharts() {
    Chart.defaults.color = '#94a3b8';
    Chart.defaults.borderColor = 'rgba(255, 255, 255, 0.05)';
    Chart.defaults.font.family = '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';

    const commonOpts = {
        responsive: true,
        maintainAspectRatio: false,
        animation: { duration: 300 },
        plugins: {
            legend: { position: 'top', labels: { boxWidth: 10, padding: 8 } },
            tooltip: { mode: 'index', intersect: false }
        },
        scales: {
            x: { grid: { display: false }, ticks: { maxRotation: 0, autoSkip: true, maxTicksLimit: 6 } },
            y: { grid: { color: 'rgba(255, 255, 255, 0.05)' } }
        }
    };

    // 1. Speeds
    chartSpeeds = new Chart(document.getElementById('chart-speeds').getContext('2d'), {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                { label: 'Upload (KB/s)', data: [], borderColor: '#10b981', tension: 0.3, fill: true, backgroundColor: 'rgba(16, 185, 129, 0.1)' },
                { label: 'Download (KB/s)', data: [], borderColor: '#06b6d4', tension: 0.3, fill: true, backgroundColor: 'rgba(6, 182, 212, 0.1)' }
            ]
        },
        options: commonOpts
    });

    // 2. Bandwidth
    chartBandwidth = new Chart(document.getElementById('chart-bandwidth').getContext('2d'), {
        type: 'line',
        data: {
            labels: [],
            datasets: [{ label: 'Bandwidth Usage (%)', data: [], borderColor: '#8b5cf6', tension: 0.3, fill: true, backgroundColor: 'rgba(139, 92, 246, 0.15)' }]
        },
        options: { ...commonOpts, scales: { ...commonOpts.scales, y: { min: 0, max: 100 } } }
    });

    // 3. Signal
    chartSignal = new Chart(document.getElementById('chart-signal').getContext('2d'), {
        type: 'line',
        data: {
            labels: [],
            datasets: [{ label: 'Wi-Fi Signal (%)', data: [], borderColor: '#f97316', tension: 0.3, fill: true, backgroundColor: 'rgba(249, 115, 22, 0.15)' }]
        },
        options: { ...commonOpts, scales: { ...commonOpts.scales, y: { min: 0, max: 100 } } }
    });

    // 4. System CPU & RAM
    chartSys = new Chart(document.getElementById('chart-sys').getContext('2d'), {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                { label: 'CPU Usage (%)', data: [], borderColor: '#3b82f6', tension: 0.3 },
                { label: 'RAM Usage (%)', data: [], borderColor: '#ec4899', tension: 0.3 }
            ]
        },
        options: { ...commonOpts, scales: { ...commonOpts.scales, y: { min: 0, max: 100 } } }
    });

    // 5. Load & Hotspot Devices
    chartLoad = new Chart(document.getElementById('chart-load').getContext('2d'), {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                { label: 'Tower Load (%)', data: [], borderColor: '#eab308', yAxisID: 'yLoad', tension: 0.3 },
                { label: 'Hotspot Devices', data: [], borderColor: '#6366f1', yAxisID: 'yUsers', tension: 0.3 }
            ]
        },
        options: {
            ...commonOpts,
            scales: {
                x: commonOpts.scales.x,
                yLoad: { type: 'linear', position: 'left', min: 0, max: 100 },
                yUsers: { type: 'linear', position: 'right', min: 0 }
            }
        }
    });

    // 6. Temperature
    chartTemp = new Chart(document.getElementById('chart-temp').getContext('2d'), {
        type: 'line',
        data: {
            labels: [],
            datasets: [{ label: 'Temperature (°C)', data: [], borderColor: '#ef4444', tension: 0.3, fill: true, backgroundColor: 'rgba(239, 68, 68, 0.15)' }]
        },
        options: { ...commonOpts, scales: { ...commonOpts.scales, y: { min: 20, max: 100 } } }
    });

    // 7. Power & Battery Voltage
    chartPower = new Chart(document.getElementById('chart-power').getContext('2d'), {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                { label: 'Power Draw (W)', data: [], borderColor: '#14b8a6', yAxisID: 'yPower', tension: 0.3 },
                { label: 'Battery (V)', data: [], borderColor: '#8b5cf6', yAxisID: 'yBattery', tension: 0.3 }
            ]
        },
        options: {
            ...commonOpts,
            scales: {
                x: commonOpts.scales.x,
                yPower: { type: 'linear', position: 'left' },
                yBattery: { type: 'linear', position: 'right', min: 9, max: 14 }
            }
        }
    });

    // 8. Traffic Accumulation
    chartTraffic = new Chart(document.getElementById('chart-traffic').getContext('2d'), {
        type: 'line',
        data: {
            labels: [],
            datasets: [{ label: 'Total Traffic (MB)', data: [], borderColor: '#06b6d4', tension: 0.3, fill: true, backgroundColor: 'rgba(6, 182, 212, 0.15)' }]
        },
        options: commonOpts
    });
}

/**
 * Fetch data from local Flask API endpoints.
 */
async function fetchTelemetry() {
    try {
        const [resLatest, resHist] = await Promise.all([
            fetch('/api/latest').then(r => r.json()),
            fetch(`/api/history?limit=${MAX_HISTORY_POINTS}`).then(r => r.json())
        ]);

        if (resLatest.status === 'success' && resLatest.data) {
            updateKpiCards(resLatest.data);
            updateAlertsFeed(resLatest.recent_alerts);
        }

        if (resHist.status === 'success' && resHist.data) {
            updateCharts(resHist.data);
        }
    } catch (err) {
        console.error('Telemetry fetch error:', err);
    }
}

/**
 * Update Tri-Status Bar, 14 KPI cards, AI panel, and hotspot client IP panel.
 */
function updateKpiCards(data) {
    // 1. TRI-STATUS CONNECTIVITY BAR
    const netStatus = data.internet_status || 'ONLINE';
    const netBadge = document.getElementById('status-internet');
    netBadge.textContent = netStatus;
    netBadge.className = netStatus === 'ONLINE' ? 'status-badge online' : 'status-badge offline';

    document.getElementById('status-local').textContent = 'ACTIVE';

    const hotspotBadge = document.getElementById('status-hotspot');
    const hotspotState = data.hotspot_status || 'ACTIVE';
    hotspotBadge.textContent = hotspotState;
    hotspotBadge.className = hotspotState === 'ACTIVE' ? 'status-badge active' : 'status-badge inactive';

    const overallBadge = document.getElementById('status-overall');
    const overallState = data.overall_status || 'NORMAL';
    overallBadge.textContent = overallState;
    overallBadge.className = overallState === 'DISCONNECTED' ? 'status-badge disconnected' :
                            (overallState === 'CRITICAL' ? 'status-badge critical' :
                            (overallState === 'WARNING' ? 'status-badge warning' : 'status-badge normal'));

    // Speeds & Traffic
    document.getElementById('kpi-upload').textContent = `${data.upload_speed.toFixed(1)} KB/s`;
    document.getElementById('kpi-download').textContent = `${data.download_speed.toFixed(1)} KB/s`;
    document.getElementById('kpi-total-traffic').textContent = formatBytes(data.total_network_traffic * 1024 * 1024);
    document.getElementById('kpi-bandwidth').textContent = `${data.bandwidth_utilization.toFixed(1)} %`;
    document.getElementById('kpi-signal').textContent = `${Math.round(data.signal_strength)} %`;
    document.getElementById('kpi-ssid').textContent = data.ssid || 'N/A';
    
    // Network status text
    const netQualityEl = document.getElementById('kpi-net-status');
    if (data.wifi_status === 'DISCONNECTED' || data.signal_strength === 0) {
        netQualityEl.textContent = 'DISCONNECTED';
        netQualityEl.style.color = '#ef4444';
    } else {
        netQualityEl.textContent = data.signal_strength >= 80 ? 'EXCELLENT' : (data.signal_strength >= 60 ? 'GOOD' : 'WEAK');
        netQualityEl.style.color = '#10b981';
    }

    // CONNECTED HOTSPOT DEVICES (REAL-TIME ARP DETECTED)
    const clientCount = data.connected_client_count || 0;
    document.getElementById('kpi-hotspot-clients').textContent = `${clientCount} device${clientCount !== 1 ? 's' : ''}`;
    document.getElementById('hotspot-device-count').textContent = `${clientCount} Device${clientCount !== 1 ? 's' : ''}`;
    document.getElementById('hotspot-state-text').textContent = hotspotState;

    // Render detected client IP list
    const clientIpFeed = document.getElementById('client-ip-list');
    const clientList = data.client_ip_list || [];
    if (clientList.length > 0) {
        clientIpFeed.innerHTML = clientList.map(ip => `
            <div class="client-ip-chip">
                <span>🌐 ${ip}</span>
                <span>CONNECTED</span>
            </div>
        `).join('');
    } else {
        clientIpFeed.innerHTML = `<div class="no-clients">No client devices currently attached.</div>`;
    }

    // System Health
    document.getElementById('kpi-cpu').textContent = `${data.cpu_usage.toFixed(1)} %`;
    document.getElementById('kpi-ram').textContent = `${data.ram_usage.toFixed(1)} %`;
    document.getElementById('kpi-battery-pct').textContent = data.battery_percentage !== null ? `${data.battery_percentage}%` : 'N/A';
    document.getElementById('kpi-battery-status').textContent = data.battery_status || 'AC Power';

    const tempEl = document.getElementById('kpi-temp');
    const tempSourceEl = document.getElementById('kpi-temp-source');
    if (data.system_temperature !== null) {
        tempEl.textContent = `${data.system_temperature.toFixed(1)} °C`;
        tempSourceEl.textContent = data.temperature_source.includes('REAL') ? 'REAL Laptop' : 'Simulated / Demo';
    } else {
        tempEl.textContent = 'Sensor Unavailable';
        tempSourceEl.textContent = 'OS Unexposed';
    }

    // Simulated Tower
    document.getElementById('kpi-power').textContent = `${data.power_consumption.toFixed(1)} W`;
    document.getElementById('kpi-battery-v').textContent = `${data.battery_voltage.toFixed(2)} V`;
    document.getElementById('kpi-load').textContent = `${data.tower_load.toFixed(1)} %`;

    // AI Prediction Panel
    document.getElementById('ai-pred-traffic').textContent = `${data.predicted_network_traffic.toFixed(2)} Mbps`;
    
    const riskPct = Math.min(Math.max(data.congestion_risk, 0), 100);
    document.getElementById('ai-risk-fill').style.width = `${riskPct}%`;
    document.getElementById('ai-risk-pct').textContent = `${riskPct.toFixed(1)}%`;

    const riskStatusEl = document.getElementById('ai-risk-status');
    if (riskPct >= 80) {
        riskStatusEl.textContent = 'CRITICAL CONGESTION RISK';
        riskStatusEl.className = 'status-crit';
    } else if (riskPct >= 50) {
        riskStatusEl.textContent = 'HIGH CONGESTION RISK';
        riskStatusEl.className = 'status-warn';
    } else {
        riskStatusEl.textContent = 'LOW RISK';
        riskStatusEl.className = 'status-norm';
    }

    const predStatusEl = document.getElementById('ai-pred-status');
    predStatusEl.textContent = data.predicted_status;
    predStatusEl.className = data.predicted_status === 'DISCONNECTED' ? 'status-disc' : 
                            (data.predicted_status === 'CRITICAL' ? 'status-crit' : 
                            (data.predicted_status === 'WARNING' ? 'status-warn' : 'status-norm'));

    // Active scenario tag
    document.getElementById('active-scenario-name').textContent = data.demo_scenario || 'NORMAL OPERATION';
}

/**
 * Format bytes into human readable scales.
 */
function formatBytes(bytes) {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
    return `${(bytes / (1024 * 1024 * 1024)).toFixed(2)} GB`;
}

/**
 * Render active alerts feed.
 */
function updateAlertsFeed(alerts) {
    const feedEl = document.getElementById('alerts-feed');
    const badgeEl = document.getElementById('alerts-count');

    if (!alerts || alerts.length === 0) {
        badgeEl.textContent = '0 Alerts';
        feedEl.innerHTML = `
            <div class="empty-alerts">
                <p>✅ All monitored parameters operating within normal thresholds.</p>
            </div>
        `;
        return;
    }

    badgeEl.textContent = `${alerts.length} Active`;
    feedEl.innerHTML = alerts.map(a => `
        <div class="alert-card ${a.severity}">
            <div>
                <strong>[${a.severity}]</strong> ${a.message}
            </div>
            <span>${a.timestamp.split(' ')[1] || a.timestamp}</span>
        </div>
    `).join('');
}

/**
 * Push historical data series to 8 Chart.js instances.
 */
function updateCharts(history) {
    const labels = history.map(h => h.timestamp ? h.timestamp.split(' ')[1] : '');

    // 1. Speeds
    chartSpeeds.data.labels = labels;
    chartSpeeds.data.datasets[0].data = history.map(h => h.upload_speed);
    chartSpeeds.data.datasets[1].data = history.map(h => h.download_speed);
    chartSpeeds.update();

    // 2. Bandwidth
    chartBandwidth.data.labels = labels;
    chartBandwidth.data.datasets[0].data = history.map(h => h.bandwidth_utilization);
    chartBandwidth.update();

    // 3. Signal
    chartSignal.data.labels = labels;
    chartSignal.data.datasets[0].data = history.map(h => h.signal_strength);
    chartSignal.update();

    // 4. System CPU & RAM
    chartSys.data.labels = labels;
    chartSys.data.datasets[0].data = history.map(h => h.cpu_usage);
    chartSys.data.datasets[1].data = history.map(h => h.ram_usage);
    chartSys.update();

    // 5. Load & Hotspot Devices
    chartLoad.data.labels = labels;
    chartLoad.data.datasets[0].data = history.map(h => h.tower_load);
    chartLoad.data.datasets[1].data = history.map(h => h.connected_client_count || 0);
    chartLoad.update();

    // 6. Temp
    chartTemp.data.labels = labels;
    chartTemp.data.datasets[0].data = history.map(h => h.system_temperature || 0);
    chartTemp.update();

    // 7. Power & Battery Voltage
    chartPower.data.labels = labels;
    chartPower.data.datasets[0].data = history.map(h => h.power_consumption);
    chartPower.data.datasets[1].data = history.map(h => h.battery_voltage);
    chartPower.update();

    // 8. Total Traffic
    chartTraffic.data.labels = labels;
    chartTraffic.data.datasets[0].data = history.map(h => h.total_network_traffic);
    chartTraffic.update();
}

/**
 * Trigger Demo Scenario via POST /api/demo-mode.
 */
async function triggerScenario(scenario) {
    try {
        const btns = document.querySelectorAll('.btn-scenario');
        btns.forEach(b => b.classList.remove('active'));
        if (event && event.currentTarget) event.currentTarget.classList.add('active');

        await fetch('/api/demo-mode', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ scenario })
        });
        fetchTelemetry();
    } catch (e) {
        console.error('Failed to trigger scenario:', e);
    }
}

/**
 * Reset Demo Mode and return to live monitoring via POST /api/demo-mode/reset.
 */
async function resetDemoMode() {
    try {
        const btns = document.querySelectorAll('.btn-scenario');
        btns.forEach(b => b.classList.remove('active'));
        document.querySelector('.btn-scenario').classList.add('active');

        await fetch('/api/demo-mode/reset', { method: 'POST' });
        fetchTelemetry();
    } catch (e) {
        console.error('Failed to reset demo mode:', e);
    }
}
