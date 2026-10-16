"""Comprehensive unit tests for the Greedy water-allocation algorithm.

Covers:
1. Worked numerical example verification (exact mathematical matches)
2. Deterministic tie-breaking rules (demand ascending & plot identifier alphabetical)
3. Allocation limits enforcement
4. Edge cases: empty plots, zero water, negative water, infinite water
5. Standalone framework-independent pure dictionary inputs (greedy_allocate_pure)
6. Domain Plot wrapper (run_greedy_allocation)
"""

import unittest
from app.algorithms.greedy import (
    calculate_priority_score,
    greedy_allocate_pure,
    run_greedy_allocation,
)
from app.models.farm import Plot


class TestGreedyWaterAllocation(unittest.TestCase):
    """Test suite verifying greedy allocation, weights, tie-breaking, and boundary limits."""

    def test_worked_numerical_example(self):
        """Verify the exact mathematical results of the worked numerical example documented in greedy.py."""
        # Available budget: 100.0 m3, cost: $0.05 / m3
        # Plot A (P-101): Demand = 60.0, Priority = 5, Stress = 0.8, Ky = 1.4, Benefit = 0.9
        # Plot B (P-102): Demand = 50.0, Priority = 3, Stress = 0.5, Ky = 0.9, Benefit = 0.5
        # Plot C (P-103): Demand = 40.0, Priority = 2, Stress = 0.3, Ky = 0.5, Benefit = 0.4
        plots_data = [
            {
                "plot_identifier": "P-101",
                "name": "Plot A",
                "remaining_demand": 60.0,
                "priority": 5,
                "moisture_stress": 0.8,
                "sensitivity_factor": 1.4,
                "benefit_factor": 0.9,
                "cost_per_unit": 0.05,
            },
            {
                "plot_identifier": "P-102",
                "name": "Plot B",
                "remaining_demand": 50.0,
                "priority": 3,
                "moisture_stress": 0.5,
                "sensitivity_factor": 0.9,
                "benefit_factor": 0.5,
                "cost_per_unit": 0.05,
            },
            {
                "plot_identifier": "P-103",
                "name": "Plot C",
                "remaining_demand": 40.0,
                "priority": 2,
                "moisture_stress": 0.3,
                "sensitivity_factor": 0.5,
                "benefit_factor": 0.4,
                "cost_per_unit": 0.05,
            },
        ]

        # Priority scores verification
        score_a = calculate_priority_score(5, 0.8, 1.4, 0.9, 0.05)
        score_b = calculate_priority_score(3, 0.5, 0.9, 0.5, 0.05)
        score_c = calculate_priority_score(2, 0.3, 0.5, 0.4, 0.05)

        # Expected: A (17.9667) > B (11.000) > C (6.9667)
        self.assertAlmostEqual(score_a, 17.9667, delta=0.01)
        self.assertAlmostEqual(score_b, 11.0000, delta=0.01)
        self.assertAlmostEqual(score_c, 6.9667, delta=0.01)
        self.assertGreater(score_a, score_b)
        self.assertGreater(score_b, score_c)

        # Execute pure greedy allocation
        result = greedy_allocate_pure(plots_data, available_water=100.0)

        # Check ranking order
        self.assertEqual(result.ranking_order, ["P-101", "P-102", "P-103"])

        # Check per-plot allocations
        alloc_map = {a.plot_identifier: a for a in result.allocations}

        # Plot A should be 100% fulfilled (60.0 allocated, 0 unmet)
        self.assertAlmostEqual(alloc_map["P-101"].allocated_water, 60.0, delta=0.01)
        self.assertAlmostEqual(alloc_map["P-101"].unmet_demand, 0.0, delta=0.01)
        self.assertEqual(alloc_map["P-101"].rank, 1)

        # Plot B should receive remaining 40.0 (unmet = 10.0)
        self.assertAlmostEqual(alloc_map["P-102"].allocated_water, 40.0, delta=0.01)
        self.assertAlmostEqual(alloc_map["P-102"].unmet_demand, 10.0, delta=0.01)
        self.assertEqual(alloc_map["P-102"].rank, 2)

        # Plot C should receive 0.0 (unmet = 40.0)
        self.assertAlmostEqual(alloc_map["P-103"].allocated_water, 0.0, delta=0.01)
        self.assertAlmostEqual(alloc_map["P-103"].unmet_demand, 40.0, delta=0.01)
        self.assertEqual(alloc_map["P-103"].rank, 3)

        # Check overall aggregate metrics
        self.assertAlmostEqual(result.total_allocated, 100.0, delta=0.01)
        self.assertAlmostEqual(result.unmet_demand, 50.0, delta=0.01)
        self.assertAlmostEqual(result.water_utilization_pct, 100.0, delta=0.01)
        # Total cost: (60 + 40) * 0.05 = $5.00
        self.assertAlmostEqual(result.total_cost, 5.0, delta=0.01)
        self.assertGreater(result.execution_time_ms, 0.0)

    def test_deterministic_tie_breaking_by_demand(self):
        """When priority scores are tied, smaller demand is ranked higher (secondary tie-breaker)."""
        # Both plots have identical parameters yielding identical scores, but different demands
        tied_plots = [
            {
                "plot_identifier": "P-LARGE",
                "remaining_demand": 80.0,
                "priority": 4,
                "moisture_stress": 0.6,
                "cost_per_unit": 0.05,
            },
            {
                "plot_identifier": "P-SMALL",
                "remaining_demand": 30.0,
                "priority": 4,
                "moisture_stress": 0.6,
                "cost_per_unit": 0.05,
            },
        ]
        result = greedy_allocate_pure(tied_plots, available_water=50.0)

        # P-SMALL should be ranked 1st because remaining_demand 30.0 < 80.0
        self.assertEqual(result.ranking_order, ["P-SMALL", "P-LARGE"])
        alloc_map = {a.plot_identifier: a for a in result.allocations}
        self.assertEqual(alloc_map["P-SMALL"].allocated_water, 30.0)
        self.assertEqual(alloc_map["P-LARGE"].allocated_water, 20.0)

    def test_deterministic_tie_breaking_by_identifier(self):
        """When both score and demand are tied, plot identifier is lexicographically compared (tertiary tie-breaker)."""
        tied_plots = [
            {"plot_identifier": "PLOT-Z", "remaining_demand": 50.0, "priority": 3, "cost_per_unit": 0.05},
            {"plot_identifier": "PLOT-A", "remaining_demand": 50.0, "priority": 3, "cost_per_unit": 0.05},
        ]
        result = greedy_allocate_pure(tied_plots, available_water=60.0)

        # PLOT-A precedes PLOT-Z alphabetically
        self.assertEqual(result.ranking_order, ["PLOT-A", "PLOT-Z"])
        alloc_map = {a.plot_identifier: a for a in result.allocations}
        self.assertEqual(alloc_map["PLOT-A"].allocated_water, 50.0)
        self.assertEqual(alloc_map["PLOT-Z"].allocated_water, 10.0)

    def test_allocation_limits_respected(self):
        """Greedy must not exceed individual plot allocation limits even if remaining demand is higher."""
        plots = [
            {
                "plot_identifier": "P-LIMITED",
                "remaining_demand": 100.0,
                "allocation_limit": 45.0,  # e.g. pump daily quota or infiltration limit
                "priority": 5,
                "cost_per_unit": 0.05,
            }
        ]
        result = greedy_allocate_pure(plots, available_water=200.0)
        self.assertEqual(result.allocations[0].allocated_water, 45.0)
        self.assertEqual(result.allocations[0].unmet_demand, 55.0)

    def test_zero_and_negative_water_safety(self):
        """Zero or negative available water safely results in 0 allocations without errors."""
        plots = [{"plot_identifier": "P-1", "remaining_demand": 50.0, "priority": 3}]

        # Zero water
        res_zero = greedy_allocate_pure(plots, available_water=0.0)
        self.assertEqual(res_zero.total_allocated, 0.0)
        self.assertEqual(res_zero.unmet_demand, 50.0)
        self.assertEqual(res_zero.total_cost, 0.0)

        # Negative water
        res_neg = greedy_allocate_pure(plots, available_water=-100.0)
        self.assertEqual(res_neg.total_allocated, 0.0)
        self.assertEqual(res_neg.available_water, 0.0)

    def test_empty_plot_input(self):
        """Empty plot list returns a valid zero-result object."""
        result = greedy_allocate_pure([], available_water=100.0)
        self.assertEqual(result.total_allocated, 0.0)
        self.assertEqual(result.total_demand, 0.0)
        self.assertEqual(len(result.allocations), 0)

    def test_domain_plot_wrapper(self):
        """Verify run_greedy_allocation integration wrapper with Plot domain objects."""
        plot_urgent = Plot(
            plot_identifier="P-URGENT",
            name="Urgent Plot",
            area=4.0,
            crop_type="Corn",
            growth_stage="Flowering",
            water_required_liters=200000.0,
            current_moisture=25.0,
            target_moisture=75.0,
            priority=5,
            sensitivity_factor=1.4,
            water_demand=200.0,
        )
        plot_low = Plot(
            plot_identifier="P-LOW",
            name="Low Priority Plot",
            area=3.0,
            crop_type="Cotton",
            growth_stage="Ripening",
            water_required_liters=100000.0,
            current_moisture=45.0,
            target_moisture=65.0,
            priority=1,
            sensitivity_factor=0.5,
            water_demand=100.0,
        )

        res = run_greedy_allocation([plot_urgent, plot_low], available_water=200.0)
        self.assertAlmostEqual(res.total_allocated, 200.0, delta=0.5)
        self.assertLessEqual(res.total_allocated, 200.0)


if __name__ == "__main__":
    unittest.main()
