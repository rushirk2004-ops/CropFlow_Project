"""Unit tests for physical, hydraulic, and agricultural constraints across algorithms."""

import unittest
from app.algorithms.dynamic_programming import run_dp_allocation
from app.algorithms.greedy import run_greedy_allocation
from app.algorithms.hybrid import run_hybrid_allocation
from app.models.farm import Farm, Plot
from app.services.scheduler import build_irrigation_schedule


class TestAgriculturalConstraints(unittest.TestCase):
    """Test suite ensuring all physical and hydraulic constraints hold strictly."""

    def setUp(self):
        """Set up diverse multi-plot test farm."""
        self.plots = [
            Plot(
                id=1,
                name="Plot 1 Clay Soil",
                size_hectares=3.0,
                crop_type="Corn",
                growth_stage="Flowering",
                soil_type="Clay",
                current_moisture=22.0,
                target_moisture=75.0,
                wilting_point=18.0,
                infiltration_rate=8.0,  # Low infiltration (runoff hazard)
                water_demand=159.0,
                crop_value_per_ha=2400.0,
                sensitivity_factor=1.4,
            ),
            Plot(
                id=2,
                name="Plot 2 Sandy Soil",
                size_hectares=5.0,
                crop_type="Cotton",
                growth_stage="Vegetative",
                soil_type="Sandy",
                current_moisture=35.0,
                target_moisture=65.0,
                wilting_point=10.0,
                infiltration_rate=25.0,  # High infiltration
                water_demand=150.0,
                crop_value_per_ha=1800.0,
                sensitivity_factor=0.85,
            ),
            Plot(
                id=3,
                name="Plot 3 Loamy Soil",
                size_hectares=2.5,
                crop_type="Tomato",
                growth_stage="Flowering",
                soil_type="Loamy",
                current_moisture=28.0,
                target_moisture=80.0,
                wilting_point=14.0,
                infiltration_rate=18.0,
                water_demand=130.0,
                crop_value_per_ha=4200.0,
                sensitivity_factor=1.3,
            ),
        ]
        self.farm = Farm(
            id=10,
            name="Constraint Test Farm",
            water_budget=250.0,
            pump_capacity=25.0,  # m3/hr
            plots=self.plots,
        )

    def test_water_budget_constraint_never_violated(self):
        """Total allocated water must never exceed available water budget under any test condition."""
        test_budgets = [10.0, 50.0, 150.0, 250.0, 439.0, 800.0]

        for budget in test_budgets:
            # Greedy
            res_g = run_greedy_allocation(self.plots, available_water=budget)
            self.assertLessEqual(
                res_g.total_allocated,
                budget + 0.1,
                f"Greedy exceeded budget {budget}: got {res_g.total_allocated}",
            )

            # DP
            res_dp = run_dp_allocation(self.plots, available_water=budget)
            self.assertLessEqual(
                res_dp.total_allocated,
                budget + 0.1,
                f"DP exceeded budget {budget}: got {res_dp.total_allocated}",
            )

            # Hybrid
            res_h = run_hybrid_allocation(self.plots, available_water=budget)
            self.assertLessEqual(
                res_h.total_allocated,
                budget + 0.1,
                f"Hybrid exceeded budget {budget}: got {res_h.total_allocated}",
            )

    def test_non_negativity_and_upper_demand_bounds(self):
        """Plot allocation must always satisfy 0 <= w_i <= Demand_i."""
        budget = 180.0
        for runner in [run_greedy_allocation, run_dp_allocation, run_hybrid_allocation]:
            res = runner(self.plots, available_water=budget)
            for item in res.allocations:
                self.assertGreaterEqual(item.allocated_water, 0.0)
                self.assertLessEqual(item.allocated_water, item.demand + 0.05)

    def test_infiltration_rate_and_pump_flow_limits(self):
        """Irrigation schedule delivery rate must not exceed plot infiltration or pump capacity."""
        res_h = run_hybrid_allocation(self.plots, available_water=self.farm.water_budget)
        scheduled_res = build_irrigation_schedule(res_h, self.farm)

        plot_map = {p.id: p for p in self.plots}
        for item in scheduled_res.schedule:
            plot = plot_map[item.plot_id]
            # Max soil intake = infiltration (mm/hr) * Area (ha) * 10 (m3/mm/ha)
            max_intake = plot.infiltration_rate * plot.size_hectares * 10.0

            # Scheduled flow rate must be <= pump capacity
            self.assertLessEqual(item.flow_rate_m3h, self.farm.pump_capacity + 0.1)
            # Scheduled flow rate must be <= max soil intake
            self.assertLessEqual(item.flow_rate_m3h, max_intake + 0.1)


if __name__ == "__main__":
    unittest.main()
