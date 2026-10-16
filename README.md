# CropFlow &mdash; Optimal Irrigation Scheduling with Limited Water

CropFlow is an agronomic decision-support and optimization web application built with **Python 3, Flask, SQLite, HTML5, CSS3, JavaScript, Bootstrap 5, and Chart.js**.

The primary objective is solving the agricultural water allocation problem under water scarcity and drought conditions. CropFlow implements, benchmarks, and combines **Greedy Urgency Triage**, **Dynamic Programming (Multiple-Choice Knapsack)**, and a **Two-Stage Hybrid Optimization Strategy** to generate actionable, infiltration-safe, cost-minimizing irrigation pump schedules.

---

## 🏛 System Architecture

CropFlow follows a modular 5-tier architecture separating optimization algorithms from database persistence and presentation:

```text
 1. Input Layer (Data Collection & Preprocessing)
    ├── Crop Metrics: Growth stage, FAO-33 sensitivity factor (Ky), market potential value ($/ha)
    ├── Soil Physics: Moisture %, permanent wilting point, field capacity, infiltration rate (mm/h)
    ├── Water Constraints: Total available water budget (m³ or Liters), drought curtailment factor
    ├── Economic Drivers: Off-peak/peak pumping energy tariffs ($/m³), labor wages ($/h)
    └── Farm Geometry: Plot areas (ha), unique identifiers (P-101), farmer priority ratings (1-5)
                 │
                 ▼
 2. Service & Validation Layer (app/services/)
    ├── Preprocessing & Validation (preprocessing.py):
    │   ├── Rejects negative numeric values and out-of-bounds soil moisture (< 0% or > 100%)
    │   ├── Enforces plot identifier uniqueness within each farm
    │   └── Imputes root-zone soil moisture deficit into net water demand Di
    ├── Drought Scenario Simulation (simulation.py):
    │   └── Models 5 supply tiers: 100% (Normal), 75% (Mild), 50% (Moderate), 25% (Severe), 10% (Emergency)
    └── Irrigation Scheduling Module (scheduler.py):
        ├── Enforces plot infiltration rate intake limits: Qi <= InfiltrationRate * Area * 10
        ├── Respects pump flow capacity limits: Qi <= PumpCapacity
        └── Schedules sequential non-overlapping windows to exploit off-peak power tariffs (20:00 - 08:00)
                 │
                 ▼
 3. Algorithmic Optimization Layer (app/algorithms/)
    ├── Greedy Allocation (greedy.py):
    │   └── Deterministic O(N log N) priority triage allocating full water to highest-urgency plots
    ├── Dynamic Programming (dynamic_programming.py):
    │   └── Discretized Bellman knapsack finding global optimum across concave FAO-33 yield curves
    └── Hybrid Allocation Strategy (hybrid.py):
        └── Two-stage architecture: anchors baseline survival water, refines residual via DP,
            performs local delta transfers, and enforces non-regression (J_hybrid >= J_greedy)
                 │
        ┌────────┴────────┐
        ▼                 ▼
 4. Persistence Layer (SQLite)   5. UI & Presentation Layer
    ├── database/schema.sql          ├── Modern agriculture-themed sidebar navigation
    ├── database/db.py               ├── 4 Summary KPI metric cards (Available, Allocated, Util %, Cost)
    │   ├── farms                    ├── Live Execution Time benchmarking (Greedy, DP, Hybrid)
    │   ├── plots                    ├── Chart.js visualizations (Allocation bar, Multi-metric, Curves)
    │   ├── optimization_runs        ├── Interactive Drought Scenario Simulator slider
    │   ├── allocations              ├── Detailed Plot Demand, Allocation & Unmet table
    │   └── scenario_settings        ├── "Run All 3 Algorithms" benchmark trigger
                                     └── Results history audit view with CSV & JSON exports
```

---

## 📁 Repository Directory Structure

```text
cropFlow/
│
├── app/
│   ├── __init__.py              # Application factory (create_app), auto-initialization, error handlers
│   │
│   ├── routes/
│   │   ├── __init__.py          # Exports dashboard_bp, farms_bp, optimization_bp, reports_bp
│   │   ├── dashboard.py         # Dashboard view, health-check endpoint (/health, /api/health)
│   │   ├── farms.py             # Farm and plot CRUD, validation rules, SQLite data collection
│   │   ├── optimization.py      # Execution endpoints (/api/optimize, /api/simulate, algorithms metadata)
│   │   └── reports.py           # Historical runs audit, run comparison (/api/reports/compare-runs), CSV/JSON export
│   │
│   ├── algorithms/
│   │   ├── __init__.py          # Exports solvers and metrics evaluation functions
│   │   ├── greedy.py            # O(N log N) greedy priority triage with deterministic tie-breaking
│   │   ├── dynamic_programming.py # O(N*C*K) multiple-choice discrete resource allocation knapsack
│   │   ├── hybrid.py            # Combined strategy: survival anchoring + residual DP + local search
│   │   └── metrics.py           # Standardized evaluation: utilization, cost, yield value, Jain's fairness
│   │
│   ├── services/
│   │   ├── __init__.py          # Exports preprocessing, scheduler, and simulation utilities
│   │   ├── preprocessing.py     # Input validation, non-negativity checks, water demand calculation
│   │   ├── scheduler.py         # Hourly non-overlapping pump schedule with infiltration & tariff limits
│   │   └── simulation.py        # Multi-strategy comparison and 5-tier drought simulation curves
│   │
│   ├── models/
│   │   ├── __init__.py          # Exports Farm, Plot, AllocationItem, OptimizationResult, ScheduleItem
│   │   ├── farm.py              # Domain models for Farm and Plot with FAO-33 yield response
│   │   └── result.py            # Dataclasses for optimization outputs, schedules, and comparisons
│   │
│   ├── templates/
│   │   ├── base.html            # Agriculture-themed base layout with responsive sidebar and topbar
│   │   ├── index.html           # System overview and architectural layer explanation
│   │   ├── dashboard.html       # Command dashboard with KPI cards, Chart.js, drought simulator, tables
│   │   ├── farms.html           # Farm profile and plot configuration forms with live validation
│   │   └── results.html         # Comparative strategy cards, plot breakdown, schedule, audit log
│   │
│   └── static/
│       ├── css/
│       │   └── style.css        # Agriculture theme CSS (emerald accents, dark forest sidebar, KPI cards)
│       └── js/
│           ├── dashboard.js     # Chart.js controllers, drought slider, run-all action, dynamic table updates
│           └── farm-form.js     # Responsive farm/plot input validation and live demand preview
│
├── database/
│   ├── __init__.py              # Database package initializer
│   ├── db.py                    # SQLite connection helpers, schema auto-migration, sample data seeder
│   └── schema.sql               # DDL schema: farms, plots, optimization_runs, allocations, scenario_settings
│
├── tests/
│   ├── __init__.py              # Test suite package initializer
│   ├── test_audit.py            # Physical invariants, edge cases (W=0, abundant W, Di=0), DP optimality
│   ├── test_greedy.py           # Unit tests for greedy allocation, tie-breaking, worked numerical example
│   ├── test_dp.py               # Unit tests for DP knapsack recurrence, quantum discretization, capacity
│   ├── test_hybrid.py           # Tests for hybrid refinement, survival anchoring, non-regression property
│   ├── test_constraints.py     # Verification of water budget limits, non-negativity, and soil infiltration
│   ├── test_comparison.py      # Multi-algorithm benchmark comparison and API health endpoint tests
│   ├── test_dashboard_ui.py     # HTML contracts, dashboard feature verification, API exports (CSV/JSON)
│   ├── test_preprocessing.py    # Validation rules, non-negativity, soil moisture bounds, plot ID uniqueness
│   └── run_experiments.py       # Multi-scale empirical benchmarking script (N=4..32, water tiers 25%..100%)
│
├── run.py                       # Local application runner
├── config.py                    # Config profiles (Development, Testing, Production) using os.getenv
├── requirements.txt             # Python dependencies (Flask, etc.)
├── .env.example                 # Example environment variables template
├── .gitignore                   # Git exclusion rules
└── README.md                    # Project documentation
```

---

## 🗄 Database Schema & Backend Persistence

The application uses SQLite with foreign key enforcement (`PRAGMA foreign_keys = ON;`) and automatic schema migration:

1. **`farms`**: Stores farm properties, reservoir capacity ($m^3$), pumping energy rates ($/m³), labor wages ($/h), and pump flow capacity ($m^3/h$).
2. **`plots`**: Stores agricultural plots associated with a farm. Enforces `UNIQUE(farm_id, plot_identifier)`. Captures plot area (ha), crop type, growth stage, soil type, infiltration rate (mm/h), soil moisture (0-100%), wilting point, priority (1-5), and computed water demand.
3. **`optimization_runs`**: Persists optimization metadata including algorithm name, scenario name, water budget, total allocated, unmet demand, water utilization %, total cost, total benefit, net return, standardized `objective_value`, input parameters JSON (`parameters_json`), execution time (ms), and Jain's fairness index.
4. **`allocations`**: Stores per-plot allocation details linked to an optimization run (`FOREIGN KEY (run_id) REFERENCES optimization_runs(id)`), including allocated water volume, demand coverage %, yield preservation %, cost, scheduled start hour, duration, and flow rate.
5. **`scenario_settings`**: Stores drought curtailment scenarios (Normal 100%, Mild 75%, Moderate 50%, Severe 25%, Emergency 10%) with water and tariff overrides.

All database queries utilize parameterized SQL statements (`?` placeholders) to prevent SQL injection vulnerabilities.

---

## 🧮 Optimization Algorithms & Mathematical Formulations

### 1. Standardized Net Objective Function
All three strategies are evaluated under the standardized agronomic objective function:

$$\max \sum_{i=1}^N U_i(w_i)$$

Where the net utility $U_i(w_i)$ of allocating $w_i$ water to plot $i$ with demand $D_i$ is:

$$U_i(w_i) = \left[ \omega(\text{Priority}_i) \times Y_{\text{ratio}}(w_i) \times \text{CropValue}_i \right] - \text{Penalty}_i(w_i) - \text{Cost}_i(w_i)$$

- **FAO-33 Yield Response Ratio**:
  $$Y_{\text{ratio}}(w_i) = \max\left(0, 1 - K_{y,i} \times \left(1 - \frac{w_i}{D_i}\right)\right)$$
- **Priority Scaling**: $\omega(\text{Priority}_i) = 0.70 + 0.10 \times \text{Priority}_i \in [0.80, 1.20]$.
- **Critical Unmet Demand Penalty**:
  $$\text{Penalty}_i(w_i) = \lambda \times \max(0.5, K_{y,i}) \times \left(1 - \frac{w_i}{D_i}\right)^2 \times \text{CropValue}_i \quad (\lambda = 0.20)$$
- **Irrigation Pumping Cost**: $\text{Cost}_i(w_i) = w_i \times \text{CostPerUnit}_i$.

---

### 2. Strategy 1: Greedy Priority Allocation ([`app/algorithms/greedy.py`](file:///d:/cropFlow/app/algorithms/greedy.py))
- **Formulation**: Calculates a composite urgency index:
  $$\text{Urgency}_i = 0.35 \times S_{\text{stress}} + 0.25 \times \frac{K_{y,i}}{1.5} + 0.25 \times \frac{\text{Priority}_i}{5} + 0.15 \times V_{\text{norm}}$$
  $$\text{Score}_i = \frac{\text{Urgency}_i}{\max(0.0001, \text{CostPerUnit}_i)}$$
- **Deterministic 3-Tier Tie-Breaking**:
  1. Priority Score descending (`-score`)
  2. Remaining demand ascending (`demand` &mdash; satisfies smaller plots first to increase coverage)
  3. Plot identifier ascending (`plot_identifier` &mdash; lexicographical reproducibility)
- **Time Complexity**: $\mathcal{O}(N \log N)$ via Timsort priority ranking.
- **Space Complexity**: $\mathcal{O}(N)$ auxiliary space for ranking maps.
- **Limitations**: Greedy makes irrevocable, myopic choices. It can allocate 100% of available water to an early high-demand plot, completely starving lower-ranked plots and causing high crop mortality.

---

### 3. Strategy 2: Dynamic Programming Resource Allocation ([`app/algorithms/dynamic_programming.py`](file:///d:/cropFlow/app/algorithms/dynamic_programming.py))
- **Formulation**: Modeled as a Multiple-Choice Knapsack problem. Water capacity is discretized into increments of quantum unit $\Delta_w$ (e.g. 10.0 L or 1.0 $m^3$):
  $$C = \left\lfloor \frac{W_{\text{available}}}{\Delta_w} \right\rfloor$$
- **Candidate Choices**: For plot $i$, candidate choices are $k \in \{0, 1, \dots, K_i\}$ where $w_{i,k} = \min(D_i, k \times \Delta_w)$.
- **Bellman Recurrence Relation**:
  $$\text{DP}[i][c] = \max_{k \le c} \left\{ \text{DP}[i-1][c - k] + U_i(w_{i,k}) \right\}$$
- **Reconstruction**: Backtrack pointer table reconstructs optimal allocations $w_i^*$.
- **Time Complexity**: $\mathcal{O}(N \cdot C \cdot K)$ pseudo-polynomial time.
- **Space Complexity**: $\mathcal{O}(N \cdot C)$ for the 2D DP state table and backtrack pointers.
- **Optimality**: Mathematically proven to achieve the global optimum on the defined discretized state space. Quantization error is bounded by $\mathcal{O}(\Delta_w)$.

---

### 4. Strategy 3: Hybrid Allocation Strategy ([`app/algorithms/hybrid.py`](file:///d:/cropFlow/app/algorithms/hybrid.py))
- **Phase 1 (Greedy Baseline)**: Computes initial feasible allocation $\mathbf{w}^{\text{greedy}}$ and records baseline objective $J_{\text{initial}} = \sum U_i(w_i^g)$.
- **Phase 2 (Incorporation into Refinement)**:
  - **Survival Anchoring**: Plots with high stress ($\ge 0.5$) or critical sensitivity ($K_y \ge 1.0$) are guaranteed baseline survival water $b_i = \min(w_i^g, \text{target}_i)$ (e.g. 30% of demand).
  - **Residual DP**: Discretized DP distributes residual water $W_{\text{rem}} = W_{\text{available}} - \sum b_i$ over remaining demands $(D_i - b_i)$.
  - **Neighborhood Delta Transfer**: Iteratively checks if shifting a fine quantum $\delta$ from plot $j$ to plot $i$ increases aggregate utility $\Delta U > 0$.
- **Phase 3 (Non-Regression Safety Gate)**:
  Evaluates candidate solution $\mathbf{w}^{\text{refined}}$ under the identical objective function:
  $$\mathbf{w}^{\text{final}} = \begin{cases} \mathbf{w}^{\text{refined}} & \text{if } J_{\text{refined}} \ge J_{\text{initial}} \\ \mathbf{w}^{\text{greedy}} & \text{otherwise} \end{cases}$$
  This guarantees the non-regression invariant: $J_{\text{final}} = \max(J_{\text{initial}}, J_{\text{refined}}) \ge J_{\text{initial}}$.
- **Time Complexity**: $\mathcal{O}(N \log N + N \cdot C \cdot K + L \cdot N^2)$.
- **Space Complexity**: $\mathcal{O}(N \cdot C)$.
- **Disclaimer**: Hybrid incurs both the runtime of the initial Greedy pass and the subsequent refinement passes; it is not claimed to be strictly faster than standalone Greedy without empirical qualification.

---

## 📊 Empirical Benchmark Experiment Results

Actual measured data obtained from running [`tests/run_experiments.py`](file:///d:/cropFlow/tests/run_experiments.py) across increasing scales of plots ($N = 4, 8, 16, 32$) and water supply tiers ($25\%, 50\%, 75\%, 100\%$):

| Plots ($N$) | Water Supply Tier | Budget ($m^3$) | Algorithm | Runtime (ms) | Objective ($) | Unmet Demand ($m^3$) | Water Util (%) | Irrigation Cost ($) |
|---|---|---|---|---|---|---|---|---|
| **4** | 25% Supply | 105.0 | Greedy | 0.05 | 1,827.27 | 315.0 | 100.0% | $4.72 |
| **4** | 25% Supply | 105.0 | Dynamic Programming | 1.38 | 8,922.58 | 316.0 | 99.0% | $4.68 |
| **4** | 25% Supply | 105.0 | Hybrid (Proposed) | 2.13 | 2,247.37 | 315.0 | 100.0% | $4.73 |
| **4** | 50% Supply | 210.0 | Greedy | 0.03 | 15,199.55 | 210.0 | 100.0% | $9.45 |
| **4** | 50% Supply | 210.0 | Dynamic Programming | 0.82 | 15,132.30 | 211.0 | 99.5% | $9.40 |
| **4** | 50% Supply | 210.0 | Hybrid (Proposed) | 2.67 | 15,199.55 | 210.0 | 100.0% | $9.45 |
| **4** | 100% Supply | 420.0 | Greedy | 0.02 | 23,641.10 | 0.0 | 100.0% | $18.90 |
| **4** | 100% Supply | 420.0 | Dynamic Programming | 0.45 | 23,485.84 | 3.0 | 99.3% | $18.76 |
| **4** | 100% Supply | 420.0 | Hybrid (Proposed) | 0.52 | 23,641.10 | 0.0 | 100.0% | $18.90 |
| **8** | 50% Supply | 390.0 | Greedy | 0.05 | 27,335.45 | 390.0 | 100.0% | $17.55 |
| **8** | 50% Supply | 390.0 | Dynamic Programming | 0.97 | 29,925.35 | 392.0 | 99.5% | $17.46 |
| **8** | 50% Supply | 390.0 | Hybrid (Proposed) | 7.37 | 29,443.91 | 390.0 | 100.0% | $17.54 |
| **16** | 50% Supply | 780.0 | Greedy | 0.08 | 55,755.90 | 780.0 | 100.0% | $35.10 |
| **16** | 50% Supply | 780.0 | Dynamic Programming | 1.26 | 55,857.98 | 783.0 | 99.6% | $34.95 |
| **16** | 50% Supply | 780.0 | Hybrid (Proposed) | 23.84 | 55,755.90 | 780.0 | 100.0% | $35.10 |
| **32** | 25% Supply | 765.0 | Greedy | 0.11 | 28,199.58 | 2,295.0 | 100.0% | $34.42 |
| **32** | 25% Supply | 765.0 | Dynamic Programming | 2.42 | 67,502.48 | 2,295.0 | 100.0% | $34.44 |
| **32** | 25% Supply | 765.0 | Hybrid (Proposed) | 164.82 | 28,199.58 | 2,295.0 | 100.0% | $34.42 |
| **32** | 75% Supply | 2295.0 | Greedy | 0.12 | 139,115.70 | 765.0 | 100.0% | $103.27 |
| **32** | 75% Supply | 2295.0 | Dynamic Programming | 1.20 | 134,103.96 | 913.5 | 93.5% | $96.54 |
| **32** | 75% Supply | 2295.0 | Hybrid (Proposed) | 22.55 | 139,115.70 | 765.0 | 100.0% | $103.27 |
| **32** | 100% Supply | 3060.0 | Greedy | 0.14 | 161,902.30 | 0.0 | 100.0% | $137.70 |
| **32** | 100% Supply | 3060.0 | Dynamic Programming | 1.04 | 154,449.17 | 280.0 | 90.8% | $125.05 |
| **32** | 100% Supply | 3060.0 | Hybrid (Proposed) | 3.08 | 161,902.30 | 0.0 | 100.0% | $137.70 |

---

## 🛡 Invariant Guarantees Verified by Tests

For every execution across all 3 algorithms, CropFlow enforces and verifies:

1. **Total Water Budget Invariant**:
   $$\sum_{i=1}^N w_i \le W_{\text{available}}$$
2. **Individual Plot Feasibility Invariant**:
   $$0 \le w_i \le D_i \quad \forall i \in \{1, \dots, N\}$$
3. **Soil Infiltration Runoff Prevention**:
   $$Q_i \le \text{InfiltrationRate}_i \times \text{Area}_i \times 10 \quad (m^3/\text{hr})$$
4. **Pump Limit**:
   $$Q_i \le C_{\text{pump}} \quad (m^3/\text{hr})$$
5. **Sequential Non-Overlapping Scheduling**:
   Total simultaneous delivery flow rate never exceeds $C_{\text{pump}}$.

---

## 💻 Exact Windows PowerShell Run Instructions

### 1. Open Terminal in Workspace Directory
```powershell
cd d:\cropFlow
```

### 2. Set Up Virtual Environment (Optional / Recommended)
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```
*(If script execution is restricted, run: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned`)*

### 3. Install Required Dependencies
```powershell
pip install -r requirements.txt
```

### 4. Run the Full Test Suite (52 Unit & Integration Tests)
```powershell
python -m unittest discover -s tests -v
```

### 5. Run the Invariant & Edge-Case Audit Suite Specifically
```powershell
python -m unittest tests/test_audit.py -v
```

### 6. Run the Multi-Scale Empirical Experiments
```powershell
python -m tests.run_experiments
```

### 7. Launch the CropFlow Web Application
```powershell
python run.py
```

Open your browser to:
- **Command Dashboard:** [http://127.0.0.1:5000/dashboard](http://127.0.0.1:5000/dashboard)
- **Farms & Plots Manager:** [http://127.0.0.1:5000/farms](http://127.0.0.1:5000/farms)
- **Results & Schedule:** [http://127.0.0.1:5000/results](http://127.0.0.1:5000/results)
- **API Health Check:** [http://127.0.0.1:5000/health](http://127.0.0.1:5000/health)

---

## 📡 REST API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | System health check, SQLite status, and algorithms list |
| `POST` | `/api/optimize` | Run Greedy, DP, or Hybrid (or all 3 via `algorithm="all"`) |
| `GET` | `/api/optimize/algorithms` | Retrieve algorithm metadata and time complexities |
| `POST` | `/api/simulate` | Run drought simulation across all 5 supply tiers |
| `GET` | `/api/farms` | List registered farms |
| `GET` | `/api/farms/<farm_id>` | Get farm details with plots |
| `POST` | `/api/farms` | Create a new farm |
| `POST` | `/api/farms/<farm_id>/plots` | Add a plot with agronomic parameters |
| `PUT` | `/api/plots/<plot_id>` | Update an existing plot |
| `DELETE` | `/api/plots/<plot_id>` | Delete a plot |
| `POST` | `/api/farms/seed` | Reset and seed the sample Greenfield Valley farm |
| `GET` | `/api/reports/history` | List historical optimization runs for a farm |
| `GET` | `/api/reports/run/<run_id>` | Retrieve detailed allocations for a saved run |
| `GET` | `/api/reports/export/<run_id>` | Export allocation report as CSV or JSON |
| `GET/POST`| `/api/reports/compare-runs` | Compare multiple historical optimization runs side-by-side |
| `GET/POST`| `/api/scenarios` | Retrieve or create scenario settings for a farm |

---

## 📸 UI Verification & Screenshot Instructions

To capture visual evidence of the running CropFlow dashboard:

1. **Irrigation Command Dashboard (`/dashboard`)**:
   - Navigate to `http://127.0.0.1:5000/dashboard`.
   - Verify the 4 KPI summary cards (*Available Water*, *Allocated Water*, *Utilization Rate*, *Estimated Cost*).
   - Capture the live **Plot Allocations Bar Chart** and **Strategy Comparison Chart**.
2. **Interactive Drought Scenario Simulator**:
   - On `/dashboard`, drag the drought slider to `50%` or click the `50%` preset button.
   - Observe the live AJAX update recalculating allocations, updating charts, and revising unmet demand metrics.
3. **"Run All 3 Algorithms" Action**:
   - Click the prominent **"Run All 3 Algorithms"** button at the top right of `/dashboard`.
   - Observe the loading spinner and subsequent execution time breakdown and updated audit table.
4. **Farm & Plot Form Manager (`/farms`)**:
   - Navigate to `http://127.0.0.1:5000/farms`.
   - Test responsive validation by entering invalid soil moisture (>100% or <0%) to observe helpful error feedback.
5. **Optimization Results & Pump Schedule (`/results`)**:
   - Navigate to `http://127.0.0.1:5000/results`.
   - Capture the side-by-side comparison cards for Greedy, Dynamic Programming, and Hybrid.
   - Capture the actionable hourly pump schedule table and historical run export buttons (`CSV` / `JSON`).
