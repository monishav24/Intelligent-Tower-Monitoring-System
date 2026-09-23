/**
 * Intelligent Telecom Tower Monitoring Dashboard JavaScript
 * 100% Offline-First Execution, Real-Time Polling, Local Chart.js Graphs & Demo Mode Controls
 * Includes Live 3-Algorithm ML Comparison Module (Random Forest vs Gradient Boosting vs XGBoost)
 */

let chartSpeeds, chartBandwidth, chartSignal, chartSys, chartTemp, chartLoad, chartPower, chartTraffic;
let chartInputNetwork, chartInputSystem;
let chartRfPred, chartGbPred, chartXgbPred, chartCmpRmse, chartCmpR2;

const MAX_HISTORY_POINTS = 25;

document.addEventListener('DOMContentLoaded', () => {
    startClock();
    initOfflineCharts();
    initComparisonCharts();
    
    fetchTelemetry();
    fetchAlgorithmComparison();
    
    // Poll telemetry API every 2 seconds
    setInterval(fetchTelemetry, 2000);

    // Poll cached ML Comparison API every 5 seconds (Never triggers retraining)
    setInterval(fetchAlgorithmComparison, 5000);
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
 * Initialize 8 telemetry Chart.js multi-series graphs using local vendor library.
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
 * Initialize Comparison Module Chart.js instances (2 Live Input Time-Series + 3 Predictions + 2 Comparison Bar Charts).
 */
function initComparisonCharts() {
    const lineOpts = {
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

    // Live Input Graph 1: Network Telemetry Used by ML Models
    const ctxInNet = document.getElementById('chart-input-network');
    if (ctxInNet) {
        chartInputNetwork = new Chart(ctxInNet.getContext('2d'), {
            type: 'line',
            data: {
                labels: [],
                datasets: [
                    { label: 'Upload Speed (KB/s)', data: [], borderColor: '#10b981', tension: 0.2 },
                    { label: 'Download Speed (KB/s)', data: [], borderColor: '#06b6d4', tension: 0.2 },
                    { label: 'Bandwidth Utilization (%)', data: [], borderColor: '#8b5cf6', tension: 0.2 }
                ]
            },
            options: lineOpts
        });
    }

    // Live Input Graph 2: System / Connectivity Telemetry Used by ML Models
    const ctxInSys = document.getElementById('chart-input-system');
    if (ctxInSys) {
        chartInputSystem = new Chart(ctxInSys.getContext('2d'), {
            type: 'line',
            data: {
                labels: [],
                datasets: [
                    { label: 'CPU Usage (%)', data: [], borderColor: '#3b82f6', tension: 0.2 },
                    { label: 'RAM Usage (%)', data: [], borderColor: '#ec4899', tension: 0.2 },
                    { label: 'Wi-Fi Signal Strength (%)', data: [], borderColor: '#f97316', tension: 0.2 }
                ]
            },
            options: lineOpts
        });
    }

    // Prediction Chart 1: Random Forest Actual vs Predicted
    const ctxRf = document.getElementById('chart-rf-pred');
    if (ctxRf) {
        chartRfPred = new Chart(ctxRf.getContext('2d'), {
            type: 'line',
            data: {
                labels: [],
                datasets: [
                    { label: 'Actual Bandwidth (%)', data: [], borderColor: '#06b6d4', tension: 0.2, pointRadius: 2 },
                    { label: 'Random Forest Pred (%)', data: [], borderColor: '#8b5cf6', borderDash: [4, 4], tension: 0.2, pointRadius: 2 }
                ]
            },
            options: lineOpts
        });
    }

    // Prediction Chart 2: Gradient Boosting Actual vs Predicted
    const ctxGb = document.getElementById('chart-gb-pred');
    if (ctxGb) {
        chartGbPred = new Chart(ctxGb.getContext('2d'), {
            type: 'line',
            data: {
                labels: [],
                datasets: [
                    { label: 'Actual Bandwidth (%)', data: [], borderColor: '#06b6d4', tension: 0.2, pointRadius: 2 },
                    { label: 'Gradient Boosting Pred (%)', data: [], borderColor: '#10b981', borderDash: [4, 4], tension: 0.2, pointRadius: 2 }
                ]
            },
            options: lineOpts
        });
    }

    // Prediction Chart 3: XGBoost Actual vs Predicted
    const ctxXgb = document.getElementById('chart-xgb-pred');
    if (ctxXgb) {
        chartXgbPred = new Chart(ctxXgb.getContext('2d'), {
            type: 'line',
            data: {
                labels: [],
                datasets: [
                    { label: 'Actual Bandwidth (%)', data: [], borderColor: '#06b6d4', tension: 0.2, pointRadius: 2 },
                    { label: 'XGBoost Pred (%)', data: [], borderColor: '#f97316', borderDash: [4, 4], tension: 0.2, pointRadius: 2 }
                ]
            },
            options: lineOpts
        });
    }

    // Bar Chart 1: Combined RMSE Comparison
    const ctxRmse = document.getElementById('chart-cmp-rmse');
    if (ctxRmse) {
        chartCmpRmse = new Chart(ctxRmse.getContext('2d'), {
            type: 'bar',
            data: {
                labels: ['Random Forest', 'Gradient Boosting', 'XGBoost', 'Naive Baseline'],
                datasets: [{
                    label: 'RMSE (Lower is better)',
                    data: [0, 0, 0, 0],
                    backgroundColor: ['rgba(139, 92, 246, 0.7)', 'rgba(16, 185, 129, 0.7)', 'rgba(249, 115, 22, 0.7)', 'rgba(107, 114, 128, 0.5)'],
                    borderColor: ['#8b5cf6', '#10b981', '#f97316', '#6b7280'],
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    x: { grid: { display: false } },
                    y: { beginAtZero: true, grid: { color: 'rgba(255, 255, 255, 0.05)' } }
                }
            }
        });
    }

    // Bar Chart 2: Combined R² Comparison
    const ctxR2 = document.getElementById('chart-cmp-r2');
    if (ctxR2) {
        chartCmpR2 = new Chart(ctxR2.getContext('2d'), {
            type: 'bar',
            data: {
                labels: ['Random Forest', 'Gradient Boosting', 'XGBoost', 'Naive Baseline'],
                datasets: [{
                    label: 'R² Score (Higher is better)',
                    data: [0, 0, 0, 0],
                    backgroundColor: ['rgba(139, 92, 246, 0.7)', 'rgba(16, 185, 129, 0.7)', 'rgba(249, 115, 22, 0.7)', 'rgba(107, 114, 128, 0.5)'],
                    borderColor: ['#8b5cf6', '#10b981', '#f97316', '#6b7280'],
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    x: { grid: { display: false } },
                    y: { grid: { color: 'rgba(255, 255, 255, 0.05)' } }
                }
            }
        });
    }
}

/**
 * Fetch telemetry data from local Flask API endpoints.
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
 * Fetch cached ML algorithm comparison metrics from GET /api/model-comparison.
 */
async function fetchAlgorithmComparison() {
    try {
        const res = await fetch('/api/model-comparison').then(r => r.json());
        updateComparisonView(res);
    } catch (err) {
        console.error('Algorithm comparison fetch error:', err);
    }
}

/**
 * Update Algorithm Comparison Module UI (Live Inputs Card, Next Predictions Card, Input Graphs, Top Performer Card, 3 Line Charts, 2 Bar Charts, Benchmark Table).
 */
function updateComparisonView(res) {
    const bannerEl = document.getElementById('cmp-status-banner');
    const textEl = document.getElementById('cmp-status-text');
    const mainEl = document.getElementById('cmp-main-content');
    const warnNoteEl = document.getElementById('best-warning-note');

    if (!res || res.status === 'insufficient_data' || res.status === 'warming_up' || res.status === 'error') {
        if (bannerEl && textEl) {
            bannerEl.classList.remove('hidden');
            textEl.textContent = res.message || 'Comparison module initializing...';
        }
        if (mainEl) mainEl.style.opacity = '0.5';
        return;
    }

    if (bannerEl) bannerEl.classList.add('hidden');
    if (mainEl) mainEl.style.opacity = '1';

    const best = res.best_model || {};
    const models = res.models || {};
    const naive = res.naive_baseline || {};
    const windowInfo = res.evaluation_window || {};
    const currInputs = res.current_inputs || {};
    const nextPreds = res.next_interval_predictions || {};
    const inSeries = res.input_history_series || {};
    const series = res.test_series || {};

    // 1. STATUS METADATA BAR
    const startT = windowInfo.start_time ? windowInfo.start_time.split(' ')[1] || windowInfo.start_time : '--';
    const endT = windowInfo.end_time ? windowInfo.end_time.split(' ')[1] || windowInfo.end_time : '--';
    document.getElementById('cmp-window-range').textContent = `${startT} → ${endT}`;
    document.getElementById('cmp-updated-at').textContent = res.updated_at ? res.updated_at.split(' ')[1] || res.updated_at : '--';

    // 2. CURRENT ML INPUTS CARD (LIVE TELEMETRY LATEST SNAPSHOT)
    if (currInputs) {
        document.getElementById('input-upload').textContent = `${currInputs.upload_speed ?? 0.0} KB/s`;
        document.getElementById('input-download').textContent = `${currInputs.download_speed ?? 0.0} KB/s`;
        document.getElementById('input-bandwidth').textContent = `${currInputs.bandwidth_utilization ?? 0.0} %`;
        document.getElementById('input-signal').textContent = `${currInputs.signal_strength ?? 0} %`;
        document.getElementById('input-cpu').textContent = `${currInputs.cpu_usage ?? 0.0} %`;
        document.getElementById('input-ram').textContent = `${currInputs.ram_usage ?? 0.0} %`;
        document.getElementById('input-power').textContent = `${currInputs.power_consumption ?? 0.0} W`;
        document.getElementById('input-battery').textContent = `${currInputs.battery_voltage ?? 0.0} V`;
        const clientsEl = document.getElementById('input-clients');
        if (clientsEl) clientsEl.textContent = currInputs.connected_client_count ?? 0;
        document.getElementById('input-load').textContent = `${currInputs.tower_load ?? 0.0} %`;
        const deltaEl = document.getElementById('input-traffic-delta');
        if (deltaEl) deltaEl.textContent = `${(currInputs.traffic_delta ?? 0.0).toFixed(2)} MB`;
    }

    // 3. CURRENT NEXT-INTERVAL PREDICTIONS CARD
    if (nextPreds) {
        document.getElementById('next-pred-rf').textContent = `${nextPreds['Random Forest'] ?? 0.0} %`;
        document.getElementById('next-pred-gb').textContent = `${nextPreds['Gradient Boosting'] ?? 0.0} %`;
        document.getElementById('next-pred-xgb').textContent = `${nextPreds['XGBoost'] ?? 0.0} %`;
        const cardTimeEl = document.getElementById('cmp-updated-at-card');
        if (cardTimeEl) cardTimeEl.textContent = res.updated_at ? res.updated_at.split(' ')[1] || res.updated_at : '--';
    }

    // 4. DYNAMIC TOP PERFORMER CARD & WIN REASON
    document.getElementById('best-model-name').textContent = best.algorithm || '--';
    document.getElementById('best-win-reason').textContent = best.win_reason || 'Lowest RMSE on current evaluation window';
    document.getElementById('best-rmse').textContent = best.rmse !== undefined ? best.rmse.toFixed(4) : '--';
    document.getElementById('best-mae').textContent = best.mae !== undefined ? best.mae.toFixed(4) : '--';
    document.getElementById('best-r2').textContent = best.r2 !== undefined ? best.r2.toFixed(4) : '--';

    if (warnNoteEl) {
        if (best.is_weak_fit || (best.r2 !== undefined && best.r2 < 0)) {
            warnNoteEl.classList.remove('hidden');
        } else {
            warnNoteEl.classList.add('hidden');
        }
    }

    // 5. LIVE INPUT TELEMETRY TIME-SERIES CHARTS
    if (chartInputNetwork && inSeries.timestamps) {
        chartInputNetwork.data.labels = inSeries.timestamps;
        chartInputNetwork.data.datasets[0].data = inSeries.upload_speed || [];
        chartInputNetwork.data.datasets[1].data = inSeries.download_speed || [];
        chartInputNetwork.data.datasets[2].data = inSeries.bandwidth_utilization || [];
        chartInputNetwork.update();
    }

    if (chartInputSystem && inSeries.timestamps) {
        chartInputSystem.data.labels = inSeries.timestamps;
        chartInputSystem.data.datasets[0].data = inSeries.cpu_usage || [];
        chartInputSystem.data.datasets[1].data = inSeries.ram_usage || [];
        chartInputSystem.data.datasets[2].data = inSeries.signal_strength || [];
        chartInputSystem.update();
    }

    // 6. COMPARISON METRICS TABLE & DYNAMIC WINNER HIGHLIGHT
    const algoRows = {
        'Random Forest': { rowId: 'row-rf', prefix: 'tbl-rf' },
        'Gradient Boosting': { rowId: 'row-gb', prefix: 'tbl-gb' },
        'XGBoost': { rowId: 'row-xgb', prefix: 'tbl-xgb' }
    };

    Object.keys(algoRows).forEach(algo => {
        const info = algoRows[algo];
        const mData = models[algo] || {};
        const rowEl = document.getElementById(info.rowId);

        document.getElementById(`${info.prefix}-mae`).textContent = mData.mae !== undefined ? mData.mae.toFixed(4) : '--';
        document.getElementById(`${info.prefix}-rmse`).textContent = mData.rmse !== undefined ? mData.rmse.toFixed(4) : '--';
        document.getElementById(`${info.prefix}-r2`).textContent = mData.r2 !== undefined ? mData.r2.toFixed(4) : '--';
        document.getElementById(`${info.prefix}-time`).textContent = mData.train_time_sec !== undefined ? `${mData.train_time_sec.toFixed(4)} s` : '--';

        if (rowEl) {
            if (algo === best.algorithm) {
                rowEl.classList.add('best-model-row');
            } else {
                rowEl.classList.remove('best-model-row');
            }
        }
    });

    // Populate Naive Baseline Row
    if (naive) {
        const nMae = document.getElementById('tbl-naive-mae');
        const nRmse = document.getElementById('tbl-naive-rmse');
        const nR2 = document.getElementById('tbl-naive-r2');
        if (nMae) nMae.textContent = naive.mae !== undefined ? naive.mae.toFixed(4) : '--';
        if (nRmse) nRmse.textContent = naive.rmse !== undefined ? naive.rmse.toFixed(4) : '--';
        if (nR2) nR2.textContent = naive.r2 !== undefined ? naive.r2.toFixed(4) : '--';
    }

    // 7. METRIC CHIPS ABOVE INDIVIDUAL ALGORITHM GRAPHS
    const rfM = models['Random Forest'] || {};
    const gbM = models['Gradient Boosting'] || {};
    const xgbM = models['XGBoost'] || {};

    document.getElementById('chip-rf-metrics').textContent = `MAE ↓: ${rfM.mae ?? '--'} | RMSE ↓: ${rfM.rmse ?? '--'} | R² ↑: ${rfM.r2 ?? '--'}`;
    document.getElementById('chip-gb-metrics').textContent = `MAE ↓: ${gbM.mae ?? '--'} | RMSE ↓: ${gbM.rmse ?? '--'} | R² ↑: ${gbM.r2 ?? '--'}`;
    document.getElementById('chip-xgb-metrics').textContent = `MAE ↓: ${xgbM.mae ?? '--'} | RMSE ↓: ${xgbM.rmse ?? '--'} | R² ↑: ${xgbM.r2 ?? '--'}`;

    // 8. THREE SEPARATE ALGORITHM ACTUAL VS PREDICTED LINE CHARTS
    const timestamps = series.timestamps || [];
    const actual = series.actual || [];

    if (chartRfPred) {
        chartRfPred.data.labels = timestamps;
        chartRfPred.data.datasets[0].data = actual;
        chartRfPred.data.datasets[1].data = rfM.predictions || [];
        chartRfPred.update();
    }

    if (chartGbPred) {
        chartGbPred.data.labels = timestamps;
        chartGbPred.data.datasets[0].data = actual;
        chartGbPred.data.datasets[1].data = gbM.predictions || [];
        chartGbPred.update();
    }

    if (chartXgbPred) {
        chartXgbPred.data.labels = timestamps;
        chartXgbPred.data.datasets[0].data = actual;
        chartXgbPred.data.datasets[1].data = xgbM.predictions || [];
        chartXgbPred.update();
    }

    // 9. COMBINED RMSE & R² COMPARISON BAR CHARTS
    if (chartCmpRmse) {
        chartCmpRmse.data.datasets[0].data = [rfM.rmse ?? 0, gbM.rmse ?? 0, xgbM.rmse ?? 0, naive.rmse ?? 0];
        chartCmpRmse.update();
    }

    if (chartCmpR2) {
        chartCmpR2.data.datasets[0].data = [rfM.r2 ?? 0, gbM.r2 ?? 0, xgbM.r2 ?? 0, naive.r2 ?? 0];
        chartCmpR2.update();
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

    const esp32Badge = document.getElementById('status-esp32');
    if (esp32Badge) {
        const isEsp32Online = Boolean(data.esp32_online);
        if (isEsp32Online) {
            esp32Badge.textContent = 'ONLINE';
            esp32Badge.className = 'status-badge online';
        } else {
            esp32Badge.textContent = 'OFFLINE';
            esp32Badge.className = 'status-badge offline';
        }
    }

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
        tempSourceEl.textContent = data.temperature_source || 'Host Laptop';
    } else {
        tempEl.textContent = 'Sensor Unavailable';
        tempSourceEl.textContent = 'Host Laptop';
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

    // Active scenario tag & button highlight
    const activeSc = data.active_scenario || data.demo_scenario || 'NORMAL';
    document.getElementById('active-scenario-name').textContent = activeSc.replace('_', ' ');

    const btns = document.querySelectorAll('.btn-scenario');
    btns.forEach(b => {
        const onClickAttr = b.getAttribute('onclick') || '';
        if (onClickAttr.includes(`'${activeSc}'`)) {
            b.classList.add('active');
        } else if (!onClickAttr.includes('resetDemoMode')) {
            b.classList.remove('active');
        }
    });

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
