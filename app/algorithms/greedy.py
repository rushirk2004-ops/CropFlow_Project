"""Greedy Water Allocation Algorithm for CropFlow.

This module implements a deterministic greedy heuristic for allocating limited irrigation
water among agricultural plots under water scarcity constraints.

-----------------------------------------------------------------------------------------
ALGORITHM OVERVIEW & COMPLEXITY:
-----------------------------------------------------------------------------------------
1. Complexity:
   - Time Complexity: O(N log N)
     - Score calculation: O(N)
     - Sorting N plots: O(N log N) via Timsort
     - Single-pass allocation: O(N)
     - Metrics computation: O(N)
     Total Time = O(N log N), where N is the number of plots.
   - Auxiliary Space Complexity: O(N)
     Stores score records, sorted ranking references, and output allocation maps.

2. Non-Optimality Disclaimer:
   THE GREEDY ALGORITHM IS A HEURISTIC AND DOES NOT GUARANTEE GLOBAL OPTIMALITY.
   Because it makes myopic, irrevocable choices based strictly on instantaneous marginal
   priority at each step, it may allocate full water to an early high-demand crop,
   completely starving multiple lower-ranked crops whose combined preserved yield would
   exceed the single crop's return. Dynamic Programming or Hybrid strategies should be
   utilized when optimal fractional payoff tradeoffs are required.

-----------------------------------------------------------------------------------------
PRIORITY SCORE FORMULATION & DOCUMENTED WEIGHTS:
-----------------------------------------------------------------------------------------
For each plot i:
  - P_norm = Priority / 5.0 in [0.2, 1.0] (Operational Importance)
  - S_stress in [0.0, 1.0]                (Soil Moisture Deficit Stress Index)
  - K_norm = min(1.0, Ky / 1.5)           (FAO-33 Yield Response Factor)
  - V_norm in [0.0, 1.0]                  (Normalized Economic Market Value)

Documented Component Weights (Sum = 1.00):
  - w_stress      = 0.35  (35% weight: Root-zone moisture exhaustion urgency)
  - w_sensitivity = 0.25  (25% weight: Crop growth stage sensitivity Ky, e.g. flowering)
  - w_priority    = 0.25  (25% weight: Farmer operational priority ranking)
  - w_benefit     = 0.15  (15% weight: Crop potential economic yield value)

Composite Urgency Index:
  Urgency = (w_stress * S_stress) + (w_sensitivity * K_norm) + (w_priority * P_norm) + (w_benefit * V_norm)

Final Priority Score:
  Score = Urgency / max(0.0001, Unit Irrigation Cost)

-----------------------------------------------------------------------------------------
DETERMINISTIC TIE-BREAKING RULE:
-----------------------------------------------------------------------------------------
When two or more plots have identical priority scores, ties are deterministically resolved by:
  1. Priority Score: Descending (highest score first)
  2. Remaining Water Demand: Ascending (satisfies smaller plots first to maximize plot coverage)
  3. Plot Identifier: Lexicographically Ascending (e.g. 'P-101' before 'P-102')

-----------------------------------------------------------------------------------------
WORKED NUMERICAL EXAMPLE:
-----------------------------------------------------------------------------------------
Available Water Budget: W_avail = 100.0 m3
Cost per m3: $0.05 for all plots

Plot A (P-101):
  - Demand = 60.0 m3, Priority = 5 (P_norm = 1.0), Stress = 0.8, Ky = 1.4 (K_norm = 0.9333), V_norm = 0.90
  - Urgency = 0.35(0.8) + 0.25(0.9333) + 0.25(1.0) + 0.15(0.90) = 0.2800 + 0.2333 + 0.2500 + 0.1350 = 0.8983
  - Score   = 0.8983 / 0.05 = 17.966

Plot B (P-102):
  - Demand = 50.0 m3, Priority = 3 (P_norm = 0.6), Stress = 0.5, Ky = 0.9 (K_norm = 0.6000), V_norm = 0.50
  - Urgency = 0.35(0.5) + 0.25(0.6000) + 0.25(0.6) + 0.15(0.50) = 0.1750 + 0.1500 + 0.1500 + 0.0750 = 0.5500
  - Score   = 0.5500 / 0.05 = 11.000

Plot C (P-103):
  - Demand = 40.0 m3, Priority = 2 (P_norm = 0.4), Stress = 0.3, Ky = 0.5 (K_norm = 0.3333), V_norm = 0.40
  - Urgency = 0.35(0.3) + 0.25(0.3333) + 0.25(0.4) + 0.15(0.40) = 0.1050 + 0.0833 + 0.1000 + 0.0600 = 0.3483
  - Score   = 0.3483 / 0.05 = 6.966

Ranking:
  1st: Plot A (Score: 17.966)
  2nd: Plot B (Score: 11.000)
  3rd: Plot C (Score: 6.966)

Sequential Greedy Allocation:
  - Step 1 (Plot A): Demand = 60.0 <= 100.0 => Allocated = 60.0 m3. Remaining W = 40.0 m3. Unmet = 0.0 m3.
  - Step 2 (Plot B): Demand = 50.0 > 40.0  => Allocated = 40.0 m3. Remaining W = 0.0 m3.  Unmet = 10.0 m3.
  - Step 3 (Plot C): Demand = 40.0, W = 0  => Allocated = 0.0 m3.  Remaining W = 0.0 m3.  Unmet = 40.0 m3.

Results:
  - Total Water Allocated = 100.0 m3
  - Water Utilization     = 100.0%
  - Total Unmet Demand    = 50.0 m3
  - Total Irrigation Cost = (60.0 + 40.0) * $0.05 = $5.00
"""

from dataclasses import dataclass, field
import time
from typing import Any, Dict, List, Optional, Tuple, Union

# Documented scoring component weights
WEIGHT_STRESS = 0.35
WEIGHT_SENSITIVITY = 0.25
WEIGHT_PRIORITY = 0.25
WEIGHT_BENEFIT = 0.15


@dataclass
class GreedyAllocationItem:
    """Represents the greedy allocation output for a single plot."""

    plot_identifier: str
    plot_name: str
    remaining_demand: float
    allocated_water: float
    unmet_demand: float
    coverage_pct: float
    priority_score: float
    rank: int
    cost: float
    allocation_limit: float

    def to_dict(self) -> Dict[str, Any]:
        """Convert item to dictionary."""
        return {
            "plot_identifier": self.plot_identifier,
            "plot_name": self.plot_name,
            "remaining_demand": self.remaining_demand,
            "allocated_water": self.allocated_water,
            "unmet_demand": self.unmet_demand,
            "coverage_pct": self.coverage_pct,
            "priority_score": self.priority_score,
            "rank": self.rank,
            "cost": self.cost,
            "allocation_limit": self.allocation_limit,
        }


@dataclass
class GreedyResult:
    """Represents the complete result of a greedy water allocation run."""

    available_water: float
    total_demand: float
    total_allocated: float
    unmet_demand: float
    water_utilization_pct: float
    total_cost: float
    execution_time_ms: float
    allocations: List[GreedyAllocationItem] = field(default_factory=list)
    ranking_order: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        return {
            "available_water": self.available_water,
            "total_demand": self.total_demand,
            "total_allocated": self.total_allocated,
            "unmet_demand": self.unmet_demand,
            "water_utilization_pct": self.water_utilization_pct,
            "total_cost": self.total_cost,
            "execution_time_ms": self.execution_time_ms,
            "allocations": [a.to_dict() for a in self.allocations],
            "ranking_order": self.ranking_order,
        }


def calculate_priority_score(
    priority: int = 3,
    moisture_stress: float = 0.5,
    sensitivity_factor: float = 1.0,
    benefit_factor: float = 0.5,
    cost_per_unit: float = 0.05,
) -> float:
    """Calculate transparent plot priority score using documented weights.

    Score = Urgency / max(0.0001, cost_per_unit)
    where Urgency = 0.35*Stress + 0.25*(Ky/1.5) + 0.25*(Priority/5) + 0.15*Benefit
    """
    # Normalize components to [0.0, 1.0]
    p_norm = max(0.2, min(1.0, priority / 5.0))
    s_norm = max(0.0, min(1.0, moisture_stress))
    k_norm = max(0.0, min(1.0, sensitivity_factor / 1.5))
    v_norm = max(0.0, min(1.0, benefit_factor))

    urgency = (
        (WEIGHT_STRESS * s_norm)
        + (WEIGHT_SENSITIVITY * k_norm)
        + (WEIGHT_PRIORITY * p_norm)
        + (WEIGHT_BENEFIT * v_norm)
    )

    safe_cost = max(0.0001, cost_per_unit)
    return round(urgency / safe_cost, 4)


def greedy_allocate_pure(
    plots_data: List[Dict[str, Any]],
    available_water: float,
) -> GreedyResult:
    """Pure, framework-independent Greedy Water Allocation engine.

    Inputs for each plot dict:
      - 'plot_identifier' (str): Unique plot ID
      - 'name' (str, optional): Plot label
      - 'remaining_demand' (float): Water needed (liters or m3)
      - 'priority' (int, 1-5): Agronomic priority
      - 'moisture_stress' (float, 0-1): Moisture deficit ratio
      - 'sensitivity_factor' (float, optional): Ky factor (default 1.0)
      - 'benefit_factor' (float, optional): Economic benefit factor [0-1] (default 0.5)
      - 'cost_per_unit' (float, optional): Unit cost (default 0.05)
      - 'allocation_limit' (float, optional): Maximum allowed allocation (default = demand)

    Returns:
      GreedyResult with allocated water, unmet demand, costs, and execution runtime.
    """
    start_time = time.perf_counter()

    # Safely handle non-positive available water
    budget = max(0.0, float(available_water))

    if not plots_data or budget <= 0.0:
        elapsed = (time.perf_counter() - start_time) * 1000.0
        allocations = []
        tot_demand = 0.0
        for p in plots_data:
            dem = max(0.0, float(p.get("remaining_demand", 0.0)))
            tot_demand += dem
            p_id = str(p.get("plot_identifier") or p.get("id") or "PLOT")
            p_name = str(p.get("name") or f"Plot {p_id}")
            allocations.append(
                GreedyAllocationItem(
                    plot_identifier=p_id,
                    plot_name=p_name,
                    remaining_demand=round(dem, 2),
                    allocated_water=0.0,
                    unmet_demand=round(dem, 2),
                    coverage_pct=0.0 if dem > 0 else 100.0,
                    priority_score=0.0,
                    rank=0,
                    cost=0.0,
                    allocation_limit=dem,
                )
            )

        return GreedyResult(
            available_water=round(budget, 2),
            total_demand=round(tot_demand, 2),
            total_allocated=0.0,
            unmet_demand=round(tot_demand, 2),
            water_utilization_pct=100.0 if budget == 0.0 else 0.0,
            total_cost=0.0,
            execution_time_ms=round(elapsed, 4),
            allocations=allocations,
            ranking_order=[a.plot_identifier for a in allocations],
        )

    # 1. Compute priority score for each plot
    prepared_plots = []
    total_demand = 0.0

    for idx, p in enumerate(plots_data):
        p_id = str(p.get("plot_identifier") or p.get("id") or f"P-{idx+1}")
        p_name = str(p.get("name") or f"Plot {p_id}")
        demand = max(0.0, float(p.get("remaining_demand", p.get("water_demand", 0.0))))
        limit = float(p.get("allocation_limit", demand))
        limit = max(0.0, min(demand, limit))  # Limit cannot exceed demand or be negative

        total_demand += demand

        priority = int(p.get("priority", 3))
        stress = float(p.get("moisture_stress", p.get("moisture_stress_index", 0.5)))
        ky = float(p.get("sensitivity_factor", 1.0))
        benefit = float(p.get("benefit_factor", 0.5))
        cost_unit = float(p.get("cost_per_unit", p.get("cost_per_liter", 0.05)))

        score = calculate_priority_score(
            priority=priority,
            moisture_stress=stress,
            sensitivity_factor=ky,
            benefit_factor=benefit,
            cost_per_unit=cost_unit,
        )

        prepared_plots.append({
            "plot_identifier": p_id,
            "name": p_name,
            "remaining_demand": demand,
            "allocation_limit": limit,
            "cost_per_unit": cost_unit,
            "priority_score": score,
            "original_index": idx,
        })

    # 2. Deterministic Tie-Breaking Sort Key:
    #    - Score descending (-score)
    #    - Remaining demand ascending (satisfy smaller plots first when tied)
    #    - Plot identifier ascending (lexicographical reproducibility)
    def tie_break_key(item: Dict[str, Any]) -> Tuple[float, float, str]:
        return (-item["priority_score"], item["remaining_demand"], item["plot_identifier"])

    ranked = sorted(prepared_plots, key=tie_break_key)

    # 3. Greedy Allocation Pass
    remaining_budget = budget
    alloc_map: Dict[str, Tuple[float, float, int]] = {}  # plot_id -> (allocated, cost, rank)

    for rank_idx, item in enumerate(ranked, start=1):
        p_id = item["plot_identifier"]
        limit = item["allocation_limit"]
        cost_unit = item["cost_per_unit"]

        if remaining_budget <= 0.00001:
            alloc_map[p_id] = (0.0, 0.0, rank_idx)
            continue

        needed = limit
        if remaining_budget >= needed:
            allocated = needed
            remaining_budget -= needed
        else:
            allocated = remaining_budget
            remaining_budget = 0.0

        plot_cost = round(allocated * cost_unit, 2)
        alloc_map[p_id] = (round(allocated, 2), plot_cost, rank_idx)

    # 4. Compile Output Allocations (maintaining input order)
    allocation_items: List[GreedyAllocationItem] = []
    total_allocated = 0.0
    total_cost = 0.0

    for item in prepared_plots:
        p_id = item["plot_identifier"]
        allocated, plot_cost, rank = alloc_map[p_id]
        demand = item["remaining_demand"]
        unmet = max(0.0, round(demand - allocated, 2))
        cov_pct = round((allocated / demand * 100.0) if demand > 0 else 100.0, 2)

        total_allocated += allocated
        total_cost += plot_cost

        allocation_items.append(
            GreedyAllocationItem(
                plot_identifier=p_id,
                plot_name=item["name"],
                remaining_demand=round(demand, 2),
                allocated_water=allocated,
                unmet_demand=unmet,
                coverage_pct=cov_pct,
                priority_score=item["priority_score"],
                rank=rank,
                cost=plot_cost,
                allocation_limit=item["allocation_limit"],
            )
        )

    elapsed_ms = (time.perf_counter() - start_time) * 1000.0
    total_allocated = round(total_allocated, 2)
    unmet_total = max(0.0, round(total_demand - total_allocated, 2))
    utilization = round(min(100.0, (total_allocated / budget * 100.0)) if budget > 0 else 100.0, 2)

    return GreedyResult(
        available_water=round(budget, 2),
        total_demand=round(total_demand, 2),
        total_allocated=total_allocated,
        unmet_demand=unmet_total,
        water_utilization_pct=utilization,
        total_cost=round(total_cost, 2),
        execution_time_ms=round(elapsed_ms, 4),
        allocations=allocation_items,
        ranking_order=[r["plot_identifier"] for r in ranked],
    )


# ---------------------------------------------------------------------------------------
# CropFlow Framework Integration Wrapper
# ---------------------------------------------------------------------------------------
def run_greedy_allocation(
    plots: List[Any],
    available_water: float,
    energy_rate: float = 0.045,
    labor_rate: float = 14.0,
    pump_capacity: float = 25.0,
    scenario_name: str = "Standard",
) -> Any:
    """CropFlow domain wrapper converting Plot domain models to GreedyResult/OptimizationResult."""
    # Convert Plot domain models to pure dictionaries for greedy_allocate_pure
    plots_payload = []
    for p in plots:
        # Normalize benefit factor based on crop potential value
        val = getattr(p, "total_potential_value", 2000.0)
        benefit_factor = min(1.0, max(0.1, val / 10000.0))
        plots_payload.append({
            "plot_identifier": getattr(p, "plot_identifier", getattr(p, "name", "P-101")),
            "name": getattr(p, "name", "Plot"),
            "remaining_demand": getattr(p, "water_demand", getattr(p, "remaining_demand_liters", 100.0)),
            "allocation_limit": getattr(p, "water_demand", 100.0),
            "priority": getattr(p, "priority", 3),
            "moisture_stress": getattr(p, "moisture_stress_index", 0.5),
            "sensitivity_factor": getattr(p, "sensitivity_factor", 1.0),
            "benefit_factor": benefit_factor,
            "cost_per_unit": energy_rate,
            "id": getattr(p, "id", None),
        })

    # Execute pure greedy allocation
    pure_res = greedy_allocate_pure(plots_payload, available_water)

    # Bridge to OptimizationResult using app.algorithms.metrics
    from app.algorithms.metrics import evaluate_allocation

    raw_allocs = {}
    for idx, p in enumerate(plots):
        key = getattr(p, "id", None) if getattr(p, "id", None) is not None else idx
        raw_allocs[key] = pure_res.allocations[idx].allocated_water

    return evaluate_allocation(
        plots=plots,
        raw_allocations=raw_allocs,
        available_water=available_water,
        energy_rate=energy_rate,
        labor_rate=labor_rate,
        pump_capacity=pump_capacity,
        algorithm_name="Greedy Allocation",
        scenario_name=scenario_name,
        execution_time_ms=pure_res.execution_time_ms,
    )
