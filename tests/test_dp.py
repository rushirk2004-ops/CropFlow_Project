"""Comprehensive unit tests for the Dynamic Programming water-allocation algorithm.

Covers:
1. Zero water availability (W = 0.0)
2. Insufficient water (severe scarcity knapsack tradeoffs, critical penalty avoidance)
3. Abundant water (W >= total demand, all plots fully irrigated without over-allocation)
4. Multiple plots with varying priorities, Ky sensitivities, and demands
5. Configurable quantum discretization unit (e.g. 10.0 liters/units)
6. Capacity constraint verification (total allocated <= available water)
7. Upper bound constraint verification (allocated <= remaining demand for all plots)
8. Framework-independent pure function (dp_allocate_pure) and Domain Plot wrapper
"""

import unittest
from app.algorithms.dynamic_programming import (
    calculate_plot_utility,
    dp_allocate_pure,
    run_dp_allocation,
)
from app.models.farm import Plot


class TestDynamicProgrammingWaterAllocation(unittest.TestCase):
    """Test suite verifying multiple-choice knapsack DP optimization and boundary conditions."""

    def setUp(self):
        """Set up standard multi-plot benchmark data."""
        self.plot_flowering = {
            "plot_identifier": "P-FLOWER",
            "name": "High-Value Flowering Tomato",
            "remaining_demand": 80.0,
            "crop_value": 4500.0,
            "sensitivity_factor": 1.40,  # Critical flowering stage
            "priority": 5,
            "cost_per_unit": 0.05,
        }
        self.plot_vegetative = {
            "plot_identifier": "P-VEG",
            "name": "Vegetative Corn",
            "remaining_demand": 100.0,
            "crop_value": 2400.0,
            "sensitivity_factor": 0.90,
            "priority": 3,
            "cost_per_unit": 0.05,
        }
        self.plot_ripening = {
            "plot_identifier": "P-RIPE",
            "name": "Ripening Cotton",
            "remaining_demand": 60.0,
            "crop_value": 1500.0,
            "sensitivity_factor": 0.45,  # Low sensitivity
            "priority": 2,
            "cost_per_unit": 0.05,
        }
        self.benchmark_plots = [self.plot_flowering, self.plot_vegetative, self.plot_ripening]
        # Total demand = 80 + 100 + 60 = 240.0

    def test_zero_water_availability(self):
        """When available water is 0, allocations and costs must be 0, with 100% unmet demand."""
        result = dp_allocate_pure(self.benchmark_plots, available_water=0.0)

        self.assertEqual(result.total_allocated, 0.0)
        self.assertEqual(result.unmet_demand, 240.0)
        self.assertEqual(result.total_cost, 0.0)
        self.assertEqual(result.water_utilization_pct, 100.0)
        for item in result.allocations:
            self.assertEqual(item.allocated_water, 0.0)
            self.assertEqual(item.coverage_pct, 0.0)

    def test_insufficient_water_prioritizes_critical_crops(self):
        """Under severe water scarcity (W = 80 vs demand 240), DP prioritizes sensitive flowering crop."""
        budget = 80.0
        result = dp_allocate_pure(self.benchmark_plots, available_water=budget, quantum_unit=5.0)

        # Budget constraint strictly held
        self.assertLessEqual(result.total_allocated, budget + 0.01)

        alloc_map = {a.plot_identifier: a for a in result.allocations}
        tomato_alloc = alloc_map["P-FLOWER"].allocated_water
        cotton_alloc = alloc_map["P-RIPE"].allocated_water

        # Tomato has high Ky (1.4) & value ($4500) vs Cotton Ky (0.45) & value ($1500)
        # Avoiding critical unmet penalty means Tomato receives the vast majority of water
        self.assertGreater(tomato_alloc, cotton_alloc)
        self.assertGreaterEqual(tomato_alloc, 60.0)

    def test_abundant_water_covers_all_plots_without_over_allocation(self):
        """When available water exceeds total demand, all plots get 100%, never exceeding demand."""
        excessive_budget = 500.0  # Much greater than 240.0 demand
        result = dp_allocate_pure(self.benchmark_plots, available_water=excessive_budget, quantum_unit=10.0)

        self.assertAlmostEqual(result.total_allocated, 240.0, delta=0.5)
        self.assertAlmostEqual(result.unmet_demand, 0.0, delta=0.1)

        for item in result.allocations:
            self.assertAlmostEqual(item.allocated_water, item.remaining_demand, delta=0.1)
            self.assertAlmostEqual(item.coverage_pct, 100.0, delta=0.1)
            # Must NEVER exceed remaining demand
            self.assertLessEqual(item.allocated_water, item.remaining_demand)

    def test_configurable_quantum_discretization_unit(self):
        """Verify that DP supports custom quantum units (e.g. 10.0 liters per unit)."""
        quantum = 10.0
        budget = 100.0
        result = dp_allocate_pure(self.benchmark_plots, available_water=budget, quantum_unit=quantum)

        self.assertEqual(result.quantum_unit, quantum)
        self.assertEqual(result.discrete_capacity_steps, int(budget / quantum))

        # Check that all discrete unit allocations are integers
        for item in result.allocations:
            self.assertIsInstance(item.discrete_units_used, int)
            self.assertGreaterEqual(item.discrete_units_used, 0)
            self.assertLessEqual(item.allocated_water, item.remaining_demand)

    def test_multiple_plots_capacity_constraint(self):
        """Ensure sum of allocated water never exceeds available water across diverse budgets."""
        test_budgets = [15.0, 45.0, 95.0, 160.0, 240.0, 300.0]

        for b in test_budgets:
            res = dp_allocate_pure(self.benchmark_plots, available_water=b, quantum_unit=5.0)
            self.assertLessEqual(
                res.total_allocated,
                b + 0.01,
                f"DP exceeded budget {b}: got {res.total_allocated}",
            )
            # Never exceed plot demand
            for a in res.allocations:
                self.assertLessEqual(a.allocated_water, a.remaining_demand + 0.01)

    def test_utility_function_properties(self):
        """Verify that utility rewards coverage and penalizes unmet critical demand."""
        # 100% allocation -> zero penalty
        net_full, pres_full, pen_full, cost_full = calculate_plot_utility(
            allocated_water=100.0,
            demand=100.0,
            crop_value=2000.0,
            sensitivity_factor=1.2,
            priority=5,
            cost_per_unit=0.05,
        )
        self.assertEqual(pen_full, 0.0)
        self.assertEqual(pres_full, 2000.0)
        self.assertAlmostEqual(cost_full, 5.0, delta=0.01)

        # 0% allocation -> incurs maximum quadratic deficit penalty
        net_zero, pres_zero, pen_zero, cost_zero = calculate_plot_utility(
            allocated_water=0.0,
            demand=100.0,
            crop_value=2000.0,
            sensitivity_factor=1.2,
            priority=5,
            cost_per_unit=0.05,
        )
        self.assertGreater(pen_zero, 0.0)
        self.assertGreater(net_full, net_zero)

    def test_domain_plot_wrapper(self):
        """Verify run_dp_allocation integration wrapper with Plot domain objects."""
        plot_1 = Plot(
            plot_identifier="P-1",
            name="Plot 1 Tomato",
            area=2.0,
            crop_type="Tomato",
            growth_stage="Flowering",
            current_moisture=30.0,
            target_moisture=75.0,
            water_demand=90.0,
            crop_value_per_ha=4000.0,
            sensitivity_factor=1.3,
            priority=5,
        )
        plot_2 = Plot(
            plot_identifier="P-2",
            name="Plot 2 Potato",
            area=3.0,
            crop_type="Potato",
            growth_stage="Vegetative",
            current_moisture=32.0,
            target_moisture=72.0,
            water_demand=120.0,
            crop_value_per_ha=2200.0,
            sensitivity_factor=0.9,
            priority=3,
        )

        res = run_dp_allocation([plot_1, plot_2], available_water=150.0)
        self.assertLessEqual(res.total_allocated, 150.0 + 0.1)
        self.assertGreater(res.total_allocated, 0.0)
        self.assertGreater(res.total_benefit, 0.0)


if __name__ == "__main__":
    unittest.main()
