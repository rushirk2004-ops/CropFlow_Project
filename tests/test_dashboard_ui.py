"""Integration tests for CropFlow dashboard UI, endpoints, and frontend contracts."""

import unittest
from app import create_app
from database.db import seed_sample_data


class TestCropFlowDashboardUI(unittest.TestCase):
    """Test suite verifying dashboard routes, template rendering, and frontend API contracts."""

    def setUp(self):
        """Set up test Flask client and ensure sample database is seeded."""
        self.app = create_app("testing")
        self.client = self.app.test_client()
        self.db_path = self.app.config["DATABASE_PATH"]
        self.farm_id = seed_sample_data(db_path=self.db_path, force=True)

    def test_dashboard_page_renders_successfully(self):
        """GET /dashboard renders HTTP 200 with all core dashboard features present."""
        response = self.client.get(f"/dashboard?farm_id={self.farm_id}")
        self.assertEqual(response.status_code, 200)

        html = response.get_data(as_text=True)

        # 1. Available Water & Crop Demand KPI
        self.assertIn("Available Water / Total Demand", html)
        self.assertIn("kpiAvailableWater", html)

        # 2. Water Allocated & Unmet Demand KPI
        self.assertIn("Allocated & Unmet Demand", html)
        self.assertIn("kpiAllocatedWater", html)
        self.assertIn("kpiUnmetDemand", html)

        # 3. Water Utilization Rate KPI
        self.assertIn("Water Utilization Rate", html)
        self.assertIn("kpiUtilization", html)

        # 4. Estimated Irrigation Cost KPI
        self.assertIn("Estimated Irrigation Cost", html)
        self.assertIn("kpiTotalCost", html)

        # 5. Algorithm Execution Times
        self.assertIn("Algorithm Execution Times", html)
        self.assertIn("runtimeGreedy", html)
        self.assertIn("runtimeDP", html)
        self.assertIn("runtimeHybrid", html)

        # 6. Bar Chart for Plot Allocations
        self.assertIn("plotAllocationsChart", html)
        self.assertIn("Water Allocation by Plot", html)

        # 7. Comparison Charts
        self.assertIn("strategyComparisonChart", html)
        self.assertIn("comparisonMetricTabs", html)

        # 8. Drought Scenario Simulator
        self.assertIn("Drought Scenario Simulator", html)
        self.assertIn("droughtSlider", html)

        # 9. Detailed Table for Plot Demand, Allocation & Unmet
        self.assertIn("Detailed Plot Demand, Allocation & Unmet Water Table", html)
        self.assertIn("plotsAllocationTable", html)

        # 10. Run All Three Algorithms Button
        self.assertIn("runAllAlgorithmsBtn", html)
        self.assertIn("Run All 3 Algorithms", html)

        # 11. Results History View
        self.assertIn("Recent Optimization History View", html)
        self.assertIn("historyRunsTable", html)

        # Sidebar navigation check
        self.assertIn("cropflow-sidebar", html)
        self.assertIn("Operations", html)

    def test_results_page_renders_successfully(self):
        """GET /results renders HTTP 200 with comparisons, schedule, and exports."""
        response = self.client.get(f"/results?farm_id={self.farm_id}")
        self.assertEqual(response.status_code, 200)

        html = response.get_data(as_text=True)
        self.assertIn("Optimization Results & Comparisons", html)
        self.assertIn("Greedy Allocation", html)
        self.assertIn("Dynamic Programming", html)
        self.assertIn("Hybrid (Greedy + DP)", html)
        self.assertIn("Actionable Hourly Irrigation Pump Schedule", html)
        self.assertIn("Historical Optimization Runs Audit", html)

    def test_api_optimize_all_strategies(self):
        """POST /api/optimize with algorithm='all' benchmarks all 3 algorithms and saves runs."""
        payload = {
            "farm_id": self.farm_id,
            "algorithm": "all",
            "water_override": 250.0,
            "scenario_name": "Test Multi-Strategy Run",
            "save_run": True,
        }
        response = self.client.post("/api/optimize", json=payload)
        self.assertEqual(response.status_code, 200)

        data = response.get_json()
        self.assertIn("results", data)
        self.assertIn("greedy", data["results"])
        self.assertIn("dynamic_programming", data["results"])
        self.assertIn("hybrid", data["results"])

        for alg_key in ["greedy", "dynamic_programming", "hybrid"]:
            res = data["results"][alg_key]
            self.assertIn("total_allocated", res)
            self.assertIn("unmet_demand", res)
            self.assertIn("water_utilization_pct", res)
            self.assertIn("total_cost", res)
            self.assertIn("total_benefit", res)
            self.assertIn("net_return", res)
            self.assertIn("execution_time_ms", res)
            self.assertIn("allocations", res)
            self.assertGreater(len(res["allocations"]), 0)

    def test_api_simulate_endpoint_returns_valid_curves(self):
        """POST /api/simulate returns 5-tier drought simulation chart data."""
        response = self.client.post("/api/simulate", json={"farm_id": self.farm_id})
        self.assertEqual(response.status_code, 200)

        data = response.get_json()
        self.assertIn("chart_series", data)
        series = data["chart_series"]
        self.assertEqual(len(series["labels"]), 5)
        self.assertEqual(len(series["greedy_benefits"]), 5)
        self.assertEqual(len(series["dp_benefits"]), 5)
        self.assertEqual(len(series["hybrid_benefits"]), 5)

    def test_api_reports_history_and_exports(self):
        """Verify run history querying and CSV/JSON export endpoints."""
        # 1. Run optimization to ensure at least one run exists
        self.client.post("/api/optimize", json={"farm_id": self.farm_id, "algorithm": "hybrid", "save_run": True})

        # 2. Query history
        hist_res = self.client.get(f"/api/reports/history?farm_id={self.farm_id}")
        self.assertEqual(hist_res.status_code, 200)
        hist_data = hist_res.get_json()
        self.assertIn("runs", hist_data)
        self.assertGreater(len(hist_data["runs"]), 0)

        latest_id = hist_data["runs"][0]["id"]

        # 3. Test CSV export
        csv_res = self.client.get(f"/api/reports/export/{latest_id}?format=csv")
        self.assertEqual(csv_res.status_code, 200)
        self.assertIn("text/csv", csv_res.headers["Content-Type"])

        # 4. Test JSON export
        json_res = self.client.get(f"/api/reports/export/{latest_id}?format=json")
        self.assertEqual(json_res.status_code, 200)
        self.assertIn("application/json", json_res.headers["Content-Type"])

    def test_multilingual_dashboard_marathi(self):
        """Dashboard renders full Marathi translations when cropflow_lang cookie is set to 'mr'."""
        self.client.set_cookie("cropflow_lang", "mr")
        response = self.client.get(f"/dashboard?farm_id={self.farm_id}")
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)

        # Check Marathi strings rendered in body, cards, and tables
        self.assertIn("सिंचन आदेश व नियंत्रण कक्ष", html)
        self.assertIn("उपलब्ध पाणी / एकूण मागणी", html)
        self.assertIn("वाटप केलेले पाणी व अपूर्ण मागणी", html)
        self.assertIn("भूखंडनिहाय पाणी वाटप", html)
        self.assertIn("₹", html)

    def test_multilingual_dashboard_chinese(self):
        """Dashboard renders full Chinese translations when cropflow_lang cookie is set to 'zh'."""
        self.client.set_cookie("cropflow_lang", "zh")
        response = self.client.get(f"/dashboard?farm_id={self.farm_id}")
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)

        # Check Chinese strings rendered in body, cards, and tables
        self.assertIn("灌溉指挥与调度控制面板", html)
        self.assertIn("可用水量 / 总需水量", html)
        self.assertIn("各地块水资源分配", html)
        self.assertIn("₹", html)

    def test_set_language_endpoint_sets_cookie(self):
        """GET /set-language/<lang_code> sets 30-day cookie and redirects."""
        response = self.client.get("/set-language/mr")
        self.assertEqual(response.status_code, 302)
        cookies = response.headers.getlist("Set-Cookie")
        self.assertTrue(any("cropflow_lang=mr" in c for c in cookies))


if __name__ == "__main__":
    unittest.main()

