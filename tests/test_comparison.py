"""Integration and comparative benchmark tests across Greedy, DP, and Hybrid strategies."""

import unittest
from app import create_app
from app.models.farm import Farm, Plot
from app.services.simulation import compare_strategies, run_drought_simulation


class TestStrategyComparison(unittest.TestCase):
    """Test suite comparing algorithms on identical agricultural benchmarks."""

    def setUp(self):
        """Set up test app and realistic farm scenario."""
        self.app = create_app("testing")
        self.client = self.app.test_client()

        self.plots = [
            Plot(
                id=1,
                name="Plot A Corn Flowering",
                size_hectares=4.0,
                crop_type="Corn",
                growth_stage="Flowering",
                soil_type="Clay",
                current_moisture=26.0,
                target_moisture=75.0,
                water_demand=196.0,
                crop_value_per_ha=2400.0,
                sensitivity_factor=1.40,
                priority=5,
            ),
            Plot(
                id=2,
                name="Plot B Tomato Flowering",
                size_hectares=2.5,
                crop_type="Tomato",
                growth_stage="Flowering",
                soil_type="Loamy",
                current_moisture=28.0,
                target_moisture=80.0,
                water_demand=130.0,
                crop_value_per_ha=4200.0,
                sensitivity_factor=1.35,
                priority=5,
            ),
            Plot(
                id=3,
                name="Plot C Wheat Vegetative",
                size_hectares=5.0,
                crop_type="Wheat",
                growth_stage="Vegetative",
                soil_type="Loamy",
                current_moisture=34.0,
                target_moisture=70.0,
                water_demand=180.0,
                crop_value_per_ha=1600.0,
                sensitivity_factor=0.85,
                priority=3,
            ),
            Plot(
                id=4,
                name="Plot D Cotton Ripening",
                size_hectares=4.0,
                crop_type="Cotton",
                growth_stage="Ripening",
                soil_type="Sandy",
                current_moisture=38.0,
                target_moisture=65.0,
                water_demand=108.0,
                crop_value_per_ha=1800.0,
                sensitivity_factor=0.50,
                priority=2,
            ),
        ]
        # Total demand = 196 + 130 + 180 + 108 = 614 m3
        self.farm = Farm(
            id=1,
            name="Benchmark Farm",
            water_budget=307.0,  # 50% drought condition
            plots=self.plots,
        )

    def test_compare_strategies_produces_valid_structure(self):
        """compare_strategies returns complete result dictionaries for all 3 algorithms."""
        comp = compare_strategies(self.farm, water_override=307.0)

        self.assertIn("greedy", comp.results)
        self.assertIn("dynamic_programming", comp.results)
        self.assertIn("hybrid", comp.results)

        for alg_key in ["greedy", "dynamic_programming", "hybrid"]:
            res = comp.results[alg_key]
            self.assertLessEqual(res.total_allocated, 307.0 + 0.1)
            self.assertGreater(res.total_benefit, 0.0)
            self.assertGreaterEqual(res.fairness_index, 0.0)
            self.assertLessEqual(res.fairness_index, 1.0)

    def test_hybrid_fairness_superior_under_drought(self):
        """In 50% drought, Hybrid provides higher equity (Jain's index) than pure Greedy."""
        comp = compare_strategies(self.farm, water_override=307.0)
        res_greedy = comp.results["greedy"]
        res_hybrid = comp.results["hybrid"]

        self.assertGreaterEqual(
            res_hybrid.fairness_index,
            res_greedy.fairness_index,
            "Hybrid must have greater or equal fairness than Greedy under severe water constraint.",
        )

    def test_drought_simulation_tiers(self):
        """Simulation covers all 5 supply tiers and returns valid chart series."""
        sim = run_drought_simulation(self.farm)

        self.assertEqual(len(sim["scenarios"]), 5)
        self.assertIn("chart_series", sim)
        series = sim["chart_series"]
        self.assertEqual(len(series["labels"]), 5)
        # Benefits should decrease as drought worsens
        self.assertGreater(series["hybrid_benefits"][0], series["hybrid_benefits"][4])

    def test_api_health_check_endpoint(self):
        """Health check endpoint returns 200 with healthy status and metadata."""
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["status"], "healthy")
        self.assertEqual(data["service"], "CropFlow")

    def test_api_optimize_endpoint(self):
        """POST /api/optimize runs optimization and returns JSON response."""
        payload = {
            "algorithm": "hybrid",
            "water_override": 250.0,
            "save_run": False,
            "farm": self.farm.to_dict(),
        }
        response = self.client.post("/api/optimize", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn("total_allocated", data)
        self.assertLessEqual(data["total_allocated"], 250.0 + 0.1)
        self.assertIn("schedule", data)


if __name__ == "__main__":
    unittest.main()
