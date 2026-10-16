"""Empirical benchmarking experiment script for CropFlow.

Runs Greedy, Dynamic Programming, and Hybrid algorithms across:
- Increasing plot scales: N = 4, 8, 16, 32 plots
- Varying water capacities: 25%, 50%, 75%, 100% of total demand

Measures and outputs real metrics:
- Execution Time (ms)
- Objective Value ($)
- Unmet Demand (m3)
- Water Utilization (%)
- Estimated Irrigation Cost ($)
"""

import time
from typing import Any, Dict, List
from app.algorithms.dynamic_programming import dp_allocate_pure
from app.algorithms.greedy import greedy_allocate_pure
from app.algorithms.hybrid import hybrid_allocate_pure

CROPS_POOL = [
    {"name": "Corn", "val": 2400.0, "ky": 1.40, "prio": 5, "stress": 0.80, "demand": 120.0},
    {"name": "Tomato", "val": 4200.0, "ky": 1.35, "prio": 5, "stress": 0.75, "demand": 90.0},
    {"name": "Potato", "val": 2100.0, "ky": 0.95, "prio": 4, "stress": 0.60, "demand": 100.0},
    {"name": "Wheat", "val": 1600.0, "ky": 0.85, "prio": 3, "stress": 0.45, "demand": 110.0},
    {"name": "Cotton", "val": 1800.0, "ky": 0.70, "prio": 2, "stress": 0.35, "demand": 80.0},
    {"name": "Soybean", "val": 1300.0, "ky": 0.60, "prio": 2, "stress": 0.30, "demand": 70.0},
]


def generate_benchmark_plots(n: int) -> List[Dict[str, Any]]:
    """Synthesize n realistic agricultural plots from standard crop pool."""
    plots = []
    for i in range(n):
        template = CROPS_POOL[i % len(CROPS_POOL)]
        plots.append({
            "plot_identifier": f"P-{i+1:02d}",
            "name": f"Plot {i+1} {template['name']}",
            "remaining_demand": template["demand"],
            "crop_value": template["val"] * 2.0,  # 2 ha baseline
            "sensitivity_factor": template["ky"],
            "priority": template["prio"],
            "moisture_stress": template["stress"],
            "cost_per_unit": 0.045,
        })
    return plots


def run_benchmark_experiments():
    """Execute multi-scale empirical benchmark."""
    plot_scales = [4, 8, 16, 32]
    water_ratios = [0.25, 0.50, 0.75, 1.00]

    results_table = []

    print("\n" + "=" * 110)
    print("CROPFLOW EMPIRICAL BENCHMARK EXPERIMENT RESULTS (ACTUAL MEASURED DATA)")
    print("=" * 110)
    print(f"{'N':<4} | {'Water Tier':<12} | {'Budget':<8} | {'Algorithm':<20} | {'Runtime (ms)':<14} | {'Objective ($)':<14} | {'Unmet (m³)':<12} | {'Util (%)':<9} | {'Cost ($)':<9}")
    print("-" * 110)

    for n in plot_scales:
        plots = generate_benchmark_plots(n)
        tot_demand = sum(p["remaining_demand"] for p in plots)

        for ratio in water_ratios:
            tier_name = f"{int(ratio * 100)}% Supply"
            budget = round(tot_demand * ratio, 1)

            # 1. Greedy
            t0 = time.perf_counter()
            g_res = greedy_allocate_pure(plots, budget)
            g_time = (time.perf_counter() - t0) * 1000.0
            # Objective under standard utility
            from app.algorithms.dynamic_programming import calculate_plot_utility
            g_obj = round(sum(
                calculate_plot_utility(a.allocated_water, a.remaining_demand, p["crop_value"], p["sensitivity_factor"], p["priority"], p["cost_per_unit"])[0]
                for a, p in zip(g_res.allocations, plots)
            ), 2)

            # 2. Dynamic Programming
            t0 = time.perf_counter()
            dp_res = dp_allocate_pure(plots, budget, max_discrete_steps=60)
            dp_time = (time.perf_counter() - t0) * 1000.0

            # 3. Hybrid
            t0 = time.perf_counter()
            h_res = hybrid_allocate_pure(plots, budget, step_count=60)
            h_time = (time.perf_counter() - t0) * 1000.0

            for alg_name, runtime, obj, unmet, util, cost in [
                ("Greedy", g_time, g_obj, g_res.unmet_demand, g_res.water_utilization_pct, g_res.total_cost),
                ("Dynamic Programming", dp_time, dp_res.objective_value, dp_res.unmet_demand, dp_res.water_utilization_pct, dp_res.total_cost),
                ("Hybrid (Proposed)", h_time, h_res.final_objective, h_res.unmet_demand, h_res.water_utilization_pct, h_res.total_cost),
            ]:
                print(f"{n:<4} | {tier_name:<12} | {budget:<8} | {alg_name:<20} | {runtime:<14.2f} | {obj:<14.2f} | {unmet:<12.1f} | {util:<9.1f} | {cost:<9.2f}")
                results_table.append({
                    "n": n,
                    "tier": tier_name,
                    "budget": budget,
                    "algorithm": alg_name,
                    "runtime_ms": round(runtime, 2),
                    "objective_val": obj,
                    "unmet_m3": unmet,
                    "utilization_pct": util,
                    "cost": cost,
                })
            print("-" * 110)

    return results_table


if __name__ == "__main__":
    run_benchmark_experiments()
