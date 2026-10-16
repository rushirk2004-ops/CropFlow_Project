/**
 * CropFlow Dashboard Interactive Controller
 * Initializes Chart.js visualizations, manages live drought scenario simulation,
 * multi-metric algorithm benchmarking, and updates dynamic KPIs via REST API endpoints.
 */

let allocationsChart = null;
let comparisonChart = null;
let droughtCurveChart = null;
let soilMoistureChart = null;

let currentComparisonData = null;
let currentActiveStrategy = 'hybrid'; // 'hybrid', 'dynamic_programming', 'greedy'
let currentComparisonMetric = 'costs'; // 'costs', 'unmet', 'runtime', 'yield'

document.addEventListener("DOMContentLoaded", function () {
    if (!window.cropflowData || !window.cropflowData.plots || window.cropflowData.plots.length === 0) {
        return;
    }

    currentComparisonData = window.cropflowData.comparison || {};

    initPlotAllocationsChart();
    initStrategyComparisonChart();
    initSoilMoistureChart();
    loadDroughtSimulationData();
    initDroughtSlider();
});

// =============================================================================
// Feature 6: Bar chart comparing water allocation by plot
// =============================================================================
function initPlotAllocationsChart() {
    const ctx = document.getElementById("plotAllocationsChart");
    if (!ctx) return;

    const plots = window.cropflowData.plots || [];
    const activeStrategyResult = currentComparisonData.results?.[currentActiveStrategy] || {};
    const allocMap = {};
    (activeStrategyResult.allocations || []).forEach(a => {
        allocMap[a.plot_name] = a.allocated_water;
    });

    const labels = plots.map(p => p.name);
    const demands = plots.map(p => p.water_demand);
    const allocated = plots.map(p => allocMap[p.name] !== undefined ? allocMap[p.name] : 0.0);

    allocationsChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Required Demand (m³)',
                    data: demands,
                    backgroundColor: 'rgba(245, 158, 11, 0.35)',
                    borderColor: 'rgba(245, 158, 11, 1)',
                    borderWidth: 1.5,
                    borderRadius: 6
                },
                {
                    label: 'Allocated Water (m³)',
                    data: allocated,
                    backgroundColor: 'rgba(16, 185, 129, 0.8)',
                    borderColor: 'rgba(16, 185, 129, 1)',
                    borderWidth: 1.5,
                    borderRadius: 6
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'top', labels: { boxWidth: 14, font: { family: "'Plus Jakarta Sans', sans-serif" } } },
                tooltip: {
                    callbacks: {
                        label: function (context) {
                            return `${context.dataset.label}: ${context.raw} m³`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: { display: false },
                    ticks: { font: { size: 11 } }
                },
                y: {
                    beginAtZero: true,
                    title: { display: true, text: 'Water Volume (m³)', font: { size: 11, weight: 'bold' } },
                    grid: { color: 'rgba(0, 0, 0, 0.04)' }
                }
            }
        }
    });
}

function switchStrategyView(strategyKey) {
    currentActiveStrategy = strategyKey;

    // Update toggle button states
    const toggleContainer = document.getElementById("strategyViewToggle");
    if (toggleContainer) {
        toggleContainer.querySelectorAll("button").forEach(btn => {
            btn.classList.remove("btn-emerald", "active");
            btn.classList.add("btn-outline-secondary");
        });
    }

    const clickedBtn = event?.currentTarget;
    if (clickedBtn) {
        clickedBtn.classList.remove("btn-outline-secondary");
        clickedBtn.classList.add("btn-emerald", "active");
    }

    // Update allocations chart
    const activeResult = currentComparisonData.results?.[strategyKey] || {};
    const allocMap = {};
    (activeResult.allocations || []).forEach(a => {
        allocMap[a.plot_name] = a.allocated_water;
    });

    if (allocationsChart) {
        const plots = window.cropflowData.plots || [];
        allocationsChart.data.datasets[1].data = plots.map(p => allocMap[p.name] !== undefined ? allocMap[p.name] : 0.0);
        
        let color = 'rgba(16, 185, 129, 0.8)';
        let border = 'rgba(16, 185, 129, 1)';
        if (strategyKey === 'greedy') {
            color = 'rgba(245, 158, 11, 0.8)';
            border = 'rgba(245, 158, 11, 1)';
        } else if (strategyKey === 'dynamic_programming') {
            color = 'rgba(14, 165, 233, 0.8)';
            border = 'rgba(14, 165, 233, 1)';
        }
        allocationsChart.data.datasets[1].backgroundColor = color;
        allocationsChart.data.datasets[1].borderColor = border;
        allocationsChart.update();
    }

    // Update table view
    updatePlotAllocationsTable(activeResult.allocations || []);
    const label = document.getElementById("tableStrategyLabel");
    if (label) {
        const nameMap = {
            'hybrid': 'Hybrid Strategy (Proposed)',
            'dynamic_programming': 'Dynamic Programming',
            'greedy': 'Greedy Allocation'
        };
        label.textContent = nameMap[strategyKey] || strategyKey;
    }
}

// =============================================================================
// Feature 7: Comparison charts for Costs, Unmet Demand, and Runtime
// =============================================================================
function initStrategyComparisonChart() {
    const ctx = document.getElementById("strategyComparisonChart");
    if (!ctx) return;

    renderComparisonChartMetric(currentComparisonMetric);
}

function setComparisonMetric(metricKey) {
    currentComparisonMetric = metricKey;

    // Update active tab pill
    const tabs = document.getElementById("comparisonMetricTabs");
    if (tabs) {
        tabs.querySelectorAll("button").forEach(b => b.classList.remove("active"));
    }
    if (event?.currentTarget) {
        event.currentTarget.classList.add("active");
    }

    renderComparisonChartMetric(metricKey);
}

function renderComparisonChartMetric(metricKey) {
    const ctx = document.getElementById("strategyComparisonChart");
    if (!ctx) return;

    const comp = currentComparisonData.results || {};
    const greedy = comp.greedy || {};
    const dp = comp.dynamic_programming || {};
    const hybrid = comp.hybrid || {};

    let metricLabel = 'Cost (₹)';
    let data = [greedy.total_cost || 0, dp.total_cost || 0, hybrid.total_cost || 0];
    let yAxisTitle = 'Cost (₹)';
    let formatPrefix = '₹';
    let formatSuffix = '';

    if (metricKey === 'costs') {
        metricLabel = 'Estimated Irrigation Cost (₹)';
        data = [greedy.total_cost || 0, dp.total_cost || 0, hybrid.total_cost || 0];
        yAxisTitle = 'Cost (₹)';
        formatPrefix = '₹';
    } else if (metricKey === 'unmet') {
        metricLabel = 'Unmet Crop Water Demand (m³)';
        data = [greedy.unmet_demand || 0, dp.unmet_demand || 0, hybrid.unmet_demand || 0];
        yAxisTitle = 'Unmet Volume (m³)';
        formatPrefix = '';
        formatSuffix = ' m³';
    } else if (metricKey === 'runtime') {
        metricLabel = 'Execution Runtime (ms)';
        data = [greedy.execution_time_ms || 0, dp.execution_time_ms || 0, hybrid.execution_time_ms || 0];
        yAxisTitle = 'Time (ms)';
        formatPrefix = '';
        formatSuffix = ' ms';
    } else if (metricKey === 'yield') {
        metricLabel = 'Preserved Crop Yield Value (₹)';
        data = [greedy.total_benefit || 0, dp.total_benefit || 0, hybrid.total_benefit || 0];
        yAxisTitle = 'Preserved Value (₹)';
        formatPrefix = '₹';
    }

    if (comparisonChart) {
        comparisonChart.destroy();
    }

    comparisonChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['Greedy', 'Dyn Prog', 'Hybrid'],
            datasets: [{
                label: metricLabel,
                data: data,
                backgroundColor: [
                    'rgba(245, 158, 11, 0.75)',
                    'rgba(14, 165, 233, 0.75)',
                    'rgba(16, 185, 129, 0.85)'
                ],
                borderColor: [
                    'rgba(245, 158, 11, 1)',
                    'rgba(14, 165, 233, 1)',
                    'rgba(16, 185, 129, 1)'
                ],
                borderWidth: 1.5,
                borderRadius: 8
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: function (context) {
                            return `${metricLabel}: ${formatPrefix}${Number(context.raw).toLocaleString()}${formatSuffix}`;
                        }
                    }
                }
            },
            scales: {
                x: { grid: { display: false } },
                y: {
                    beginAtZero: true,
                    title: { display: true, text: yAxisTitle, font: { size: 11, weight: 'bold' } },
                    grid: { color: 'rgba(0, 0, 0, 0.04)' }
                }
            }
        }
    });
}

// =============================================================================
// Soil Moisture Profile Chart
// =============================================================================
function initSoilMoistureChart() {
    const ctx = document.getElementById("soilMoistureChart");
    if (!ctx) return;

    const plots = window.cropflowData.plots || [];
    const labels = plots.map(p => p.name.split(' - ')[1] || p.name);
    const wilting = plots.map(p => p.wilting_point);
    const current = plots.map(p => p.current_moisture);
    const target = plots.map(p => p.target_moisture);

    soilMoistureChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Wilting Point (%)',
                    data: wilting,
                    backgroundColor: 'rgba(239, 68, 68, 0.4)',
                    borderColor: 'rgba(239, 68, 68, 1)',
                    borderWidth: 1
                },
                {
                    label: 'Current Moisture (%)',
                    data: current,
                    backgroundColor: 'rgba(14, 165, 233, 0.75)',
                    borderColor: 'rgba(14, 165, 233, 1)',
                    borderWidth: 1
                },
                {
                    label: 'Target Moisture (%)',
                    data: target,
                    backgroundColor: 'rgba(16, 185, 129, 0.4)',
                    borderColor: 'rgba(16, 185, 129, 1)',
                    borderWidth: 1
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'top', labels: { boxWidth: 12, font: { size: 10 } } }
            },
            scales: {
                x: { grid: { display: false } },
                y: {
                    beginAtZero: true,
                    max: 100,
                    title: { display: true, text: 'Moisture (%)', font: { size: 10, weight: 'bold' } },
                    grid: { color: 'rgba(0, 0, 0, 0.04)' }
                }
            }
        }
    });
}

// =============================================================================
// Feature 8: Drought Scenario Simulator
// =============================================================================
function initDroughtSlider() {
    const slider = document.getElementById("droughtSlider");
    if (!slider) return;

    slider.addEventListener("change", function (e) {
        const pct = parseInt(e.target.value);
        triggerOptimization(pct);
    });

    slider.addEventListener("input", function (e) {
        const pct = parseInt(e.target.value);
        const baseBudget = window.cropflowData.farmBudget;
        const currentBudget = ((baseBudget * pct) / 100.0).toFixed(1);
        const label = document.getElementById("sliderPctLabel");
        if (label) {
            label.textContent = `${pct}% Supply (${currentBudget} m³) - Recalculating...`;
        }
    });
}

function setDroughtPreset(pct) {
    const slider = document.getElementById("droughtSlider");
    if (slider) {
        slider.value = pct;
        triggerOptimization(pct);
    }
}

function triggerOptimization(pct) {
    const baseBudget = window.cropflowData.farmBudget;
    const currentBudget = ((baseBudget * pct) / 100.0).toFixed(1);
    const label = document.getElementById("sliderPctLabel");
    if (label) {
        label.textContent = `${pct}% Supply (${currentBudget} m³) - Live Solver Running...`;
    }

    fetch('/api/optimize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            farm_id: window.cropflowData.farmId,
            algorithm: 'all',
            water_override: parseFloat(currentBudget),
            scenario_name: `${pct}% Drought Curtailment`,
            save_run: false
        })
    })
    .then(r => {
        if (!r.ok) throw new Error("Optimization failed.");
        return r.json();
    })
    .then(comp => {
        if (!comp.results) return;
        currentComparisonData = comp;

        // Update KPIs
        updateDashboardKPIs(comp, parseFloat(currentBudget));

        // Update Runtimes
        updateRuntimeDisplay(comp);

        // Update Charts
        if (allocationsChart) {
            const activeResult = comp.results[currentActiveStrategy] || comp.results.hybrid;
            const allocMap = {};
            (activeResult.allocations || []).forEach(a => allocMap[a.plot_name] = a.allocated_water);
            allocationsChart.data.datasets[1].data = (window.cropflowData.plots || []).map(p => allocMap[p.name] !== undefined ? allocMap[p.name] : 0.0);
            allocationsChart.update();
        }

        renderComparisonChartMetric(currentComparisonMetric);

        // Update Plot Allocations Table
        const activeResult = comp.results[currentActiveStrategy] || comp.results.hybrid;
        updatePlotAllocationsTable(activeResult.allocations || []);

        if (label) {
            label.textContent = `${pct}% Supply (${currentBudget} m³) - Solved (Yield: ₹${(activeResult.total_benefit || 0).toLocaleString()})`;
        }
    })
    .catch(err => {
        console.error("Drought simulation error:", err);
        showDynamicAlert("Failed to execute drought optimization. Please try again.", "danger");
    });
}

// =============================================================================
// Feature 10: "Run All Three Algorithms" Action
// =============================================================================
function runAllAlgorithms() {
    const btn = document.getElementById("runAllAlgorithmsBtn");
    const btnText = document.getElementById("runAllBtnText");
    const originalText = btnText ? btnText.textContent : "Run All 3 Algorithms";

    if (btn) btn.disabled = true;
    if (btnText) {
        btnText.innerHTML = '<span class="cropflow-spinner me-1"></span> Optimizing...';
    }

    const baseBudget = window.cropflowData.farmBudget;

    fetch('/api/optimize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            farm_id: window.cropflowData.farmId,
            algorithm: 'all',
            water_override: baseBudget,
            scenario_name: "Multi-Strategy Benchmark Run",
            save_run: true
        })
    })
    .then(r => {
        if (!r.ok) throw new Error("Failed to run all algorithms.");
        return r.json();
    })
    .then(comp => {
        if (!comp.results) return;
        currentComparisonData = comp;

        // Update KPIs
        updateDashboardKPIs(comp, baseBudget);

        // Update Runtime displays
        updateRuntimeDisplay(comp);

        // Refresh Charts
        if (allocationsChart) {
            const activeResult = comp.results[currentActiveStrategy] || comp.results.hybrid;
            const allocMap = {};
            (activeResult.allocations || []).forEach(a => allocMap[a.plot_name] = a.allocated_water);
            allocationsChart.data.datasets[1].data = (window.cropflowData.plots || []).map(p => allocMap[p.name] !== undefined ? allocMap[p.name] : 0.0);
            allocationsChart.update();
        }

        renderComparisonChartMetric(currentComparisonMetric);

        // Update Table
        const activeResult = comp.results[currentActiveStrategy] || comp.results.hybrid;
        updatePlotAllocationsTable(activeResult.allocations || []);

        // Refresh History View
        fetchHistoryRuns();

        showDynamicAlert("All 3 optimization strategies executed successfully on the current agricultural dataset! Results saved to database.", "success");
    })
    .catch(err => {
        console.error("Error executing all algorithms:", err);
        showDynamicAlert("Optimization failed: " + err.message, "danger");
    })
    .finally(() => {
        if (btn) btn.disabled = false;
        if (btnText) btnText.textContent = originalText;
    });
}

// =============================================================================
// Dynamic UI Update Utilities
// =============================================================================
function updateDashboardKPIs(comp, budget) {
    const activeResult = comp.results[currentActiveStrategy] || comp.results.hybrid || {};
    const totalDemand = window.cropflowData.totalDemand || 0.0;

    // Available Water
    const kpiAvail = document.getElementById("kpiAvailableWater");
    if (kpiAvail) {
        kpiAvail.innerHTML = `${budget.toFixed(1)} <span class="fs-6 fw-normal text-muted">/ ${totalDemand.toFixed(1)} m³</span>`;
    }

    // Water Balance
    const balance = budget - totalDemand;
    const balanceEl = document.getElementById("kpiWaterBalance");
    if (balanceEl) {
        if (balance < 0) {
            balanceEl.innerHTML = `<span class="text-danger fw-semibold"><i class="bi bi-exclamation-triangle-fill me-1"></i> Deficit: ${Math.abs(balance).toFixed(1)} m³</span>`;
        } else {
            balanceEl.innerHTML = `<span class="text-success fw-semibold"><i class="bi bi-check-circle-fill me-1"></i> Surplus: +${balance.toFixed(1)} m³</span>`;
        }
    }

    // Allocated & Unmet
    const kpiAlloc = document.getElementById("kpiAllocatedWater");
    if (kpiAlloc) {
        kpiAlloc.innerHTML = `${(activeResult.total_allocated || 0).toFixed(1)} <span class="fs-6 fw-normal text-muted">m³</span>`;
    }

    const kpiUnmet = document.getElementById("kpiUnmetDemand");
    if (kpiUnmet) {
        kpiUnmet.textContent = `${(activeResult.unmet_demand || 0).toFixed(1)} m³`;
    }

    const kpiCoverage = document.getElementById("kpiCoverageBadge");
    if (kpiCoverage && totalDemand > 0) {
        const covPct = Math.min(100, (activeResult.total_allocated / totalDemand * 100.0)).toFixed(1);
        kpiCoverage.textContent = `${covPct}% Coverage`;
    }

    // Water Utilization
    const kpiUtil = document.getElementById("kpiUtilization");
    if (kpiUtil) {
        kpiUtil.textContent = `${(activeResult.water_utilization_pct || 0).toFixed(1)}%`;
    }
    const kpiUtilBar = document.getElementById("kpiUtilizationBar");
    if (kpiUtilBar) {
        kpiUtilBar.style.width = `${Math.min(100, activeResult.water_utilization_pct || 0)}%`;
    }

    const kpiFairness = document.getElementById("kpiFairness");
    if (kpiFairness) {
        kpiFairness.textContent = (activeResult.fairness_index || 0).toFixed(3);
    }

    // Cost & Net Return
    const kpiCost = document.getElementById("kpiTotalCost");
    if (kpiCost) {
        kpiCost.textContent = `₹${(activeResult.total_cost || 0).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
    }

    const kpiNet = document.getElementById("kpiNetReturn");
    if (kpiNet) {
        kpiNet.textContent = `₹${(activeResult.net_return || 0).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
    }

    const tableBudget = document.getElementById("tableBudgetLabel");
    if (tableBudget) {
        tableBudget.textContent = budget.toFixed(1);
    }
}

function updateRuntimeDisplay(comp) {
    const greedyTime = document.getElementById("runtimeGreedy");
    if (greedyTime && comp.results?.greedy) {
        greedyTime.textContent = (comp.results.greedy.execution_time_ms || 0).toFixed(2);
    }

    const dpTime = document.getElementById("runtimeDP");
    if (dpTime && comp.results?.dynamic_programming) {
        dpTime.textContent = (comp.results.dynamic_programming.execution_time_ms || 0).toFixed(2);
    }

    const hybridTime = document.getElementById("runtimeHybrid");
    if (hybridTime && comp.results?.hybrid) {
        hybridTime.textContent = (comp.results.hybrid.execution_time_ms || 0).toFixed(2);
    }
}

// =============================================================================
// Feature 9: Detailed Plot Demand, Allocation & Remaining Unmet Demand Table
// =============================================================================
function updatePlotAllocationsTable(allocations) {
    if (!allocations || allocations.length === 0) return;

    allocations.forEach((item, idx) => {
        const row = document.getElementById(`plot-row-${idx}`);
        if (!row) return;

        const cellAlloc = row.querySelector(".cell-allocated");
        if (cellAlloc) cellAlloc.textContent = `${item.allocated_water.toFixed(1)} m³`;

        const cellUnmet = row.querySelector(".cell-unmet");
        if (cellUnmet) {
            cellUnmet.textContent = `${item.unmet_demand.toFixed(1)} m³`;
            if (item.unmet_demand > 0) {
                cellUnmet.classList.remove("text-muted");
                cellUnmet.classList.add("text-danger");
            } else {
                cellUnmet.classList.remove("text-danger");
                cellUnmet.classList.add("text-muted");
            }
        }

        const cellCov = row.querySelector(".cell-coverage");
        if (cellCov) {
            const bar = cellCov.querySelector(".progress-bar");
            if (bar) {
                bar.style.width = `${Math.min(100, item.coverage_pct)}%`;
                bar.className = 'progress-bar';
                if (item.coverage_pct >= 90) bar.classList.add('bg-success');
                else if (item.coverage_pct >= 50) bar.classList.add('bg-info');
                else if (item.coverage_pct > 0) bar.classList.add('bg-warning');
                else bar.classList.add('bg-danger');
            }
            const covText = cellCov.querySelector("span");
            if (covText) covText.textContent = `${item.coverage_pct.toFixed(1)}%`;
        }

        const cellYield = row.querySelector(".cell-yield");
        if (cellYield) {
            cellYield.textContent = `${item.yield_preservation_pct.toFixed(1)}%`;
        }

        const cellCost = row.querySelector(".cell-cost");
        if (cellCost) {
            cellCost.textContent = `₹${item.cost.toFixed(2)}`;
        }
    });
}

// =============================================================================
// Feature 11: Results History View & Audits
// =============================================================================
function fetchHistoryRuns() {
    const farmId = window.cropflowData.farmId;
    fetch(`/api/reports/history?farm_id=${farmId}`)
    .then(r => r.json())
    .then(data => {
        if (!data.runs) return;
        renderHistoryTable(data.runs.slice(0, 8));
    })
    .catch(err => console.error("Error refreshing history table:", err));
}

function renderHistoryTable(runs) {
    const tbody = document.getElementById("historyTableBody");
    if (!tbody) return;

    if (!runs || runs.length === 0) {
        tbody.innerHTML = `
            <tr id="emptyHistoryRow">
                <td colspan="10" class="text-center text-muted py-3">
                    No historical runs saved yet. Click <strong>"Run All 3 Algorithms"</strong> above to benchmark and save runs.
                </td>
            </tr>
        `;
        return;
    }

    let html = '';
    runs.forEach(r => {
        let badgeClass = 'badge-greedy';
        if (r.algorithm.includes('Hybrid')) badgeClass = 'badge-hybrid';
        else if (r.algorithm.includes('Dynamic')) badgeClass = 'badge-dp';

        html += `
            <tr>
                <td class="font-mono fw-bold">#${r.id}</td>
                <td class="small text-muted">${r.created_at || 'Just now'}</td>
                <td><span class="badge ${badgeClass}">${r.algorithm}</span></td>
                <td class="font-mono">${r.available_water} m³</td>
                <td class="font-mono text-emerald fw-semibold">${r.total_allocated} m³</td>
                <td class="font-mono ${r.unmet_demand > 0 ? 'text-danger' : 'text-muted'}">${r.unmet_demand} m³</td>
                <td class="font-mono text-muted">₹${Number(r.total_cost).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}</td>
                <td class="font-mono fw-bold text-success">₹${Number(r.net_return).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}</td>
                <td class="font-mono">${r.fairness_index}</td>
                <td>
                    <div class="btn-group btn-group-sm">
                        <a href="/api/reports/export/${r.id}?format=csv" class="btn btn-outline-secondary btn-sm font-mono py-0">CSV</a>
                        <a href="/api/reports/export/${r.id}?format=json" class="btn btn-outline-secondary btn-sm font-mono py-0">JSON</a>
                    </div>
                </td>
            </tr>
        `;
    });

    tbody.innerHTML = html;
}

// =============================================================================
// Drought Sensitivity Curve Chart
// =============================================================================
function loadDroughtSimulationData() {
    const farmId = window.cropflowData.farmId;
    fetch('/api/simulate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ farm_id: farmId })
    })
    .then(r => r.json())
    .then(data => {
        if (!data.chart_series) return;
        renderDroughtCurve(data.chart_series);
    })
    .catch(err => console.error("Error loading drought curves:", err));
}

function renderDroughtCurve(series) {
    const ctx = document.getElementById("droughtCurveChart");
    if (!ctx) return;

    if (droughtCurveChart) {
        droughtCurveChart.destroy();
    }

    droughtCurveChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: series.labels,
            datasets: [
                {
                    label: 'Greedy (₹)',
                    data: series.greedy_benefits,
                    borderColor: 'rgba(245, 158, 11, 1)',
                    backgroundColor: 'rgba(245, 158, 11, 0.1)',
                    borderWidth: 2,
                    tension: 0.3,
                    fill: false
                },
                {
                    label: 'Dynamic Prog (₹)',
                    data: series.dp_benefits,
                    borderColor: 'rgba(14, 165, 233, 1)',
                    backgroundColor: 'rgba(14, 165, 233, 0.1)',
                    borderWidth: 2,
                    tension: 0.3,
                    fill: false
                },
                {
                    label: 'Hybrid (₹)',
                    data: series.hybrid_benefits,
                    borderColor: 'rgba(16, 185, 129, 1)',
                    backgroundColor: 'rgba(16, 185, 129, 0.15)',
                    borderWidth: 3,
                    tension: 0.3,
                    fill: true
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'top', labels: { boxWidth: 12, font: { size: 10 } } },
                tooltip: {
                    callbacks: {
                        label: function (ctx) {
                            return `${ctx.dataset.label}: ₹${Number(ctx.raw).toLocaleString()}`;
                        }
                    }
                }
            },
            scales: {
                x: { grid: { display: false } },
                y: {
                    title: { display: true, text: 'Preserved Yield (₹)', font: { size: 10, weight: 'bold' } },
                    grid: { color: 'rgba(0, 0, 0, 0.04)' }
                }
            }
        }
    });
}

// =============================================================================
// Feature 12: Helpful validation errors and dismissible alert banners
// =============================================================================
function showDynamicAlert(message, type = 'info') {
    const container = document.getElementById("dynamicAlertContainer");
    if (!container) return;

    const alertHtml = `
        <div class="alert alert-${type} alert-dismissible fade show shadow-sm d-flex align-items-center gap-2 mb-0" role="alert">
            <i class="bi ${type === 'danger' ? 'bi-exclamation-triangle-fill' : type === 'success' ? 'bi-check-circle-fill' : 'bi-info-circle-fill'}"></i>
            <div>${message}</div>
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        </div>
    `;
    container.innerHTML = alertHtml;
    container.classList.remove("d-none");

    setTimeout(() => {
        const alertEl = container.querySelector(".alert");
        if (alertEl) {
            alertEl.classList.remove("show");
            setTimeout(() => container.classList.add("d-none"), 300);
        }
    }, 6000);
}
