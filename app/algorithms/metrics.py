"""Metrics and evaluation utilities for irrigation optimization algorithms.

Provides standardized calculations for water utilization, unmet demand,
preserved yield benefits, irrigation costs, and Jain's fairness index.
"""

from typing import Dict, List, Tuple
from app.models.farm import Plot
from app.models.result import AllocationItem, OptimizationResult


def calculate_jain_fairness(allocations: List[float], demands: List[float]) -> float:
    """Compute Jain's Fairness Index across plot coverage ratios.

    J(x) = (sum(x_i))^2 / (n * sum(x_i^2))
    where x_i = allocated / demand (clamped [0, 1]).
    Returns value between 0.0 and 1.0 (1.0 = completely fair proportional sharing).
    """
    if not allocations or not demands:
        return 1.0

    ratios = []
    for alloc, dem in zip(allocations, demands):
        if dem > 0:
            ratios.append(min(1.0, max(0.0, alloc / dem)))
        else:
            ratios.append(1.0)

    n = len(ratios)
    if n == 0:
        return 1.0

    sum_r = sum(ratios)
    if sum_r == 0:
        return 1.0  # Evenly starved is mathematically treated as balanced zero-allocation

    sum_sq = sum(r * r for r in ratios)
    if sum_sq == 0:
        return 1.0

    fairness = (sum_r ** 2) / (n * sum_sq)
    return round(min(1.0, max(0.0, fairness)), 4)


def calculate_water_utilization(total_allocated: float, available_water: float) -> float:
    """Calculate the percentage of available water budget actually utilized."""
    if available_water <= 0:
        return 100.0 if total_allocated == 0 else 0.0
    return round(min(100.0, max(0.0, (total_allocated / available_water) * 100.0)), 2)


def evaluate_allocation(
    plots: List[Plot],
    raw_allocations: Dict[int, float],
    available_water: float,
    energy_rate: float,
    labor_rate: float,
    pump_capacity: float,
    algorithm_name: str,
    scenario_name: str,
    execution_time_ms: float,
) -> OptimizationResult:
    """Build a comprehensive OptimizationResult from raw plot allocations."""
    total_demand = sum(p.water_demand for p in plots)
    total_allocated = 0.0
    total_cost = 0.0
    total_benefit = 0.0
    allocation_items: List[AllocationItem] = []

    alloc_list = []
    demand_list = []

    for idx, plot in enumerate(plots):
        plot_key = plot.id if plot.id is not None else idx
        allocated = raw_allocations.get(plot_key, 0.0)
        # Never exceed plot demand or negative
        allocated = max(0.0, min(plot.water_demand, allocated))

        total_allocated += allocated
        unmet = max(0.0, round(plot.water_demand - allocated, 2))
        cov_pct = round((allocated / plot.water_demand * 100.0) if plot.water_demand > 0 else 100.0, 2)
        yield_pct = plot.calculate_yield_response(allocated)
        cost = plot.calculate_irrigation_cost(allocated, energy_rate, labor_rate, pump_capacity)

        # Benefit = preserved fraction of total crop value
        preserved_val = round((yield_pct / 100.0) * plot.total_potential_value, 2)

        total_cost += cost
        total_benefit += preserved_val

        alloc_list.append(allocated)
        demand_list.append(plot.water_demand)

        allocation_items.append(
            AllocationItem(
                plot_id=plot.id,
                plot_name=plot.name,
                crop_type=plot.crop_type,
                demand=round(plot.water_demand, 2),
                allocated_water=round(allocated, 2),
                unmet_demand=unmet,
                coverage_pct=cov_pct,
                yield_preservation_pct=yield_pct,
                preserved_value=preserved_val,
                cost=cost,
                urgency_score=plot.urgency_score,
            )
        )

    total_allocated = round(total_allocated, 2)
    unmet_total = max(0.0, round(total_demand - total_allocated, 2))
    utilization = calculate_water_utilization(total_allocated, available_water)
    net_return = round(total_benefit - total_cost, 2)
    fairness = calculate_jain_fairness(alloc_list, demand_list)

    return OptimizationResult(
        algorithm=algorithm_name,
        scenario_name=scenario_name,
        available_water=round(available_water, 2),
        total_demand=round(total_demand, 2),
        total_allocated=total_allocated,
        unmet_demand=unmet_total,
        water_utilization_pct=utilization,
        total_cost=round(total_cost, 2),
        total_benefit=round(total_benefit, 2),
        net_return=net_return,
        execution_time_ms=round(execution_time_ms, 3),
        fairness_index=fairness,
        allocations=allocation_items,
    )
