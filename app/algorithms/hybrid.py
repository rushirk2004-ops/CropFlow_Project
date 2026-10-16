"""Hybrid Irrigation Optimization Strategy for CropFlow.

Combines the rapid urgency triage of Greedy Allocation with the global non-linear
combinatorial refinement of Dynamic Programming and neighborhood local search.

-----------------------------------------------------------------------------------------
ALGORITHM WORKFLOW & REFINEMENT METHODOLOGY:
-----------------------------------------------------------------------------------------
1. Phase 1: Initial Feasible Allocation (Greedy Baseline)
   - Computes deterministic composite priority scores based on soil moisture stress,
     growth stage sensitivity factor Ky (FAO-33), agronomic priority, and economic benefit.
   - Generates an initial feasible allocation w_greedy = (w_1^g, ..., w_N^g) respecting
     demand bounds (0 <= w_i^g <= D_i) and total water budget (sum w_i^g <= W_available).
   - Evaluates the baseline objective value J_initial = sum U_i(w_i^g) under the standardized
     net utility function U_i(w).

2. Phase 2: Incorporation of Greedy Solution into Refinement
   - The greedy allocation is not discarded; it serves two foundational purposes:
     a) Survival Anchor Reservation:
        Vulnerable plots (severe moisture stress >= 0.5 or high sensitivity Ky >= 1.0)
        are protected with an essential baseline survival allocation:
          b_i = min(w_i^g, survival_target_i)
        where survival_target_i prevents irreversible wilting and avoids catastrophic
        quadratic deficit penalties.
     b) Search Space Initialization:
        The remaining water budget W_rem = W_available - sum(b_i) is distributed across
        residual demands (D_i - b_i) using discretized Dynamic Programming over concave
        FAO-33 yield response curves.
     c) Local Neighborhood Delta-Transfer Search:
        Starting from the candidate solution, iterative marginal delta transfers are
        evaluated between plot pairs (transferring quantum delta from plots with lower
        marginal utility to plots with higher marginal utility) until no pairwise
        reallocation strictly improves the aggregate objective.

3. Phase 3: Objective Comparison & Non-Regression Safety Gate
   - The refined allocation w_refined is evaluated under the EXACT same objective function:
       J_refined = sum U_i(w_i^refined)
   - If J_refined >= J_initial:
       w_final = w_refined
       was_refined_better = True
     Else:
       w_final = w_greedy
       was_refined_better = False
   - This mathematically guarantees the non-regression property:
       J_final = max(J_initial, J_refined) >= J_initial

4. Phase 4: Runtime & Metric Tracking
   - Wall-clock runtimes for both the Greedy baseline pass (greedy_time_ms) and the
     refinement pass (refinement_time_ms) are recorded alongside the aggregate execution time.
   - Pre-refinement objective, post-refinement objective, and net refinement gain are logged.

-----------------------------------------------------------------------------------------
COMPUTATIONAL COMPLEXITY:
-----------------------------------------------------------------------------------------
- Time Complexity: O(N log N + N * C * K + L * N^2)
  - Phase 1 (Greedy): O(N log N) via Timsort priority ranking.
  - Phase 2 (DP on residual capacity): O(N * C * K), where C = W_rem / Delta_w and K = D_max / Delta_w.
  - Phase 3 (Local neighborhood search): O(L * N^2), where L is the bounded local iteration limit.
  Overall Time Complexity = O(N log N + N * C * K).
- Auxiliary Space Complexity: O(N * C)
  Maintains the 2D DP state table and backtrack decision pointers for the residual capacity.

-----------------------------------------------------------------------------------------
EMPIRICAL PERFORMANCE DISCLAIMER:
-----------------------------------------------------------------------------------------
THE HYBRID STRATEGY IS NOT CLAIMED TO BE FASTER OR UNIVERSALLY SUPERIOR WITHOUT
EMPIRICAL BENCHMARKING.
Because the hybrid pipeline executes both an initial greedy allocation pass and a subsequent
discretized optimization refinement pass, its computational runtime is strictly greater than
pure Greedy and comparable to standalone Dynamic Programming. Its objective advantage depends
on farm drought severity, crop diversity, and discretization resolution.
-----------------------------------------------------------------------------------------
"""

from dataclasses import dataclass, field
import math
import time
from typing import Any, Dict, List, Optional, Tuple

from app.algorithms.dynamic_programming import calculate_plot_utility
from app.algorithms.greedy import greedy_allocate_pure


@dataclass
class HybridAllocationItem:
    """Represents the hybrid allocation output for an individual agricultural plot."""

    plot_identifier: str
    plot_name: str
    remaining_demand: float
    initial_greedy_allocated: float
    refined_allocated: float
    allocated_water: float
    unmet_demand: float
    coverage_pct: float
    initial_utility: float
    final_utility: float
    cost: float
    yield_preservation_pct: float

    def to_dict(self) -> Dict[str, Any]:
        """Convert item to dictionary."""
        return {
            "plot_identifier": self.plot_identifier,
            "plot_name": self.plot_name,
            "remaining_demand": self.remaining_demand,
            "initial_greedy_allocated": self.initial_greedy_allocated,
            "refined_allocated": self.refined_allocated,
            "allocated_water": self.allocated_water,
            "unmet_demand": self.unmet_demand,
            "coverage_pct": self.coverage_pct,
            "initial_utility": self.initial_utility,
            "final_utility": self.final_utility,
            "cost": self.cost,
            "yield_preservation_pct": self.yield_preservation_pct,
        }


@dataclass
class HybridResult:
    """Represents the complete result of a hybrid optimization run."""

    available_water: float
    total_demand: float
    total_allocated: float
    unmet_demand: float
    water_utilization_pct: float
    total_cost: float
    initial_objective: float
    refined_objective: float
    final_objective: float
    was_refined_better: bool
    refinement_gain: float
    greedy_time_ms: float
    refinement_time_ms: float
    execution_time_ms: float
    allocations: List[HybridAllocationItem] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        return {
            "available_water": self.available_water,
            "total_demand": self.total_demand,
            "total_allocated": self.total_allocated,
            "unmet_demand": self.unmet_demand,
            "water_utilization_pct": self.water_utilization_pct,
            "total_cost": self.total_cost,
            "initial_objective": self.initial_objective,
            "refined_objective": self.refined_objective,
            "final_objective": self.final_objective,
            "was_refined_better": self.was_refined_better,
            "refinement_gain": self.refinement_gain,
            "greedy_time_ms": self.greedy_time_ms,
            "refinement_time_ms": self.refinement_time_ms,
            "execution_time_ms": self.execution_time_ms,
            "allocations": [a.to_dict() for a in self.allocations],
        }


def hybrid_allocate_pure(
    plots_data: List[Dict[str, Any]],
    available_water: float,
    step_count: int = 60,
    lambda_penalty: float = 0.20,
    max_local_refinement_steps: int = 25,
) -> HybridResult:
    """Pure, framework-independent Hybrid Water Allocation Engine.

    Inputs for each plot dict:
      - 'plot_identifier' (str): Unique plot ID
      - 'name' (str, optional): Label
      - 'remaining_demand' (float): Water needed (liters or m3)
      - 'crop_value' (float, optional): Potential crop economic value (default 2000.0)
      - 'sensitivity_factor' (float, optional): FAO-33 Ky factor (default 1.0)
      - 'priority' (int, 1-5): Agronomic priority (default 3)
      - 'moisture_stress' (float, optional): Stress index in [0, 1] (default 0.5)
      - 'cost_per_unit' (float, optional): Cost per unit water (default 0.05)

    Parameters:
      - available_water (float): Total water budget constraint
      - step_count (int): Discrete capacity steps for residual DP refinement
      - lambda_penalty (float): Critical deficit penalty multiplier
      - max_local_refinement_steps (int): Upper bound on pairwise marginal search iterations

    Returns:
      HybridResult: Comprehensive outcome containing pre- and post-refinement objectives,
      runtimes, and plot allocations.
    """
    total_start_time = time.perf_counter()
    budget = max(0.0, float(available_water))

    # Calculate total demand
    total_demand = 0.0
    for p in plots_data:
        dem = max(0.0, float(p.get("remaining_demand", p.get("water_demand", 0.0))))
        total_demand += dem

    # Handle zero plots or zero budget
    if not plots_data or budget <= 0.0:
        elapsed = (time.perf_counter() - total_start_time) * 1000.0
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

            u_0, _, _, _ = calculate_plot_utility(
                allocated_water=0.0,
                demand=dem,
                crop_value=val,
                sensitivity_factor=ky,
                priority=prio,
                cost_per_unit=cost_u,
                lambda_penalty=lambda_penalty,
            )
            tot_utility += u_0
            allocations.append(
                HybridAllocationItem(
                    plot_identifier=p_id,
                    plot_name=p_name,
                    remaining_demand=round(dem, 2),
                    initial_greedy_allocated=0.0,
                    refined_allocated=0.0,
                    allocated_water=0.0,
                    unmet_demand=round(dem, 2),
                    coverage_pct=0.0 if dem > 0 else 100.0,
                    initial_utility=u_0,
                    final_utility=u_0,
                    cost=0.0,
                    yield_preservation_pct=round(max(0.0, 1.0 - ky) * 100.0, 2) if dem > 0 else 100.0,
                )
            )

        return HybridResult(
            available_water=round(budget, 2),
            total_demand=round(total_demand, 2),
            total_allocated=0.0,
            unmet_demand=round(total_demand, 2),
            water_utilization_pct=100.0 if budget == 0.0 else 0.0,
            total_cost=0.0,
            initial_objective=round(tot_utility, 2),
            refined_objective=round(tot_utility, 2),
            final_objective=round(tot_utility, 2),
            was_refined_better=True,
            refinement_gain=0.0,
            greedy_time_ms=0.0,
            refinement_time_ms=0.0,
            execution_time_ms=round(elapsed, 4),
            allocations=allocations,
        )

    # -----------------------------------------------------------------------------------
    # Step 1: Initial Feasible Allocation using Greedy Algorithm
    # -----------------------------------------------------------------------------------
    t_greedy_start = time.perf_counter()
    greedy_res = greedy_allocate_pure(plots_data, budget)
    greedy_time_ms = (time.perf_counter() - t_greedy_start) * 1000.0

    greedy_alloc_map: Dict[str, float] = {
        item.plot_identifier: item.allocated_water for item in greedy_res.allocations
    }

    # Evaluate initial objective under the standardized utility function U(w)
    initial_utilities: Dict[str, float] = {}
    for p in plots_data:
        p_id = str(p.get("plot_identifier") or p.get("id") or "PLOT")
        w_g = greedy_alloc_map.get(p_id, 0.0)
        dem = max(0.0, float(p.get("remaining_demand", p.get("water_demand", 0.0))))
        val = float(p.get("crop_value", p.get("total_potential_value", 2000.0)))
        ky = float(p.get("sensitivity_factor", 1.0))
        prio = int(p.get("priority", 3))
        cost_u = float(p.get("cost_per_unit", p.get("cost_per_liter", 0.05)))

        u, _, _, _ = calculate_plot_utility(
            allocated_water=w_g,
            demand=dem,
            crop_value=val,
            sensitivity_factor=ky,
            priority=prio,
            cost_per_unit=cost_u,
            lambda_penalty=lambda_penalty,
        )
        initial_utilities[p_id] = u

    initial_objective = round(sum(initial_utilities.values()), 2)

    # -----------------------------------------------------------------------------------
    # Step 2: Refinement using Dynamic Programming & Local Search
    # -----------------------------------------------------------------------------------
    t_ref_start = time.perf_counter()

    # Determine baseline survival protection targets
    survival_targets: Dict[str, float] = {}
    total_survival_needed = 0.0

    for p in plots_data:
        p_id = str(p.get("plot_identifier") or p.get("id") or "PLOT")
        dem = max(0.0, float(p.get("remaining_demand", p.get("water_demand", 0.0))))
        ky = float(p.get("sensitivity_factor", 1.0))
        stress = float(p.get("moisture_stress", p.get("moisture_stress_index", 0.5)))

        # Vulnerable crops (flowering or severe stress) require 30% survival water; others 15%
        if ky >= 1.0 or stress >= 0.5:
            target = min(dem, dem * 0.30)
        else:
            target = min(dem, dem * 0.15)
        survival_targets[p_id] = target
        total_survival_needed += target

    survival_allocations: Dict[str, float] = {}
    if budget <= total_survival_needed:
        # Water budget is extremely constrained: prioritize survival targets greedily by urgency
        rem_water = budget
        for g_item in greedy_res.allocations:
            p_id = g_item.plot_identifier
            needed = survival_targets.get(p_id, 0.0)
            alloc = min(rem_water, needed)
            survival_allocations[p_id] = alloc
            rem_water -= alloc
        remaining_water = 0.0
    else:
        # Budget accommodates all baseline survival targets
        for p_id, tgt in survival_targets.items():
            survival_allocations[p_id] = tgt
        remaining_water = budget - total_survival_needed

    # Residual Dynamic Programming over remaining water
    num_plots = len(plots_data)
    steps = max(1, min(step_count, max(20, int(remaining_water)))) if remaining_water > 0 else 1
    step_size = remaining_water / float(steps) if remaining_water > 0 else 1.0

    # Build discrete candidate choices for each plot
    plot_choices: List[List[Tuple[int, float, float]]] = []  # (k_steps, extra_water, utility)
    for p in plots_data:
        p_id = str(p.get("plot_identifier") or p.get("id") or "PLOT")
        dem = max(0.0, float(p.get("remaining_demand", p.get("water_demand", 0.0))))
        val = float(p.get("crop_value", p.get("total_potential_value", 2000.0)))
        ky = float(p.get("sensitivity_factor", 1.0))
        prio = int(p.get("priority", 3))
        cost_u = float(p.get("cost_per_unit", p.get("cost_per_liter", 0.05)))

        base_w = survival_allocations.get(p_id, 0.0)
        res_dem = max(0.0, dem - base_w)

        candidates: List[Tuple[int, float, float]] = []

        # Choice 0: Only baseline survival allocation
        u_base, _, _, _ = calculate_plot_utility(
            base_w, dem, val, ky, prio, cost_u, lambda_penalty
        )
        candidates.append((0, 0.0, u_base))

        if remaining_water > 0 and res_dem > 0:
            max_k = min(steps, int(math.ceil(res_dem / step_size)))
            for k in range(1, max_k + 1):
                extra_w = min(res_dem, k * step_size)
                total_w = base_w + extra_w
                u, _, _, _ = calculate_plot_utility(
                    total_w, dem, val, ky, prio, cost_u, lambda_penalty
                )
                candidates.append((k, extra_w, u))
                if extra_w >= res_dem:
                    break

        plot_choices.append(candidates)

    # 2D DP Table over discrete capacity steps
    dp: List[List[float]] = [[-1e9] * (steps + 1) for _ in range(num_plots + 1)]
    backtrack: List[List[int]] = [[0] * (steps + 1) for _ in range(num_plots + 1)]
    dp[0][0] = 0.0

    for i in range(1, num_plots + 1):
        candidates = plot_choices[i - 1]
        for c in range(steps + 1):
            best_val = -1e9
            best_idx = 0
            for cand_idx, (k, _, u_val) in enumerate(candidates):
                if k <= c:
                    prev = dp[i - 1][c - k]
                    if prev > -1e8:
                        cand_val = prev + u_val
                        if cand_val > best_val:
                            best_val = cand_val
                            best_idx = cand_idx
            dp[i][c] = best_val
            backtrack[i][c] = best_idx

    # Find optimal discrete terminal state
    best_c = 0
    best_obj = -1e9
    for c in range(steps + 1):
        if dp[num_plots][c] > best_obj:
            best_obj = dp[num_plots][c]
            best_c = c

    # Backtrack to reconstruct plot allocations
    curr_c = best_c
    refined_alloc_map: Dict[str, float] = {}
    for i in range(num_plots, 0, -1):
        p_id = str(plots_data[i - 1].get("plot_identifier") or plots_data[i - 1].get("id") or f"P-{i}")
        dem = max(0.0, float(plots_data[i - 1].get("remaining_demand", plots_data[i - 1].get("water_demand", 0.0))))
        cand_idx = backtrack[i][curr_c]
        k, extra_w, _ = plot_choices[i - 1][cand_idx]
        base_w = survival_allocations.get(p_id, 0.0)
        refined_alloc_map[p_id] = round(min(dem, base_w + extra_w), 2)
        curr_c -= k

    # Local Neighborhood Delta-Transfer Search:
    # Starting from the DP solution, evaluate pairwise water transfers
    delta = max(0.1, step_size / 2.0)
    for _ in range(max_local_refinement_steps):
        best_delta_gain = 0.0
        best_donor_id = None
        best_receiver_id = None

        for j_idx, donor in enumerate(plots_data):
            d_id = str(donor.get("plot_identifier") or donor.get("id") or f"P-{j_idx+1}")
            if refined_alloc_map.get(d_id, 0.0) < delta:
                continue
            d_dem = max(0.0, float(donor.get("remaining_demand", donor.get("water_demand", 0.0))))
            d_val = float(donor.get("crop_value", donor.get("total_potential_value", 2000.0)))
            d_ky = float(donor.get("sensitivity_factor", 1.0))
            d_prio = int(donor.get("priority", 3))
            d_cost = float(donor.get("cost_per_unit", donor.get("cost_per_liter", 0.05)))

            for i_idx, rec in enumerate(plots_data):
                if i_idx == j_idx:
                    continue
                r_id = str(rec.get("plot_identifier") or rec.get("id") or f"P-{i_idx+1}")
                r_dem = max(0.0, float(rec.get("remaining_demand", rec.get("water_demand", 0.0))))
                if refined_alloc_map.get(r_id, 0.0) + delta > r_dem:
                    continue
                r_val = float(rec.get("crop_value", rec.get("total_potential_value", 2000.0)))
                r_ky = float(rec.get("sensitivity_factor", 1.0))
                r_prio = int(rec.get("priority", 3))
                r_cost = float(rec.get("cost_per_unit", rec.get("cost_per_liter", 0.05)))

                w_d = refined_alloc_map[d_id]
                w_r = refined_alloc_map[r_id]

                u_d_cur, _, _, _ = calculate_plot_utility(w_d, d_dem, d_val, d_ky, d_prio, d_cost, lambda_penalty)
                u_r_cur, _, _, _ = calculate_plot_utility(w_r, r_dem, r_val, r_ky, r_prio, r_cost, lambda_penalty)

                u_d_new, _, _, _ = calculate_plot_utility(w_d - delta, d_dem, d_val, d_ky, d_prio, d_cost, lambda_penalty)
                u_r_new, _, _, _ = calculate_plot_utility(w_r + delta, r_dem, r_val, r_ky, r_prio, r_cost, lambda_penalty)

                gain = (u_d_new + u_r_new) - (u_d_cur + u_r_cur)
                if gain > best_delta_gain:
                    best_delta_gain = gain
                    best_donor_id = d_id
                    best_receiver_id = r_id

        if best_delta_gain > 0.05 and best_donor_id and best_receiver_id:
            refined_alloc_map[best_donor_id] = round(refined_alloc_map[best_donor_id] - delta, 2)
            refined_alloc_map[best_receiver_id] = round(refined_alloc_map[best_receiver_id] + delta, 2)
        else:
            break

    # Strictly enforce total water budget constraint
    tot_refined_w = sum(refined_alloc_map.values())
    if tot_refined_w > budget:
        excess = tot_refined_w - budget
        # Trim excess from plots with lowest marginal sensitivity
        sorted_for_trim = sorted(
            plots_data,
            key=lambda x: (
                float(x.get("sensitivity_factor", 1.0)),
                int(x.get("priority", 3)),
            ),
        )
        for p_t in sorted_for_trim:
            p_tid = str(p_t.get("plot_identifier") or p_t.get("id") or "PLOT")
            curr_val = refined_alloc_map[p_tid]
            deduct = min(excess, curr_val)
            refined_alloc_map[p_tid] = round(curr_val - deduct, 2)
            excess -= deduct
            if excess <= 0.001:
                break

    refinement_time_ms = (time.perf_counter() - t_ref_start) * 1000.0

    # -----------------------------------------------------------------------------------
    # Step 3: Compare Refined Solution with Greedy Baseline & Retain Best Candidate
    # -----------------------------------------------------------------------------------
    refined_utilities: Dict[str, float] = {}
    for p in plots_data:
        p_id = str(p.get("plot_identifier") or p.get("id") or "PLOT")
        w_r = refined_alloc_map.get(p_id, 0.0)
        dem = max(0.0, float(p.get("remaining_demand", p.get("water_demand", 0.0))))
        val = float(p.get("crop_value", p.get("total_potential_value", 2000.0)))
        ky = float(p.get("sensitivity_factor", 1.0))
        prio = int(p.get("priority", 3))
        cost_u = float(p.get("cost_per_unit", p.get("cost_per_liter", 0.05)))

        u_r, _, _, _ = calculate_plot_utility(
            w_r, dem, val, ky, prio, cost_u, lambda_penalty
        )
        refined_utilities[p_id] = u_r

    refined_objective = round(sum(refined_utilities.values()), 2)

    # Comparison under identical objective:
    # Retain the refined solution if it improves or ties the Greedy baseline;
    # otherwise, safely fallback to the Greedy candidate.
    was_refined_better = refined_objective >= initial_objective

    final_alloc_map = refined_alloc_map if was_refined_better else greedy_alloc_map
    final_objective = max(initial_objective, refined_objective)
    refinement_gain = round(final_objective - initial_objective, 2)

    # -----------------------------------------------------------------------------------
    # Step 4: Compile Output Allocation Items and Metrics
    # -----------------------------------------------------------------------------------
    allocations: List[HybridAllocationItem] = []
    total_allocated = 0.0
    total_cost = 0.0

    for p in plots_data:
        p_id = str(p.get("plot_identifier") or p.get("id") or "PLOT")
        p_name = str(p.get("name") or f"Plot {p_id}")
        dem = max(0.0, float(p.get("remaining_demand", p.get("water_demand", 0.0))))
        val = float(p.get("crop_value", p.get("total_potential_value", 2000.0)))
        ky = float(p.get("sensitivity_factor", 1.0))
        prio = int(p.get("priority", 3))
        cost_u = float(p.get("cost_per_unit", p.get("cost_per_liter", 0.05)))

        w_final = final_alloc_map.get(p_id, 0.0)
        w_final = max(0.0, min(dem, w_final))
        w_greedy = greedy_alloc_map.get(p_id, 0.0)
        w_refined = refined_alloc_map.get(p_id, 0.0)

        unmet = max(0.0, round(dem - w_final, 2))
        cov_pct = round((w_final / dem * 100.0) if dem > 0 else 100.0, 2)
        plot_cost = round(w_final * cost_u, 2)

        # FAO-33 yield preservation percentage
        deficit = 1.0 - (w_final / dem if dem > 0 else 1.0)
        yield_pres_pct = round(max(0.0, 1.0 - (ky * deficit)) * 100.0, 2)

        u_init = initial_utilities.get(p_id, 0.0)
        u_final = refined_utilities.get(p_id, 0.0) if was_refined_better else u_init

        total_allocated += w_final
        total_cost += plot_cost

        allocations.append(
            HybridAllocationItem(
                plot_identifier=p_id,
                plot_name=p_name,
                remaining_demand=round(dem, 2),
                initial_greedy_allocated=round(w_greedy, 2),
                refined_allocated=round(w_refined, 2),
                allocated_water=round(w_final, 2),
                unmet_demand=unmet,
                coverage_pct=cov_pct,
                initial_utility=round(u_init, 2),
                final_utility=round(u_final, 2),
                cost=plot_cost,
                yield_preservation_pct=yield_pres_pct,
            )
        )

    total_time_ms = (time.perf_counter() - total_start_time) * 1000.0
    total_allocated = round(total_allocated, 2)
    unmet_total = max(0.0, round(total_demand - total_allocated, 2))
    utilization = round(min(100.0, (total_allocated / budget * 100.0)) if budget > 0 else 100.0, 2)

    return HybridResult(
        available_water=round(budget, 2),
        total_demand=round(total_demand, 2),
        total_allocated=total_allocated,
        unmet_demand=unmet_total,
        water_utilization_pct=utilization,
        total_cost=round(total_cost, 2),
        initial_objective=initial_objective,
        refined_objective=refined_objective,
        final_objective=final_objective,
        was_refined_better=was_refined_better,
        refinement_gain=refinement_gain,
        greedy_time_ms=round(greedy_time_ms, 3),
        refinement_time_ms=round(refinement_time_ms, 3),
        execution_time_ms=round(total_time_ms, 3),
        allocations=allocations,
    )


# ---------------------------------------------------------------------------------------
# CropFlow Framework Integration Wrapper
# ---------------------------------------------------------------------------------------
def run_hybrid_allocation(
    plots: List[Any],
    available_water: float,
    energy_rate: float = 0.045,
    labor_rate: float = 14.0,
    pump_capacity: float = 25.0,
    scenario_name: str = "Standard",
    step_count: int = 60,
) -> Any:
    """CropFlow domain wrapper adapting Plot domain models to HybridResult and OptimizationResult."""
    # Convert Plot domain models to pure dictionary representations
    plots_payload = []
    for idx, p in enumerate(plots):
        plots_payload.append({
            "plot_identifier": getattr(p, "plot_identifier", getattr(p, "name", f"P-{idx+1}")),
            "name": getattr(p, "name", f"Plot {idx+1}"),
            "remaining_demand": getattr(p, "water_demand", 100.0),
            "crop_value": getattr(p, "total_potential_value", 2000.0),
            "sensitivity_factor": getattr(p, "sensitivity_factor", 1.0),
            "priority": getattr(p, "priority", 3),
            "moisture_stress": getattr(p, "moisture_stress_index", 0.5),
            "cost_per_unit": energy_rate,
            "id": getattr(p, "id", None),
        })

    # Run the pure Hybrid allocation algorithm
    pure_res = hybrid_allocate_pure(
        plots_data=plots_payload,
        available_water=available_water,
        step_count=step_count,
    )

    # Bridge to OptimizationResult using app.algorithms.metrics
    from app.algorithms.metrics import evaluate_allocation

    raw_allocs = {}
    for idx, p in enumerate(plots):
        key = getattr(p, "id", None) if getattr(p, "id", None) is not None else idx
        raw_allocs[key] = pure_res.allocations[idx].allocated_water

    result = evaluate_allocation(
        plots=plots,
        raw_allocations=raw_allocs,
        available_water=available_water,
        energy_rate=energy_rate,
        labor_rate=labor_rate,
        pump_capacity=pump_capacity,
        algorithm_name="Hybrid (Greedy + DP)",
        scenario_name=scenario_name,
        execution_time_ms=pure_res.execution_time_ms,
    )

    # Attach hybrid pre/post metadata for analysis and logging
    result.initial_objective = pure_res.initial_objective
    result.refined_objective = pure_res.refined_objective
    result.final_objective = pure_res.final_objective
    result.was_refined_better = pure_res.was_refined_better
    result.refinement_gain = pure_res.refinement_gain
    result.greedy_time_ms = pure_res.greedy_time_ms
    result.refinement_time_ms = pure_res.refinement_time_ms

    return result
