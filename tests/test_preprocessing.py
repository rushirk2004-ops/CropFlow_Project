"""Unit tests for farm data collection, preprocessing, and validation."""

import unittest
from app import create_app
from app.services.preprocessing import (
    ValidationError,
    calculate_remaining_water_demand,
    validate_farm_input,
    validate_plot_input,
)
from database.db import get_db_connection, init_db, seed_sample_data


class TestFarmPreprocessingAndValidation(unittest.TestCase):
    """Test suite for data collection, validation rules, and remaining water demand calculations."""

    def setUp(self):
        """Set up test Flask application context and clean in-memory/test SQLite database."""
        self.app = create_app("testing")
        self.client = self.app.test_client()
        with self.app.app_context():
            init_db()

    def test_calculate_remaining_water_demand_assumptions(self):
        """Verify remaining water demand calculation under documented assumptions."""
        # Case 1: Active deficit
        # Target = 75%, WP = 15% -> Range = 60%. Current = 45% -> Deficit = 30%. Deficit ratio = 30/60 = 0.50 (50%)
        # Base water required = 100,000 Liters -> Remaining = 50,000 Liters.
        calc = calculate_remaining_water_demand(
            area_hectares=2.0,
            water_required_liters=100000.0,
            current_moisture_pct=45.0,
            target_moisture_pct=75.0,
            wilting_point_pct=15.0,
        )
        self.assertAlmostEqual(calc["remaining_demand_liters"], 50000.0, delta=1.0)
        self.assertAlmostEqual(calc["deficit_ratio"], 0.50, delta=0.01)
        self.assertEqual(len(calc["assumptions_applied"]), 4)

        # Case 2: Current moisture >= Target moisture (Field capacity met)
        calc_saturated = calculate_remaining_water_demand(
            area_hectares=2.0,
            water_required_liters=100000.0,
            current_moisture_pct=80.0,
            target_moisture_pct=75.0,
            wilting_point_pct=15.0,
        )
        self.assertEqual(calc_saturated["remaining_demand_liters"], 0.0)
        self.assertEqual(calc_saturated["deficit_ratio"], 0.0)

    def test_reject_negative_numeric_inputs(self):
        """Reject negative area, water volume, infiltration rate, and costs."""
        # Negative area
        with self.assertRaises(ValidationError) as ctx:
            validate_plot_input({
                "plot_identifier": "P-NEG-1",
                "area": -2.5,
                "crop_type": "Wheat",
                "water_required_liters": 100000.0,
                "current_moisture": 30.0,
                "infiltration_rate": 15.0,
                "cost_per_liter": 0.000045,
            })
        self.assertIn("area", ctx.exception.errors)

        # Negative required water
        with self.assertRaises(ValidationError) as ctx:
            validate_plot_input({
                "plot_identifier": "P-NEG-2",
                "area": 2.0,
                "crop_type": "Corn",
                "water_required_liters": -5000.0,
                "current_moisture": 30.0,
                "infiltration_rate": 15.0,
                "cost_per_liter": 0.000045,
            })
        self.assertIn("water_required_liters", ctx.exception.errors)

        # Negative cost per liter
        with self.assertRaises(ValidationError) as ctx:
            validate_plot_input({
                "plot_identifier": "P-NEG-3",
                "area": 2.0,
                "crop_type": "Corn",
                "water_required_liters": 50000.0,
                "current_moisture": 30.0,
                "infiltration_rate": 15.0,
                "cost_per_liter": -0.05,
            })
        self.assertIn("cost_per_liter", ctx.exception.errors)

    def test_validate_soil_moisture_percentage_bounds(self):
        """Reject soil moisture less than 0% or greater than 100%."""
        # Below 0%
        with self.assertRaises(ValidationError) as ctx:
            validate_plot_input({
                "plot_identifier": "P-M1",
                "area": 1.0,
                "crop_type": "Wheat",
                "current_moisture": -5.0,
            })
        self.assertIn("current_moisture", ctx.exception.errors)

        # Above 100%
        with self.assertRaises(ValidationError) as ctx:
            validate_plot_input({
                "plot_identifier": "P-M2",
                "area": 1.0,
                "crop_type": "Wheat",
                "current_moisture": 105.0,
            })
        self.assertIn("current_moisture", ctx.exception.errors)

    def test_plot_id_uniqueness_within_farm(self):
        """Reject duplicate plot identifiers within the same farm."""
        existing_ids = ["P-101", "P-102", "P-103"]
        with self.assertRaises(ValidationError) as ctx:
            validate_plot_input(
                {
                    "plot_identifier": "P-101",
                    "area": 3.0,
                    "crop_type": "Soybean",
                    "current_moisture": 35.0,
                },
                existing_plot_identifiers=existing_ids,
            )
        self.assertIn("plot_identifier", ctx.exception.errors)
        self.assertIn("already exists", ctx.exception.errors["plot_identifier"])

    def test_farm_data_collection_and_sqlite_storage(self):
        """Create a farm and add a plot via API, verifying SQLite storage."""
        # 1. Create farm
        farm_resp = self.client.post("/api/farms", json={
            "name": "Validation Test Farm",
            "location": "Aquifer Sub-basin 7",
            "total_available_water_liters": 450000.0,
            "drought_severity": "Moderate",
            "window_start": "21:00",
            "window_end": "05:00",
            "window_duration_hours": 8.0,
        })
        self.assertEqual(farm_resp.status_code, 201)
        farm_data = farm_resp.get_json()
        farm_id = farm_data["farm_id"]

        # 2. Add plot
        plot_resp = self.client.post(f"/api/farms/{farm_id}/plots", json={
            "plot_identifier": "PL-ALPHA",
            "name": "Alpha Field",
            "area": 3.5,
            "crop_type": "Tomato",
            "growth_stage": "Flowering",
            "water_required_liters": 180000.0,
            "current_moisture": 32.0,
            "soil_type": "Loamy",
            "infiltration_rate": 18.0,
            "priority": 5,
            "cost_per_liter": 0.000052,
        })
        self.assertEqual(plot_resp.status_code, 201)
        plot_data = plot_resp.get_json()
        self.assertIn("remaining_demand_liters", plot_data["plot"])
        self.assertGreater(plot_data["plot"]["remaining_demand_liters"], 0.0)

        # 3. Check duplicate rejection via API
        dup_resp = self.client.post(f"/api/farms/{farm_id}/plots", json={
            "plot_identifier": "PL-ALPHA",  # Duplicate!
            "area": 2.0,
            "crop_type": "Wheat",
            "water_required_liters": 50000.0,
            "current_moisture": 40.0,
            "soil_type": "Sandy",
            "infiltration_rate": 20.0,
            "priority": 2,
            "cost_per_liter": 0.000040,
        })
        self.assertEqual(dup_resp.status_code, 400)
        dup_err = dup_resp.get_json()
        self.assertIn("field_errors", dup_err)
        self.assertIn("plot_identifier", dup_err["field_errors"])

    def test_seed_sample_farm_data(self):
        """Verify that sample farm data seeds successfully with 6 diverse plots."""
        with self.app.app_context():
            farm_id = seed_sample_data(force=True)
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("SELECT * FROM farms WHERE id = ?", (farm_id,))
            farm_row = cur.fetchone()
            self.assertIsNotNone(farm_row)
            self.assertEqual(farm_row["total_available_water_liters"], 650000.0)

            cur.execute("SELECT COUNT(*) as cnt FROM plots WHERE farm_id = ?", (farm_id,))
            plot_count = cur.fetchone()["cnt"]
            self.assertEqual(plot_count, 6)


if __name__ == "__main__":
    unittest.main()
