"""Comprehensive audit and invariant verification test suite for CropFlow.

Tests:
1. Zero available water (W = 0).
2. Water supply exceeding total demand (W > sum(D_i)).
3. Water supply below total demand (W < sum(D_i)).
4. Zero-demand plots (D_i = 0).
5. Invalid or negative inputs handling.
6. Greedy allocation feasibility.
7. Dynamic Programming optimality on small cases exhaustively checked.
8. Hybrid solution feasibility and objective consistency.
9. Irrigation scheduling conflict prevention (pump & infiltration limits).
10. Database persistence of runs, parameters, and allocations.
11. Flask route integration across endpoints.

Invariant checks enforced on every result:
- Sum(allocated_water) <= available_water
- 0 <= allocated_water <= remaining_demand (for all plots)
"""

import itertools
import math
import unittest

from app import create_app
from app.algorithms.dynamic_programming import (
    calculate_plot_utility,
    dp_allocate_pure,
    run_dp_allocation,
)
from app.algorithms.greedy import (
    greedy_allocate_pure,
    run_greedy_allocation,
)
from app.algorithms.hybrid import (
    hybrid_allocate_pure,
    run_hybrid_allocation,
)
from app.models.farm import Farm, Plot
from app.services.preprocessing import (
    ValidationError,
    validate_farm_input,
    validate_plot_input,
)
from app.services.scheduler import build_irrigation_schedule
from database.db import get_db_connection, seed_sample_data


class TestCropFlowAudit(unittest.TestCase):
    """Audit suite verifying physical invariants, mathematical optimality, and edge cases."""

    def setUp(self):
        """Set up benchmark datasets and testing app context."""
        self.app = create_app("testing")
        self.client = self.app.test_client()
        self.db_path = self.app.config["DATABASE_PATH"]
        self.farm_id = seed_sample_data(db_path=self.db_path, force=True)

        self.standard_plots_data = [
            {
                "plot_identifier": "P-1",
                "name": "Corn Flowering",
                "remaining_demand": 120.0,
                "crop_value": 4800.0,
                "sensitivity_factor": 1.4,
                "priority": 5,
                "moisture_stress": 0.8,
                "cost_per_unit": 0.045,
            },
            {
                "plot_identifier": "P-2",
                "name": "Tomato Vegetative",
                "remaining_demand": 80.0,
                "crop_value": 5200.0,
                "sensitivity_factor": 1.1,
                "priority": 4,
                "moisture_stress": 0.6,
                "cost_per_unit": 0.045,
            },
            {
                "plot_identifier": "P-3",
                "name": "Wheat Ripening",
                "remaining_demand": 60.0,
                "crop_value": 3000.0,
                "sensitivity_factor": 0.7,
                "priority": 2,
                "moisture_stress": 0.3,
                "cost_per_unit": 0.045,
            },
        ]
        # Total demand = 120 + 80 + 60 = 260.0

    def assert_cropflow_invariants(self, result, available_water, plots_data):
        """Enforce core invariants on any allocation result."""
        budget = max(0.0, float(available_water))

        # Invariant 1: Sum of allocated water <= available water
        self.assertLessEqual(
            result.total_allocated,
            budget + 0.05,
            f"Invariant violation: Total allocated {result.total_allocated} exceeds available budget {budget}",
        )

        demands_map = {
            p.get("plot_identifier", p.get("id", "")): float(p.get("remaining_demand", p.get("water_demand", 0.0)))
            for p in plots_data
        }

        # Invariant 2: For every plot, 0 <= allocated_water <= remaining_demand
        for item in result.allocations:
            alloc = item.allocated_water
            p_id = getattr(item, "plot_identifier", getattr(item, "plot_id", ""))
            demand = demands_map.get(p_id, getattr(item, "demand", getattr(item, "remaining_demand", 0.0)))

            self.assertGreaterEqual(
                alloc,
                -0.001,
                f"Invariant violation: Negative allocation {alloc} for plot {p_id}",
            )
            self.assertLessEqual(
                alloc,
                demand + 0.05,
                f"Invariant violation: Allocation {alloc} exceeds demand {demand} for plot {p_id}",
            )

    # -----------------------------------------------------------------------------------
    # Audit 1: Zero Available Water (W = 0)
    # -----------------------------------------------------------------------------------
    def test_audit_zero_available_water(self):
        """Verify behavior when available water is 0 across all 3 algorithms."""
        budget = 0.0

        for name, solver in [
            ("Greedy", greedy_allocate_pure),
            ("DP", dp_allocate_pure),
            ("Hybrid", hybrid_allocate_pure),
        ]:
            res = solver(self.standard_plots_data, budget)
            self.assertEqual(res.total_allocated, 0.0, f"{name} allocated water when budget was 0")
            self.assertAlmostEqual(res.unmet_demand, 260.0, places=2)
            self.assertEqual(res.total_cost, 0.0)
            self.assert_cropflow_invariants(res, budget, self.standard_plots_data)

    # -----------------------------------------------------------------------------------
    # Audit 2: Water Supply Exceeding Total Demand (W > sum(D_i))
    # -----------------------------------------------------------------------------------
    def test_audit_water_supply_exceeds_total_demand(self):
        """When water is abundant, all plots get 100% without overallocation."""
        abundant_water = 500.0  # Total demand is 260.0

        for name, solver in [
            ("Greedy", greedy_allocate_pure),
            ("DP", dp_allocate_pure),
            ("Hybrid", hybrid_allocate_pure),
        ]:
            res = solver(self.standard_plots_data, abundant_water)
            self.assertAlmostEqual(res.total_allocated, 260.0, places=1, msg=f"{name} failed full allocation")
            self.assertAlmostEqual(res.unmet_demand, 0.0, places=1)
            for item in res.allocations:
                self.assertAlmostEqual(item.allocated_water, item.remaining_demand, places=1)
                self.assertEqual(item.unmet_demand, 0.0)
                self.assertEqual(item.coverage_pct, 100.0)
            self.assert_cropflow_invariants(res, abundant_water, self.standard_plots_data)

    # -----------------------------------------------------------------------------------
    # Audit 3: Water Supply Below Total Demand (W < sum(D_i))
    # -----------------------------------------------------------------------------------
    def test_audit_water_supply_below_total_demand(self):
        """Under severe water deficit, water is bounded by budget and prioritized appropriately."""
        scarce_water = 100.0  # Total demand is 260.0

        for name, solver in [
            ("Greedy", greedy_allocate_pure),
            ("DP", dp_allocate_pure),
            ("Hybrid", hybrid_allocate_pure),
        ]:
            res = solver(self.standard_plots_data, scarce_water)
            self.assertLessEqual(res.total_allocated, scarce_water + 0.05)
            self.assertGreater(res.unmet_demand, 0.0)
            self.assert_cropflow_invariants(res, scarce_water, self.standard_plots_data)

    # -----------------------------------------------------------------------------------
    # Audit 4: Zero-Demand Plots (D_i = 0)
    # -----------------------------------------------------------------------------------
    def test_audit_zero_demand_plots(self):
        """Plots with 0 remaining demand must receive 0 water without division by zero errors."""
        plots_with_zero = [
            {
                "plot_identifier": "P-Zero",
                "name": "Harvested Plot",
                "remaining_demand": 0.0,
                "crop_value": 0.0,
                "sensitivity_factor": 1.0,
                "priority": 1,
                "moisture_stress": 0.0,
                "cost_per_unit": 0.045,
            },
            {
                "plot_identifier": "P-Active",
                "name": "Active Plot",
                "remaining_demand": 80.0,
                "crop_value": 4000.0,
                "sensitivity_factor": 1.2,
                "priority": 4,
                "moisture_stress": 0.7,
                "cost_per_unit": 0.045,
            },
        ]
        budget = 50.0

        for name, solver in [
            ("Greedy", greedy_allocate_pure),
            ("DP", dp_allocate_pure),
            ("Hybrid", hybrid_allocate_pure),
        ]:
            res = solver(plots_with_zero, budget)
            zero_item = next(a for a in res.allocations if a.plot_identifier == "P-Zero")
            self.assertEqual(zero_item.allocated_water, 0.0)
            self.assertEqual(zero_item.unmet_demand, 0.0)
            self.assertEqual(zero_item.coverage_pct, 100.0)
            self.assert_cropflow_invariants(res, budget, plots_with_zero)

    # -----------------------------------------------------------------------------------
    # Audit 5: Invalid or Negative Inputs Handling
    # -----------------------------------------------------------------------------------
    def test_audit_invalid_or_negative_inputs(self):
        """Reject invalid or negative numeric inputs with clear validation errors."""
        # Negative water budget in pure solver clamps safely to 0.0
        res_neg = greedy_allocate_pure(self.standard_plots_data, -50.0)
        self.assertEqual(res_neg.total_allocated, 0.0)

        # Service-level validation rejects negative inputs
        with self.assertRaises(ValidationError):
            validate_farm_input({"name": "Test", "total_available_water_liters": -100})

        with self.assertRaises(ValidationError):
            validate_plot_input({"plot_identifier": "P-1", "area": -2.0, "current_moisture": 50})

        with self.assertRaises(ValidationError):
            validate_plot_input({"plot_identifier": "P-1", "area": 2.0, "current_moisture": 120.0})

        with self.assertRaises(ValidationError):
            validate_plot_input({"plot_identifier": "P-1", "area": 2.0, "current_moisture": -5.0})

    # -----------------------------------------------------------------------------------
    # Audit 6: Greedy Allocation Feasibility
    # -----------------------------------------------------------------------------------
    def test_audit_greedy_allocation_feasibility(self):
        """Greedy must satisfy feasibility under all water capacity levels."""
        for w in [10.0, 50.0, 120.0, 200.0, 260.0, 350.0]:
            res = greedy_allocate_pure(self.standard_plots_data, w)
            self.assert_cropflow_invariants(res, w, self.standard_plots_data)

    # -----------------------------------------------------------------------------------
    # Audit 7: Dynamic Programming Optimality on Small Exhaustive Case
    # -----------------------------------------------------------------------------------
    def test_audit_dp_optimality_on_small_exhaustive_case(self):
        """Verify that DP achieves the exact mathematical global optimum on an exhaustively verified case."""
        # 3 small plots, small budget, coarse quantum for fast brute-force permutation
        small_plots = [
            {"plot_identifier": "P-A", "remaining_demand": 20.0, "crop_value": 1000.0, "sensitivity_factor": 1.2, "priority": 5, "cost_per_unit": 0.05},
            {"plot_identifier": "P-B", "remaining_demand": 15.0, "crop_value": 1200.0, "sensitivity_factor": 0.8, "priority": 3, "cost_per_unit": 0.05},
            {"plot_identifier": "P-C", "remaining_demand": 10.0, "crop_value": 800.0, "sensitivity_factor": 0.6, "priority": 2, "cost_per_unit": 0.05},
        ]
        quantum = 5.0
        budget = 25.0

        # Discrete choices for each plot: {0, 5, 10, ... up to demand}
        choices_a = [0.0, 5.0, 10.0, 15.0, 20.0]
        choices_b = [0.0, 5.0, 10.0, 15.0]
        choices_c = [0.0, 5.0, 10.0]

        # Brute-force exhaustive search over all feasible discrete combinations
        best_brute_obj = -1e9
        best_brute_combo = None

        for wa in choices_a:
            for wb in choices_b:
                for wc in choices_c:
                    if wa + wb + wc <= budget:
                        ua, _, _, _ = calculate_plot_utility(wa, 20.0, 1000.0, 1.2, 5, 0.05)
                        ub, _, _, _ = calculate_plot_utility(wb, 15.0, 1200.0, 0.8, 3, 0.05)
                        uc, _, _, _ = calculate_plot_utility(wc, 10.0, 800.0, 0.6, 2, 0.05)
                        tot_u = round(ua + ub + uc, 2)
                        if tot_u > best_brute_obj:
                            best_brute_obj = tot_u
                            best_brute_combo = (wa, wb, wc)

        # Run DP with exact quantum
        dp_res = dp_allocate_pure(small_plots, budget, quantum_unit=quantum)
        dp_obj = dp_res.objective_value

        self.assertAlmostEqual(
            dp_obj,
            best_brute_obj,
            places=1,
            msg=f"DP objective {dp_obj} failed to match brute-force optimum {best_brute_obj} on discrete grid",
        )
        self.assert_cropflow_invariants(dp_res, budget, small_plots)

    # -----------------------------------------------------------------------------------
    # Audit 8: Hybrid Solution Feasibility and Objective Consistency
    # -----------------------------------------------------------------------------------
    def test_audit_hybrid_feasibility_and_objective_consistency(self):
        """Hybrid must always satisfy invariants and never regress below Greedy under identical objective."""
        for budget in [30.0, 80.0, 150.0, 220.0, 260.0]:
            h_res = hybrid_allocate_pure(self.standard_plots_data, budget)
            self.assert_cropflow_invariants(h_res, budget, self.standard_plots_data)

            # Mathematical invariant: final_objective >= initial_objective
            self.assertGreaterEqual(
                h_res.final_objective,
                h_res.initial_objective - 0.01,
                f"Hybrid regressed below greedy baseline at budget {budget}",
            )

    # -----------------------------------------------------------------------------------
    # Audit 9: Irrigation Scheduling Conflict Prevention
    # -----------------------------------------------------------------------------------
    def test_audit_irrigation_scheduling_conflicts(self):
        """Schedule must prevent concurrent pump over-subscription and soil infiltration runoff."""
        plots = [
            Plot(id=1, name="P1", size_hectares=2.0, crop_type="Corn", water_demand=100.0, infiltration_rate=10.0),
            Plot(id=2, name="P2", size_hectares=3.0, crop_type="Tomato", water_demand=90.0, infiltration_rate=8.0),
        ]
        farm = Farm(id=1, name="Pump Farm", water_budget=150.0, pump_capacity=20.0, plots=plots)
        res = run_hybrid_allocation(plots, available_water=150.0)
        scheduled = build_irrigation_schedule(res, farm)

        # Infiltration check: max soil intake = infiltration (mm/h) * ha * 10
        plot_map = {p.id: p for p in plots}
        for item in scheduled.schedule:
            p = plot_map[item.plot_id]
            max_intake = p.infiltration_rate * p.size_hectares * 10.0
            self.assertLessEqual(item.flow_rate_m3h, farm.pump_capacity + 0.05)
            self.assertLessEqual(item.flow_rate_m3h, max_intake + 0.05)
            # Duration should match volume / flow_rate
            expected_dur = round(item.water_volume_m3 / item.flow_rate_m3h, 2)
            self.assertAlmostEqual(item.duration_hours, expected_dur, places=1)

    # -----------------------------------------------------------------------------------
    # Audit 10: Database Persistence of Parameters, Objectives, and Allocations
    # -----------------------------------------------------------------------------------
    def test_audit_database_persistence(self):
        """Verify that algorithm name, inputs, allocations, and objectives persist to SQLite."""
        payload = {
            "farm_id": self.farm_id,
            "algorithm": "hybrid",
            "water_override": 180.0,
            "scenario_name": "Audit Persistence Test",
            "save_run": True,
        }
        resp = self.client.post("/api/optimize", json=payload)
        self.assertEqual(resp.status_code, 200)

        data = resp.get_json()
        run_id = data.get("run_id")
        self.assertIsNotNone(run_id)

        # Query database directly using parameterized query
        conn = get_db_connection(self.db_path)
        cur = conn.cursor()
        cur.execute("SELECT * FROM optimization_runs WHERE id = ?", (run_id,))
        run_row = cur.fetchone()
        self.assertIsNotNone(run_row)
        self.assertEqual(run_row["algorithm"], "Hybrid (Greedy + DP)")
        self.assertEqual(run_row["scenario_name"], "Audit Persistence Test")
        self.assertAlmostEqual(run_row["available_water"], 180.0, places=1)

        # Check allocations table
        cur.execute("SELECT * FROM allocations WHERE run_id = ?", (run_id,))
        alloc_rows = cur.fetchall()
        self.assertGreater(len(alloc_rows), 0)

        # Check compare-runs endpoint
        comp_resp = self.client.get(f"/api/reports/compare-runs?run_ids={run_id}")
        self.assertEqual(comp_resp.status_code, 200)
        comp_data = comp_resp.get_json()
        self.assertEqual(comp_data["count"], 1)

    # -----------------------------------------------------------------------------------
    # Audit 11: Flask Route Integration
    # -----------------------------------------------------------------------------------
    def test_audit_flask_route_integration(self):
        """Verify all core endpoints respond with HTTP 200 and expected contracts."""
        endpoints = [
            ("/health", 200),
            ("/dashboard", 200),
            ("/farms", 200),
            ("/results", 200),
            ("/api/farms", 200),
            (f"/api/farms/{self.farm_id}", 200),
            ("/api/optimize/algorithms", 200),
            ("/api/scenarios", 200),
        ]
        for path, expected_status in endpoints:
            r = self.client.get(path)
            self.assertEqual(r.status_code, expected_status, f"Endpoint {path} failed with {r.status_code}")


if __name__ == "__main__":
    unittest.main()
