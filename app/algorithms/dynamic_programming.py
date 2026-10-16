"""Dynamic Programming Water-Allocation Algorithm for CropFlow.

Models irrigation scheduling as a Multiple-Choice Resource Allocation / Knapsack problem.
Discretizes available water capacity and optimizes non-linear concave yield curves,
crop priorities, and unmet critical demand penalties to achieve global Bellman optimality
for the discretized model.

-----------------------------------------------------------------------------------------
MATHEMATICAL FORMULATION:
-----------------------------------------------------------------------------------------
1. Multiple-Choice Resource Allocation Model:
   Let N be the number of agricultural plots, indexed i = 1, ..., N.
   Let W_available be the total available water (in liters or m3).
   Let D_i be the remaining water demand for plot i (D_i >= 0).
   The water space is discretized into configurable quantum units:
     Delta_w = quantum_unit  (e.g., 10.0 Liters or 1.0 m3)
   Total discrete capacity states:
     C = floor(W_available / Delta_w)

   For each plot i, the candidate discrete allocation choices are:
     Choices(i) = { (k, w_{i,k}) | k in {0, 1, ..., K_i}, w_{i,k} = min(D_i, k * Delta_w) }
     where K_i = ceil(D_i / Delta_w).

2. Utility / Objective Function U_i(w):
   For plot i receiving discrete water allocation w in [0, D_i]:
     a. Demand Coverage Fraction:
        f_i(w) = w / D_i  (if D_i > 0, else 1.0)
     b. FAO-33 Concave Yield Preservation Reward:
        Y_ratio(w) = max(0.0, 1.0 - Ky_i * (1.0 - f_i(w)))
        Preserved_Value(w) = Y_ratio(w) * CropPotentialValue_i
     c. Agronomic Priority Weighting:
        omega(Priority_i) = 0.70 + (0.10 * Priority_i)  (range: [0.80, 1.20])
     d. Penalty for Unmet Critical Demand:
        Unmet demand on high-sensitivity crops (Ky >= 1.0, e.g. flowering stage)
        or high priority plots (Priority >= 4) incurs severe non-linear stress:
        Penalty(w) = lambda_penalty * Ky_i * (1.0 - f_i(w))^2 * CropPotentialValue_i
        (where lambda_penalty = 0.20; Penalty is exactly 0.0 when demand is fully met)
     e. Consistent Irrigation Cost:
        Cost(w) = w * CostPerUnit_i
     f. Net Plot Utility:
        U_i(w) = [ omega(Priority_i) * Preserved_Value(w) ] - Penalty(w) - Cost(w)

   Total Optimization Objective:
     Maximize sum_{i=1..N} U_i(w_i)
     Subject to:
       sum_{i=1..N} w_i <= W_available
       0 <= w_i <= D_i  for all i in {1..N}

3. Dynamic Programming Specification:
   - State Definition:
     DP[i][c]: The maximum total net utility attainable by allocating at most c
     discrete units of water across the first i plots (i in 0..N, c in 0..C).
   - Recurrence Relation:
     DP[i][c] = max_{ (k, w) in Choices(i), k <= c } { DP[i-1][c - k] + U_i(w) }
   - Initialization:
     DP[0][c] = 0.0 for all c in {0..C}
     DP[i][c] = -infinity for i > 0, c in {0..C}
   - Reconstruction:
     Maintain backtrack[i][c] = chosen_k pointer table.
     Identify optimal terminal capacity state: c* = argmax_{0 <= c <= C} DP[N][c].
     Backtrack from i = N down to 1:
       k* = backtrack[i][c*]
       w_i* = min(D_i, k* * Delta_w)
       c* <- c* - k*

4. Complexity Analysis:
   - Time Complexity: O(N * C * K_max)
     where N = number of plots,
           C = floor(W_available / Delta_w) (discretized capacity states),
           K_max = max_i ceil(D_i / Delta_w) (maximum discrete choices per plot).
     Bounded polynomial pseudo-polynomial time in discrete capacity.
   - Auxiliary Space Complexity: O(N * C)
     Stores the 2D DP table and 2D backtrack decision pointers.

5. Optimality Explanation & Approximation Boundary:
   THE DP SOLUTION IS MATHEMATICALLY OPTIMAL FOR THE DEFINED DISCRETIZED MODEL,
   BUT IS AN APPROXIMATION OF THE ORIGINAL CONTINUOUS PROBLEM.
   Continuous water volume is quantized into increments of Delta_w. The true continuous
   global optimum may lie between discrete grid intervals. The quantization error is
   bounded by O(Delta_w) and converges asymptotically to the continuous optimum as
   Delta_w -> 0.
-----------------------------------------------------------------------------------------
"""

from dataclasses import dataclass, field
import math
import time
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class DPAllocationItem:
    """Represents the DP allocation output for a single plot."""

    plot_identifier: str
    plot_name: str
    remaining_demand: float
    allocated_water: float
    unmet_demand: float
    coverage_pct: float
    utility: float
    cost: float
    yield_preservation_pct: float
    discrete_units_used: int

    def to_dict(self) -> Dict[str, Any]:
        """Convert item to dictionary."""
        return {
            "plot_identifier": self.plot_identifier,
            "plot_name": self.plot_name,
            "remaining_demand": self.remaining_demand,
            "allocated_water": self.allocated_water,
            "unmet_demand": self.unmet_demand,
            "coverage_pct": self.coverage_pct,
            "utility": self.utility,
            "cost": self.cost,
            "yield_preservation_pct": self.yield_preservation_pct,
            "discrete_units_used": self.discrete_units_used,
        }


@dataclass
class DPResult:
    """Represents the complete result of a dynamic programming water allocation run."""

    available_water: float
    quantum_unit: float
    discrete_capacity_steps: int
    objective_value: float
    total_allocated: float
    total_demand: float
    unmet_demand: float
    water_utilization_pct: float
    total_cost: float
    execution_time_ms: float
    allocations: List[DPAllocationItem] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        return {
            "available_water": self.available_water,
            "quantum_unit": self.quantum_unit,
            "discrete_capacity_steps": self.discrete_capacity_steps,
            "objective_value": self.objective_value,
            "total_allocated": self.total_allocated,
            "total_demand": self.total_demand,
            "unmet_demand": self.unmet_demand,
            "water_utilization_pct": self.water_utilization_pct,
            "total_cost": self.total_cost,
            "execution_time_ms": self.execution_time_ms,
            "allocations": [a.to_dict() for a in self.allocations],
        }


def calculate_plot_utility(
    allocated_water: float,
    demand: float,
    crop_value: float,
    sensitivity_factor: float = 1.0,
    priority: int = 3,
    cost_per_unit: float = 0.05,
    lambda_penalty: float = 0.20,
) -> Tuple[float, float, float, float]:
    """Compute plot utility, preserved yield %, penalty, and cost for a given water allocation.

    Returns:
      (net_utility, preserved_value, penalty, cost)
    """
    if demand <= 0.0:
        return (0.0, 0.0, 0.0, 0.0)

    # Clamped allocation fraction
    alloc = max(0.0, min(demand, allocated_water))
    coverage = alloc / demand
    deficit = 1.0 - coverage

    # 1. FAO-33 Yield Response Ratio
    yield_ratio = max(0.0, 1.0 - (sensitivity_factor * deficit))
    preserved_yield_pct = round(yield_ratio * 100.0, 2)
    base_preserved_value = yield_ratio * crop_value

    # 2. Priority Scaling
    priority_weight = 0.70 + (0.10 * max(1, min(5, priority)))
    weighted_benefit = priority_weight * base_preserved_value

    # 3. Critical Unmet Demand Penalty
    # Severe quadratic penalty for unwatered sensitive (flowering) or high-priority crops
    critical_factor = max(0.5, sensitivity_factor)
    penalty = lambda_penalty * critical_factor * (deficit ** 2) * crop_value

    # 4. Irrigation Cost
    cost = alloc * cost_per_unit

    # Net Utility
    net_utility = weighted_benefit - penalty - cost
    return (round(net_utility, 3), round(base_preserved_value, 2), round(penalty, 2), round(cost, 2))


def dp_allocate_pure(
    plots_data: List[Dict[str, Any]],
    available_water: float,
    quantum_unit: Optional[float] = None,
    max_discrete_steps: int = 150,
) -> DPResult:
    """Pure, framework-independent Dynamic Programming resource allocation algorithm.

    Inputs for each plot dict:
      - 'plot_identifier' (str): Unique identifier
      - 'name' (str, optional): Label
      - 'remaining_demand' (float): Water needed (liters or m3)
      - 'crop_value' (float, optional): Maximum potential economic value (default 2000.0)
      - 'sensitivity_factor' (float, optional): FAO-33 Ky factor (default 1.0)
      - 'priority' (int, 1-5): Agronomic priority (default 3)
      - 'cost_per_unit' (float, optional): Cost per unit water (default 0.05)

    Parameters:
      - available_water (float): Total water budget constraint
      - quantum_unit (float, optional): Discretization step Delta_w. If None, dynamically
        derived to maintain accuracy with <= max_discrete_steps.
      - max_discrete_steps (int): Upper bound for discrete capacity grid resolution.

    Returns:
      DPResult: Optimal allocations for the discretized model with objective value,
      costs, unmet demand, and execution time.
    """
    start_time = time.perf_counter()

    budget = max(0.0, float(available_water))
    total_demand = sum(max(0.0, float(p.get("remaining_demand", p.get("water_demand", 0.0)))) for p in plots_data)

    # Edge cases: No plots or zero available water
    if not plots_data or budget <= 0.0:
        elapsed = (time.perf_counter() - start_time) * 1000.0
        allocations = []
        tot_utility = 0.0
        for p in plots_data:
            p_id = str(p.get("plot_identifier") or p.get("id") or "PLOT")
            p_name = str(p.get("name") or f"Plot {p_id}")
            dem = max(0.0, float(p.get("remaining_demand", p.get("water_demand", 0.0))))
            val = float(p.get("crop_value", p.get("total_potential_value", 2000.0)))
            ky = float(p.get("sensitivity_factor", 1.0))
            prio = int(p.get("priority", 3))
            cost_u = float(p.get("cost_per_unit", p.get("cost_per_liter", 0.05)))

            u_0, _, _, _ = calculate_plot_utility(0.0, dem, val, ky, prio, cost_u)
            tot_utility += u_0

            allocations.append(
                DPAllocationItem(
                    plot_identifier=p_id,
                    plot_name=p_name,
                    remaining_demand=round(dem, 2),
                    allocated_water=0.0,
                    unmet_demand=round(dem, 2),
                    coverage_pct=0.0 if dem > 0 else 100.0,
                    utility=u_0,
                    cost=0.0,
                    yield_preservation_pct=round(max(0.0, 1.0 - ky) * 100.0, 2) if dem > 0 else 100.0,
                    discrete_units_used=0,
                )
            )

        return DPResult(
            available_water=round(budget, 2),
            quantum_unit=10.0 if quantum_unit is None else quantum_unit,
            discrete_capacity_steps=0,
            objective_value=round(tot_utility, 2),
            total_allocated=0.0,
            total_demand=round(total_demand, 2),
            unmet_demand=round(total_demand, 2),
            water_utilization_pct=100.0 if budget == 0.0 else 0.0,
            total_cost=0.0,
            execution_time_ms=round(elapsed, 4),
            allocations=allocations,
        )

    # Determine discretization quantum Delta_w
    if quantum_unit is not None and quantum_unit > 0.0:
        delta_w = float(quantum_unit)
        c_steps = int(math.floor(budget / delta_w))
    else:
        # Dynamic quantum step sized to respect max_discrete_steps for fast execution
        c_steps = min(max_discrete_steps, max(50, int(budget)))
        delta_w = budget / float(c_steps) if c_steps > 0 else 1.0

    c_steps = max(1, c_steps)
    num_plots = len(plots_data)

    # 1. Generate feasible discrete candidate choices for each plot
    # plot_choices[i] = list of tuples: (k_units, water_volume, utility, cost, yield_pct)
    plot_choices: List[List[Tuple[int, float, float, float, float]]] = []

    for p in plots_data:
        demand = max(0.0, float(p.get("remaining_demand", p.get("water_demand", 0.0))))
        val = float(p.get("crop_value", p.get("total_potential_value", 2000.0)))
        ky = float(p.get("sensitivity_factor", 1.0))
        prio = int(p.get("priority", 3))
        cost_u = float(p.get("cost_per_unit", p.get("cost_per_liter", 0.05)))

        candidates: List[Tuple[int, float, float, float, float]] = []

        if demand <= 0.0:
            candidates.append((0, 0.0, 0.0, 0.0, 100.0))
            plot_choices.append(candidates)
            continue

        # Zero allocation choice
        u_0, _, _, c_0 = calculate_plot_utility(0.0, demand, val, ky, prio, cost_u)
        y_0 = round(max(0.0, 1.0 - ky) * 100.0, 2)
        candidates.append((0, 0.0, u_0, c_0, y_0))

        # Discrete allocation levels up to plot demand
        max_k = int(math.ceil(demand / delta_w))
        # Ensure we don't exceed capacity
        max_k = min(c_steps, max_k)

        for k in range(1, max_k + 1):
            w = min(demand, k * delta_w)  # Strictly enforce: never exceed plot demand
            u, _, _, c = calculate_plot_utility(w, demand, val, ky, prio, cost_u)
            cov = w / demand
            y_pct = round(max(0.0, 1.0 - (ky * (1.0 - cov))) * 100.0, 2)
            candidates.append((k, w, u, c, y_pct))

            if w >= demand:
                break

        plot_choices.append(candidates)

    # 2. Dynamic Programming Table & Backtrack Pointers
    # dp[i][c] = max total utility using c units across plots 1..i
    # backtrack[i][c] = index of chosen candidate tuple in plot_choices[i-1]
    dp: List[List[float]] = [[-1e9] * (c_steps + 1) for _ in range(num_plots + 1)]
    backtrack: List[List[int]] = [[0] * (c_steps + 1) for _ in range(num_plots + 1)]

    # Base case: 0 plots allocated 0 capacity yields 0 utility
    dp[0][0] = 0.0

    # Fill DP Table
    for i in range(1, num_plots + 1):
        candidates = plot_choices[i - 1]
        for c in range(c_steps + 1):
            best_val = -1e9
            best_cand_idx = 0
            for cand_idx, (k, _, u_gain, _, _) in enumerate(candidates):
                if k <= c:
                    prev_val = dp[i - 1][c - k]
                    if prev_val > -1e8:
                        val = prev_val + u_gain
                        if val > best_val:
                            best_val = val
                            best_cand_idx = cand_idx

            dp[i][c] = best_val
            backtrack[i][c] = best_cand_idx

    # 3. Identify Optimal Terminal Capacity State c*
    best_c = 0
    best_objective = -1e9
    for c in range(c_steps + 1):
        if dp[num_plots][c] > best_objective:
            best_objective = dp[num_plots][c]
            best_c = c

    # 4. Reconstruction of Chosen Plot Allocations
    curr_c = best_c
    plot_alloc_results: List[Tuple[float, float, float, float, int]] = [(0.0, 0.0, 0.0, 0.0, 0)] * num_plots

    for i in range(num_plots, 0, -1):
        cand_idx = backtrack[i][curr_c]
        k, w_vol, u_val, cost_val, y_pct = plot_choices[i - 1][cand_idx]
        plot_alloc_results[i - 1] = (w_vol, u_val, cost_val, y_pct, k)
        curr_c -= k

    # 5. Format Output Results
    allocations: List[DPAllocationItem] = []
    total_allocated = 0.0
    total_cost = 0.0

    for idx, p in enumerate(plots_data):
        p_id = str(p.get("plot_identifier") or p.get("id") or f"P-{idx+1}")
        p_name = str(p.get("name") or f"Plot {p_id}")
        demand = max(0.0, float(p.get("remaining_demand", p.get("water_demand", 0.0))))

        w_vol, u_val, cost_val, y_pct, k_units = plot_alloc_results[idx]
        w_vol = round(w_vol, 2)
        unmet = max(0.0, round(demand - w_vol, 2))
        cov_pct = round((w_vol / demand * 100.0) if demand > 0 else 100.0, 2)

        total_allocated += w_vol
        total_cost += cost_val

        allocations.append(
            DPAllocationItem(
                plot_identifier=p_id,
                plot_name=p_name,
                remaining_demand=round(demand, 2),
                allocated_water=w_vol,
                unmet_demand=unmet,
                coverage_pct=cov_pct,
                utility=round(u_val, 2),
                cost=round(cost_val, 2),
                yield_preservation_pct=y_pct,
                discrete_units_used=k_units,
            )
        )

    elapsed_ms = (time.perf_counter() - start_time) * 1000.0
    total_allocated = round(total_allocated, 2)
    unmet_total = max(0.0, round(total_demand - total_allocated, 2))
    utilization = round(min(100.0, (total_allocated / budget * 100.0)) if budget > 0 else 100.0, 2)

    return DPResult(
        available_water=round(budget, 2),
        quantum_unit=round(delta_w, 4),
        discrete_capacity_steps=c_steps,
        objective_value=round(best_objective, 2),
        total_allocated=total_allocated,
        total_demand=round(total_demand, 2),
        unmet_demand=unmet_total,
        water_utilization_pct=utilization,
        total_cost=round(total_cost, 2),
        execution_time_ms=round(elapsed_ms, 4),
        allocations=allocations,
    )


# ---------------------------------------------------------------------------------------
# CropFlow Framework Integration Wrapper
# ---------------------------------------------------------------------------------------
def run_dp_allocation(
    plots: List[Any],
    available_water: float,
    energy_rate: float = 0.045,
    labor_rate: float = 14.0,
    pump_capacity: float = 25.0,
    scenario_name: str = "Standard",
    quantum_unit: Optional[float] = None,
    step_count: int = 100,
) -> Any:
    """CropFlow domain wrapper adapting Plot domain models to DPResult and OptimizationResult."""
    # Convert Plot domain models to pure dictionary representations
    plots_payload = []
    for p in plots:
        plots_payload.append({
            "plot_identifier": getattr(p, "plot_identifier", getattr(p, "name", "P-101")),
            "name": getattr(p, "name", "Plot"),
            "remaining_demand": getattr(p, "water_demand", 100.0),
            "crop_value": getattr(p, "total_potential_value", 2000.0),
            "sensitivity_factor": getattr(p, "sensitivity_factor", 1.0),
            "priority": getattr(p, "priority", 3),
            "cost_per_unit": energy_rate,
            "id": getattr(p, "id", None),
        })

    # Run the pure Dynamic Programming algorithm
    pure_res = dp_allocate_pure(
        plots_data=plots_payload,
        available_water=available_water,
        quantum_unit=quantum_unit,
        max_discrete_steps=step_count,
    )

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
        algorithm_name="Dynamic Programming",
        scenario_name=scenario_name,
        execution_time_ms=pure_res.execution_time_ms,
    )
