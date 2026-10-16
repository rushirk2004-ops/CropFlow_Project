"""Drought scenario simulation and multi-strategy benchmarking service."""

from typing import Any, Dict, List
from app.algorithms.dynamic_programming import run_dp_allocation
from app.algorithms.greedy import run_greedy_allocation
from app.algorithms.hybrid import run_hybrid_allocation
from app.models.farm import Farm
from app.models.result import OptimizationResult, StrategyComparison
from app.services.scheduler import build_irrigation_schedule

DROUGHT_LEVELS = [
    {"name": "Normal Supply", "factor": 1.00, "description": "100% normal water budget available"},
    {"name": "Mild Deficit", "factor": 0.75, "description": "25% water restriction applied"},
    {"name": "Moderate Drought", "factor": 0.50, "description": "50% water shortage scenario"},
    {"name": "Severe Drought", "factor": 0.25, "description": "Critical 75% water curtailment"},
    {"name": "Emergency Drought", "factor": 0.10, "description": "Emergency survival water supply (10%)"},
]


def compare_strategies(
    farm: Farm,
    water_override: float = None,
    scenario_name: str = "Standard",
) -> StrategyComparison:
    """Run Greedy, Dynamic Programming, and Hybrid allocations side-by-side on the farm."""
    avail_water = water_override if water_override is not None else farm.water_budget

    res_greedy = run_greedy_allocation(
        plots=farm.plots,
        available_water=avail_water,
        energy_rate=farm.energy_rate,
        labor_rate=farm.labor_rate,
        pump_capacity=farm.pump_capacity,
        scenario_name=scenario_name,
    )
    res_greedy = build_irrigation_schedule(res_greedy, farm)

    res_dp = run_dp_allocation(
        plots=farm.plots,
        available_water=avail_water,
        energy_rate=farm.energy_rate,
        labor_rate=farm.labor_rate,
        pump_capacity=farm.pump_capacity,
        scenario_name=scenario_name,
    )
    res_dp = build_irrigation_schedule(res_dp, farm)

    res_hybrid = run_hybrid_allocation(
        plots=farm.plots,
        available_water=avail_water,
        energy_rate=farm.energy_rate,
        labor_rate=farm.labor_rate,
        pump_capacity=farm.pump_capacity,
        scenario_name=scenario_name,
    )
    res_hybrid = build_irrigation_schedule(res_hybrid, farm)

    results_map = {
        "greedy": res_greedy,
        "dynamic_programming": res_dp,
        "hybrid": res_hybrid,
    }

    # Determine winners
    winner_yield = max(results_map.keys(), key=lambda k: results_map[k].total_benefit)
    winner_net = max(results_map.keys(), key=lambda k: results_map[k].net_return)
    winner_fairness = max(results_map.keys(), key=lambda k: results_map[k].fairness_index)

    # Formulate insights
    insights = []
    water_deficit = max(0.0, farm.total_demand - avail_water)
    if water_deficit > 0:
        yield_diff = res_hybrid.total_benefit - res_greedy.total_benefit
        if yield_diff > 0:
            insights.append(
                f"Hybrid strategy preserves ${yield_diff:,.2f} more crop yield than Greedy by avoiding complete starvation of sensitive plots."
            )
        else:
            insights.append("Greedy focused all limited water on top-urgency crops.")

        fairness_diff = res_hybrid.fairness_index - res_greedy.fairness_index
        if fairness_diff > 0.1:
            insights.append(
                f"Hybrid significantly improves water equity across plots (Jain index: {res_hybrid.fairness_index:.2f} vs Greedy {res_greedy.fairness_index:.2f})."
            )
    else:
        insights.append("Water supply is sufficient to cover 100% of all plot irrigation demands.")

    return StrategyComparison(
        scenario=scenario_name,
        available_water=round(avail_water, 2),
        total_demand=farm.total_demand,
        results=results_map,
        winner_yield=winner_yield,
        winner_net_return=winner_net,
        winner_fairness=winner_fairness,
        insights=insights,
    )


def run_drought_simulation(farm: Farm) -> Dict[str, Any]:
    """Execute all drought tiers across all 3 algorithms to generate comparative curve data."""
    base_budget = farm.water_budget
    scenarios_data = []

    for level in DROUGHT_LEVELS:
        tier_water = round(base_budget * level["factor"], 2)
        comp = compare_strategies(farm, water_override=tier_water, scenario_name=level["name"])

        scenarios_data.append({
            "name": level["name"],
            "factor_pct": int(level["factor"] * 100),
            "available_water": tier_water,
            "description": level["description"],
            "comparison": comp.to_dict(),
        })

    # Summary curve points for Chart.js
    chart_series = {
        "labels": [s["name"] for s in scenarios_data],
        "greedy_benefits": [s["comparison"]["results"]["greedy"]["total_benefit"] for s in scenarios_data],
        "dp_benefits": [s["comparison"]["results"]["dynamic_programming"]["total_benefit"] for s in scenarios_data],
        "hybrid_benefits": [s["comparison"]["results"]["hybrid"]["total_benefit"] for s in scenarios_data],
        "greedy_fairness": [s["comparison"]["results"]["greedy"]["fairness_index"] for s in scenarios_data],
        "dp_fairness": [s["comparison"]["results"]["dynamic_programming"]["fairness_index"] for s in scenarios_data],
        "hybrid_fairness": [s["comparison"]["results"]["hybrid"]["fairness_index"] for s in scenarios_data],
    }

    return {
        "farm_id": farm.id,
        "farm_name": farm.name,
        "base_budget": base_budget,
        "scenarios": scenarios_data,
        "chart_series": chart_series,
    }
