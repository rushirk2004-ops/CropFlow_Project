"""Unit and integration tests for CropFlow's Hybrid Allocation Strategy."""

import unittest
from app.algorithms.dynamic_programming import calculate_plot_utility, run_dp_allocation
from app.algorithms.greedy import run_greedy_allocation
from app.algorithms.hybrid import (
    HybridAllocationItem,
    HybridResult,
    hybrid_allocate_pure,
    run_hybrid_allocation,
)
from app.models.farm import Plot


class TestHybridAllocationStrategy(unittest.TestCase):
    """Test suite verifying feasibility, consistency, and refinement of the Hybrid Strategy."""

    def setUp(self):
        """Set up standard benchmark plots with diverse agronomic sensitivities."""
        self.sample_payload = [
            {
                "plot_identifier": "P-101",
                "name": "Corn Flowering",
                "remaining_demand": 196.0,
                "crop_value": 9600.0,
                "sensitivity_factor": 1.40,
                "priority": 5,
                "moisture_stress": 0.80,
                "cost_per_unit": 0.045,
            },
            {
                "plot_identifier": "P-102",
                "name": "Tomato Flowering",
                "remaining_demand": 130.0,
                "crop_value": 10500.0,
                "sensitivity_factor": 1.35,
                "priority": 5,
                "moisture_stress": 0.70,
                "cost_per_unit": 0.045,
            },
            {
                "plot_identifier": "P-103",
                "name": "Wheat Vegetative",
                "remaining_demand": 180.0,
                "crop_value": 8000.0,
                "sensitivity_factor": 0.85,
                "priority": 3,
                "moisture_stress": 0.40,
                "cost_per_unit": 0.045,
            },
            {
                "plot_identifier": "P-104",
                "name": "Cotton Ripening",
                "remaining_demand": 108.0,
                "crop_value": 7200.0,
                "sensitivity_factor": 0.50,
                "priority": 2,
                "moisture_stress": 0.30,
                "cost_per_unit": 0.045,
            },
        ]
        # Total demand = 196 + 130 + 180 + 108 = 614.0
        self.domain_plots = [
            Plot(
                id=1,
                plot_identifier="P-101",
                name="Corn Flowering",
                size_hectares=4.0,
                crop_type="Corn",
                growth_stage="Flowering",
                current_moisture=26.0,
                target_moisture=75.0,
                water_demand=196.0,
                crop_value_per_ha=2400.0,
                sensitivity_factor=1.40,
                priority=5,
            ),
            Plot(
                id=2,
                plot_identifier="P-102",
                name="Tomato Flowering",
                size_hectares=2.5,
                crop_type="Tomato",
                growth_stage="Flowering",
                current_moisture=28.0,
                target_moisture=80.0,
                water_demand=130.0,
                crop_value_per_ha=4200.0,
                sensitivity_factor=1.35,
                priority=5,
            ),
            Plot(
                id=3,
                plot_identifier="P-103",
                name="Wheat Vegetative",
                size_hectares=5.0,
                crop_type="Wheat",
                growth_stage="Vegetative",
                current_moisture=34.0,
                target_moisture=70.0,
                water_demand=180.0,
                crop_value_per_ha=1600.0,
                sensitivity_factor=0.85,
                priority=3,
            ),
            Plot(
                id=4,
                plot_identifier="P-104",
                name="Cotton Ripening",
                size_hectares=4.0,
                crop_type="Cotton",
                growth_stage="Ripening",
                current_moisture=38.0,
                target_moisture=65.0,
                water_demand=108.0,
                crop_value_per_ha=1800.0,
                sensitivity_factor=0.50,
                priority=2,
            ),
        ]

    def test_initial_greedy_baseline_generation(self):
        """Verify that the initial baseline is generated via Greedy and is feasible."""
        budget = 307.0
        result = hybrid_allocate_pure(self.sample_payload, budget)

        self.assertIsInstance(result, HybridResult)
        self.assertEqual(len(result.allocations), 4)

        # Baseline Greedy allocation checks
        total_greedy = sum(a.initial_greedy_allocated for a in result.allocations)
        self.assertLessEqual(total_greedy, budget + 0.05)

        for item in result.allocations:
            self.assertGreaterEqual(item.initial_greedy_allocated, 0.0)
            self.assertLessEqual(item.initial_greedy_allocated, item.remaining_demand + 0.05)

    def test_non_regression_property_under_same_objective(self):
        """Verify that the final objective is never worse than the initial Greedy baseline."""
        test_budgets = [50.0, 150.0, 307.0, 450.0, 614.0]

        for budget in test_budgets:
            result = hybrid_allocate_pure(self.sample_payload, budget)

            # Mathematical invariant: final_objective >= initial_objective
            self.assertGreaterEqual(
                result.final_objective,
                result.initial_objective - 0.01,
                f"Hybrid regressed below greedy baseline at budget {budget}: "
                f"initial={result.initial_objective}, final={result.final_objective}",
            )
            self.assertGreaterEqual(result.refinement_gain, -0.01)

            # If refined was better, final_objective matches refined_objective
            if result.was_refined_better:
                self.assertAlmostEqual(result.final_objective, result.refined_objective, places=1)
            else:
                self.assertAlmostEqual(result.final_objective, result.initial_objective, places=1)

    def test_water_budget_and_demand_constraints(self):
        """Verify that allocated water never exceeds available water or individual plot demands."""
        test_budgets = [0.0, 25.0, 100.0, 250.0, 307.0, 500.0, 614.0, 800.0]

        for budget in test_budgets:
            result = hybrid_allocate_pure(self.sample_payload, budget)

            # Sum of allocations <= available water
            self.assertLessEqual(
                result.total_allocated,
                budget + 0.05,
                f"Budget violated at {budget}: total_allocated={result.total_allocated}",
            )

            # Each plot allocation in [0, remaining_demand]
            for item in result.allocations:
                self.assertGreaterEqual(item.allocated_water, 0.0)
                self.assertLessEqual(item.allocated_water, item.remaining_demand + 0.05)
                self.assertAlmostEqual(
                    item.unmet_demand,
                    round(item.remaining_demand - item.allocated_water, 2),
                    places=2,
                )

    def test_record_runtimes_and_objectives(self):
        """Verify that runtimes and pre/post objectives are accurately recorded."""
        result = hybrid_allocate_pure(self.sample_payload, 307.0)

        self.assertGreater(result.execution_time_ms, 0.0)
        self.assertGreaterEqual(result.greedy_time_ms, 0.0)
        self.assertGreaterEqual(result.refinement_time_ms, 0.0)
        self.assertGreater(result.initial_objective, 0.0)
        self.assertGreater(result.final_objective, 0.0)

        # Dictionary serialization
        res_dict = result.to_dict()
        self.assertIn("initial_objective", res_dict)
        self.assertIn("refined_objective", res_dict)
        self.assertIn("final_objective", res_dict)
        self.assertIn("was_refined_better", res_dict)
        self.assertIn("refinement_gain", res_dict)
        self.assertIn("greedy_time_ms", res_dict)
        self.assertIn("refinement_time_ms", res_dict)

    def test_zero_and_negative_water_safety(self):
        """Verify safe handling of zero or negative water budget."""
        for w in [0.0, -10.0]:
            result = hybrid_allocate_pure(self.sample_payload, w)
            self.assertEqual(result.total_allocated, 0.0)
            self.assertEqual(result.unmet_demand, 614.0)
            self.assertEqual(result.total_cost, 0.0)
            for item in result.allocations:
                self.assertEqual(item.allocated_water, 0.0)
                self.assertEqual(item.unmet_demand, item.remaining_demand)

    def test_empty_plots_input(self):
        """Verify safe handling of empty plot lists."""
        result = hybrid_allocate_pure([], 100.0)
        self.assertEqual(result.total_allocated, 0.0)
        self.assertEqual(result.total_demand, 0.0)
        self.assertEqual(len(result.allocations), 0)

    def test_abundant_water_allocation(self):
        """When water is abundant, all plots receive 100% without exceeding demand."""
        abundant_water = 1000.0  # total demand is 614.0
        result = hybrid_allocate_pure(self.sample_payload, abundant_water)

        self.assertAlmostEqual(result.total_allocated, 614.0, places=1)
        self.assertAlmostEqual(result.unmet_demand, 0.0, places=1)
        for item in result.allocations:
            self.assertAlmostEqual(item.allocated_water, item.remaining_demand, places=1)
            self.assertEqual(item.unmet_demand, 0.0)
            self.assertEqual(item.coverage_pct, 100.0)

    def test_domain_plot_wrapper_and_independent_callability(self):
        """Verify that run_hybrid_allocation operates independently alongside Greedy and DP."""
        budget = 307.0

        res_g = run_greedy_allocation(self.domain_plots, budget)
        res_dp = run_dp_allocation(self.domain_plots, budget)
        res_h = run_hybrid_allocation(self.domain_plots, budget)

        # All 3 strategies return valid OptimizationResult models
        for res in [res_g, res_dp, res_h]:
            self.assertLessEqual(res.total_allocated, budget + 0.1)
            self.assertGreater(res.total_benefit, 0.0)
            self.assertGreaterEqual(res.fairness_index, 0.0)
            self.assertLessEqual(res.fairness_index, 1.0)
            self.assertEqual(len(res.allocations), 4)

        # Verify hybrid attached metadata
        self.assertTrue(hasattr(res_h, "initial_objective"))
        self.assertTrue(hasattr(res_h, "final_objective"))
        self.assertTrue(hasattr(res_h, "refinement_gain"))
        self.assertTrue(hasattr(res_h, "was_refined_better"))


if __name__ == "__main__":
    unittest.main()
