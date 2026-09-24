/**
 * Intelligent Telecom Tower Monitoring Dashboard JavaScript
 * 100% Offline-First Execution, Real-Time Telemetry Pipeline, Chart.js Graphs & Demo Mode Controls
 * Includes 3-Algorithm Multi-Target ML Experimental Evaluation (Random Forest vs Gradient Boosting vs Extra Trees)
 */

let chartOverallComparison;
let chartParamTraffic, chartParamDelay, chartParamThroughput, chartParamPropagation, chartParamRam;

document.addEventListener('DOMContentLoaded', () => {
    startClock();
    initComparisonCharts();
    
    fetchTelemetry();
    fetchAlgorithmComparison();
    
    // Poll telemetry API every 2 seconds
    setInterval(fetchTelemetry, 2000);

    // Poll cached ML Comparison API every 5 seconds
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
 * Initialize 3-Algorithm Comparison & 5 Parameter Comparison Chart.js Instances with Light Theme Styling.
 */
function initComparisonCharts() {
    Chart.defaults.color = '#475569';
    Chart.defaults.borderColor = '#BAE6FD';
    Chart.defaults.font.family = 'Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif';

    const lineOpts = {
        responsive: true,
        maintainAspectRatio: false,
        animation: { duration: 300 },
        plugins: {
            legend: { 
                position: 'top', 
                labels: { 
                    boxWidth: 20, 
                    padding: 12,
                    font: { size: 12, weight: '600' },
                    usePointStyle: false,
                    color: '#0F172A'
                } 
            },
            tooltip: { mode: 'index', intersect: false, backgroundColor: '#0F172A', titleColor: '#FFFFFF', bodyColor: '#BAE6FD' }
        },
        scales: {
            x: { grid: { display: false }, ticks: { maxRotation: 0, autoSkip: true, maxTicksLimit: 8, font: { size: 11 }, color: '#475569' } },
            y: { grid: { color: '#E0F2FE' }, ticks: { font: { size: 11 }, color: '#475569' } }
        }
    };

    // 1. Overall 3-Algorithm Comparison Bar Chart (Composite Score 0-10 Scale)
    const ctxOverall = document.getElementById('chart-overall-comparison');
    if (ctxOverall) {
        chartOverallComparison = new Chart(ctxOverall.getContext('2d'), {
            type: 'bar',
            data: {
                labels: ['Random Forest', 'Gradient Boosting', 'Extra Trees'],
                datasets: [{
                    label: 'Overall Composite Score (/ 10)',
                    data: [0, 0, 0],
                    backgroundColor: [
                        'rgba(124, 58, 237, 0.85)',
                        'rgba(22, 163, 74, 0.85)',
                        'rgba(234, 88, 12, 0.85)'
                    ],
                    borderColor: ['#7c3aed', '#16a34a', '#ea580c'],
                    borderWidth: 1.5,
                    borderRadius: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { 
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return `Composite Score: ${context.parsed.y.toFixed(2)} / 10`;
                            }
                        }
                    }
                },
                scales: {
                    x: { grid: { display: false }, ticks: { color: '#0F172A', font: { weight: '600' } } },
                    y: { 
                        beginAtZero: true, 
                        min: 0, 
                        max: 10, 
                        ticks: { stepSize: 2, color: '#475569', callback: value => `${value}` }, 
                        grid: { color: '#E0F2FE' } 
                    }
                }
            }
        });
    }

    // Helper to create parameter line chart with Sky Theme styling
    const createParamChart = (elementId, paramLabel) => {
        const ctx = document.getElementById(elementId);
        if (!ctx) return null;
        return new Chart(ctx.getContext('2d'), {
            type: 'line',
            data: {
                labels: [],
                datasets: [
                    { 
                        label: `Actual ${paramLabel}`, 
                        data: [], 
                        borderColor: '#0284c7', 
                        borderWidth: 2.5,
                        tension: 0.2, 
                        pointStyle: 'circle',
                        pointRadius: 3,
                        pointHoverRadius: 5,
                        pointBackgroundColor: '#0369a1',
                        pointBorderWidth: 0
                    },
                    { 
                        label: 'Random Forest Pred', 
                        data: [], 
                        borderColor: '#7c3aed', 
                        borderDash: [6, 4], 
                        borderWidth: 2,
                        tension: 0.2, 
                        pointStyle: 'circle',
                        pointRadius: 3,
                        pointHoverRadius: 5,
                        pointBackgroundColor: '#6d28d9',
                        pointBorderWidth: 0
                    },
                    { 
                        label: 'Gradient Boosting Pred', 
                        data: [], 
                        borderColor: '#059669', 
                        borderDash: [4, 4], 
                        borderWidth: 2,
                        tension: 0.2, 
                        pointStyle: 'circle',
                        pointRadius: 3,
                        pointHoverRadius: 5,
                        pointBackgroundColor: '#047857',
                        pointBorderWidth: 0
                    },
                    { 
                        label: 'Extra Trees Pred', 
                        data: [], 
                        borderColor: '#ea580c', 
                        borderWidth: 2,
                        tension: 0.2, 
                        pointStyle: 'circle',
                        pointRadius: 3,
                        pointHoverRadius: 5,
                        pointBackgroundColor: '#c2410c',
                        pointBorderWidth: 0
                    }
                ]
            },
            options: lineOpts
        });
    };

    chartParamTraffic = createParamChart('chart-param-traffic', 'Traffic (MB)');
    chartParamDelay = createParamChart('chart-param-delay', 'Delay (ms)');
    chartParamThroughput = createParamChart('chart-param-throughput', 'Throughput (Mbps)');
    chartParamPropagation = createParamChart('chart-param-propagation', 'Propagation Time (ms)');
    chartParamRam = createParamChart('chart-param-ram', 'RAM Usage (%)');
}

/**
 * Fetch live telemetry from Flask API endpoints.
 */
async function fetchTelemetry() {
    try {
        const [resLatest, resDiag] = await Promise.all([
            fetch('/api/latest').then(r => r.json()),
            fetch('/api/telemetry/diagnostic').then(r => r.json())
        ]);

        if (resLatest.status === 'success' && resLatest.data) {
            updateTelemetryUi(resLatest.data, resDiag.diagnostic);
            updateAlertsFeed(resLatest.recent_alerts);
        }
    } catch (err) {
        console.error('Telemetry fetch error:', err);
    }
}

/**
 * Update core live telemetry cards, live pipeline indicator, & predictions dashboard.
 */
function updateTelemetryUi(data, diag) {
    // 1. Live Telemetry Pipeline Status & Ticker
    const liveTag = document.getElementById('status-live-indicator');
    const tickerEl = document.getElementById('status-last-updated');

    const secSince = diag ? diag.seconds_since_latest : null;
    const isLive = diag ? diag.is_live : true;

    if (liveTag) {
        if (isLive) {
            liveTag.textContent = '● LIVE';
            liveTag.className = 'status-badge online';
        } else {
            liveTag.textContent = '● STALE';
            liveTag.className = 'status-badge offline';
        }
    }

    if (tickerEl) {
        if (secSince !== null && secSince !== undefined) {
            tickerEl.textContent = `Last updated: ${Math.round(secSince)}s ago`;
        } else {
            tickerEl.textContent = 'Last updated: 0s ago';
        }
    }

    // 2. Status Bar
    const netStatus = data.internet_status || 'ONLINE';
    const netBadge = document.getElementById('status-internet');
    netBadge.textContent = netStatus;
    netBadge.className = netStatus === 'ONLINE' ? 'status-badge online' : 'status-badge offline';

    const hotspotBadge = document.getElementById('status-hotspot');
    const hotspotState = data.hotspot_status || 'ACTIVE';
    hotspotBadge.textContent = hotspotState;
    hotspotBadge.className = hotspotState === 'ACTIVE' ? 'status-badge active' : 'status-badge inactive';

    const esp32Badge = document.getElementById('status-esp32');
    if (esp32Badge) {
        const isEsp32Online = Boolean(data.esp32_online);
        esp32Badge.textContent = isEsp32Online ? 'ONLINE' : 'OFFLINE';
        esp32Badge.className = isEsp32Online ? 'status-badge online' : 'status-badge offline';
    }

    const overallBadge = document.getElementById('status-overall');
    const overallState = data.overall_status || 'NORMAL';
    overallBadge.textContent = overallState;
    overallBadge.className = overallState === 'DISCONNECTED' ? 'status-badge disconnected' :
                            (overallState === 'CRITICAL' ? 'status-badge critical' :
                            (overallState === 'WARNING' ? 'status-badge warning' : 'status-badge normal'));

    // 3. Hardware Temperature Card (ONLY Hardware Sensor)
    const tempEl = document.getElementById('kpi-temp');
    const tempSourceEl = document.getElementById('kpi-temp-source');
    if (data.temperature !== undefined && data.temperature !== null) {
        tempEl.textContent = `${Number(data.temperature).toFixed(1)} °C`;
        tempSourceEl.textContent = data.temperature_source || 'ESP32 Hardware';
    } else {
        tempEl.textContent = 'Sensor Unavailable';
        tempSourceEl.textContent = 'Temperature Sensor Unavailable';
    }

    // 4. 5 Required Telemetry KPI Cards
    const trafficMb = data.traffic !== undefined ? data.traffic : (data.total_network_traffic || 0.0);
    document.getElementById('kpi-total-traffic').textContent = `${Number(trafficMb).toFixed(1)} MB`;

    const delayMs = data.delay !== undefined ? data.delay : (data.delay_ms || 0.0);
    document.getElementById('kpi-delay').textContent = `${Number(delayMs).toFixed(1)} ms`;

    const throughputMbps = data.throughput !== undefined ? data.throughput : (data.throughput_mbps || 0.0);
    document.getElementById('kpi-throughput').textContent = `${Number(throughputMbps).toFixed(2)} Mbps`;

    const propMs = data.propagation_time !== undefined ? data.propagation_time : (data.propagation_time_ms || 0.0);
    document.getElementById('kpi-propagation').textContent = `${Number(propMs).toFixed(2)} ms`;

    const ramPct = data.ram_usage !== undefined ? data.ram_usage : 0.0;
    document.getElementById('kpi-ram').textContent = `${Number(ramPct).toFixed(1)} %`;

    // 5. Live ML Predictions Dashboard (Generated by Fixed Selected Model)
    const selectedModel = data.selected_model || data.best_algorithm || data.active_model || 'Random Forest';
    document.getElementById('live-active-model-badge').textContent = `SELECTED MODEL: ${selectedModel}`;

    const predTraffic = data.predicted_traffic !== undefined ? data.predicted_traffic : (data.predicted_network_traffic || 0.0);
    document.getElementById('pred-val-traffic').textContent = `${Number(predTraffic).toFixed(2)} MB`;

    const predDelay = data.predicted_delay !== undefined ? data.predicted_delay : 0.0;
    document.getElementById('pred-val-delay').textContent = `${Number(predDelay).toFixed(1)} ms`;

    const predThroughput = data.predicted_throughput !== undefined ? data.predicted_throughput : 0.0;
    document.getElementById('pred-val-throughput').textContent = `${Number(predThroughput).toFixed(2)} Mbps`;

    const predProp = data.predicted_propagation_time !== undefined ? data.predicted_propagation_time : 0.0;
    document.getElementById('pred-val-propagation').textContent = `${Number(predProp).toFixed(2)} ms`;

    const predRam = data.predicted_ram_usage !== undefined ? data.predicted_ram_usage : 0.0;
    document.getElementById('pred-val-ram').textContent = `${Number(predRam).toFixed(1)} %`;

    // Risk indicator
    const riskPct = Math.min(Math.max(data.congestion_risk || 0.0, 0), 100);
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

    // Hotspot details
    const clientCount = data.connected_client_count || 0;
    document.getElementById('hotspot-device-count').textContent = `${clientCount} Device${clientCount !== 1 ? 's' : ''}`;
    document.getElementById('hotspot-state-text').textContent = hotspotState;

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

    // Active scenario name
    const activeSc = data.active_scenario || data.demo_scenario || 'NORMAL';
    document.getElementById('active-scenario-name').textContent = activeSc.replace('_', ' ');
}

/**
 * Fetch cached ML 3-algorithm comparison data.
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
 * Trigger manual model retraining of all 3 algorithms via POST /api/ml/retrain.
 */
async function triggerRetrain() {
    try {
        const nameEl = document.getElementById('best-model-name');
        if (nameEl) nameEl.textContent = 'Retraining All 3...';
        const res = await fetch('/api/ml/retrain', { method: 'POST' }).then(r => r.json());
        if (res.data) {
            updateComparisonView(res.data);
        }
        fetchTelemetry();
    } catch (err) {
        console.error('Retrain error:', err);
    }
}

/**
 * Update 3-Algorithm Comparison View (Status Cards, Overall Graph, Best Algorithm Card, Performance Table, Dataset Info, 5 Parameter Graphs).
 */
function updateComparisonView(res) {
    if (!res || res.status === 'insufficient_data' || res.status === 'warming_up' || res.status === 'error') {
        const winnerEl = document.getElementById('best-model-name');
        if (winnerEl) winnerEl.textContent = res.message || 'Collecting telemetry...';
        return;
    }

    const bestAlgorithm = res.best_algorithm || res.selected_model || res.active_model || 'Random Forest';
    const topPerformer = res.top_performer || {};
    const overallScores = res.overall_scores || {};
    const datasetInfo = res.dataset_info || {};
    const models = res.models || {};
    const paramSeries = res.parameter_comparison || {};

    // 1. UPDATE EXECUTION STATUS CARDS FOR ALL 3 ALGORITHMS
    const rfScore = overallScores['Random Forest'] !== undefined ? `${Number(overallScores['Random Forest']).toFixed(2)} / 10` : '-- / 10';
    const gbScore = overallScores['Gradient Boosting'] !== undefined ? `${Number(overallScores['Gradient Boosting']).toFixed(2)} / 10` : '-- / 10';
    const etScore = overallScores['Extra Trees'] !== undefined ? `${Number(overallScores['Extra Trees']).toFixed(2)} / 10` : '-- / 10';

    const cardRf = document.getElementById('card-score-rf');
    if (cardRf) cardRf.textContent = rfScore;
    const cardGb = document.getElementById('card-score-gb');
    if (cardGb) cardGb.textContent = gbScore;
    const cardEt = document.getElementById('card-score-et');
    if (cardEt) cardEt.textContent = etScore;

    // 2. BEST ALGORITHM CARD (Displays exactly ONE best-performing algorithm)
    document.getElementById('best-model-name').textContent = topPerformer.algorithm || bestAlgorithm;
    document.getElementById('best-overall-score').textContent = topPerformer.score !== undefined ? `${Number(topPerformer.score).toFixed(2)} / 10` : '-- / 10';

    // 3. OVERALL COMPARISON BAR CHART (0-10 Scale)
    if (chartOverallComparison) {
        const numRf = overallScores['Random Forest'] || 0;
        const numGb = overallScores['Gradient Boosting'] || 0;
        const numEt = overallScores['Extra Trees'] || 0;
        chartOverallComparison.data.datasets[0].data = [numRf, numGb, numEt];
        chartOverallComparison.update();
    }

    // 4. DATASET INFORMATION CARD
    if (datasetInfo) {
        document.getElementById('ds-source').textContent = datasetInfo.source || 'Live SQLite Telemetry';
        document.getElementById('ds-samples').textContent = `${datasetInfo.total_samples || 0} samples`;
        document.getElementById('ds-split').textContent = `Train: ${datasetInfo.train_samples || 0} | Test: ${datasetInfo.test_samples || 0}`;
        document.getElementById('ds-last-train').textContent = datasetInfo.last_training ? (datasetInfo.last_training.split(' ')[1] || datasetInfo.last_training) : '--';
        document.getElementById('ds-active-model').textContent = bestAlgorithm;
    }

    // 5. MODEL PERFORMANCE TABLE (Columns: Algorithm, Parameter, MAE, RMSE, R², Composite Score / 10, Selection Status)
    const tbody = document.getElementById('cmp-table-body');
    if (tbody && models) {
        let rowsHtml = '';
        const algoNames = ['Random Forest', 'Gradient Boosting', 'Extra Trees'];
        const paramNames = ['traffic', 'delay', 'throughput', 'propagation_time', 'ram_usage'];
        const paramLabels = {
            'traffic': 'Traffic (MB)',
            'delay': 'Delay (ms)',
            'throughput': 'Throughput (Mbps)',
            'propagation_time': 'Propagation Time (ms)',
            'ram_usage': 'RAM Usage (%)'
        };

        algoNames.forEach(algo => {
            const mData = models[algo] || {};
            const targets = mData.targets || {};
            const rawScore = mData.overall_score !== undefined ? mData.overall_score : 0;
            const formattedScore = `${Number(rawScore).toFixed(2)} / 10`;
            const isBest = (algo === bestAlgorithm);
            const statusBadge = isBest ? '<span class="status-badge online">🏆 BEST ALGORITHM</span>' : '<span style="color: var(--text-muted); font-size: 0.78rem;">✓ Evaluated</span>';

            paramNames.forEach((param, idx) => {
                const tInfo = targets[param] || {};
                const mae = tInfo.mae !== undefined ? tInfo.mae.toFixed(4) : '--';
                const rmse = tInfo.rmse !== undefined ? tInfo.rmse.toFixed(4) : '--';
                const r2 = tInfo.r2 !== undefined ? tInfo.r2.toFixed(4) : '--';

                rowsHtml += `
                    <tr class="${isBest ? 'best-model-row' : ''}">
                        ${idx === 0 ? `<td rowspan="5" style="vertical-align: middle; font-weight: 700;">${algo}</td>` : ''}
                        <td>${paramLabels[param]}</td>
                        <td>${mae}</td>
                        <td>${rmse}</td>
                        <td>${r2}</td>
                        ${idx === 0 ? `<td rowspan="5" style="vertical-align: middle; font-weight: 800; font-size: 1.05rem; color: var(--color-actual);">${formattedScore}</td>` : ''}
                        ${idx === 0 ? `<td rowspan="5" style="vertical-align: middle;">${statusBadge}</td>` : ''}
                    </tr>
                `;
            });
        });

        tbody.innerHTML = rowsHtml;
    }

    // 6. UPDATE 5 SEPARATE PARAMETER COMPARISON LINE CHARTS
    const updateParamChart = (chart, targetName) => {
        if (!chart || !paramSeries[targetName]) return;
        const dataObj = paramSeries[targetName];
        chart.data.labels = dataObj.timestamps || [];
        chart.data.datasets[0].data = dataObj.actual || [];
        chart.data.datasets[1].data = dataObj.rf_predictions || [];
        chart.data.datasets[2].data = dataObj.gb_predictions || [];
        chart.data.datasets[3].data = dataObj.et_predictions || [];
        chart.update();
    };

    updateParamChart(chartParamTraffic, 'traffic');
    updateParamChart(chartParamDelay, 'delay');
    updateParamChart(chartParamThroughput, 'throughput');
    updateParamChart(chartParamPropagation, 'propagation_time');
    updateParamChart(chartParamRam, 'ram_usage');
}

/**
 * Render active alerts feed.
 */
function updateAlertsFeed(alerts) {
    const feedEl = document.getElementById('alerts-feed');
    const badgeEl = document.getElementById('alerts-count');

    if (!alerts || alerts.length === 0) {
        badgeEl.textContent = '0 Alerts';
        badgeEl.className = 'status-badge online';
        feedEl.innerHTML = `
            <div class="empty-alerts">
                <p>✅ All monitored parameters operating within normal thresholds.</p>
            </div>
        `;
        return;
    }

    badgeEl.textContent = `${alerts.length} Active`;
    badgeEl.className = 'status-badge warning';
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
