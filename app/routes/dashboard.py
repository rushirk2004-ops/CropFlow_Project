"""Dashboard routes and system health-check endpoints."""

from datetime import datetime, timezone
import sqlite3
from flask import Blueprint, jsonify, render_template, request
from app.models.farm import Farm, Plot
from app.services.preprocessing import generate_water_demand_matrix
from app.services.simulation import compare_strategies
from database.db import get_db_connection, seed_sample_data

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/")
def home():
    """Home / landing page introducing CropFlow architecture and objectives."""
    return render_template("index.html")


@dashboard_bp.route("/dashboard")
def view_dashboard():
    """Main interactive irrigation dashboard."""
    conn = get_db_connection()
    cur = conn.cursor()

    # Ensure at least sample data exists
    cur.execute("SELECT COUNT(*) as cnt FROM farms")
    if cur.fetchone()["cnt"] == 0:
        seed_sample_data()

    # Fetch all farms
    cur.execute("SELECT id, name, location, water_budget, total_area FROM farms ORDER BY id ASC")
    farms_rows = cur.fetchall()

    if not farms_rows:
        return render_template("dashboard.html", farm=None, farms=[], comparison=None)

    # Select farm
    farm_id = request.args.get("farm_id", type=int)
    if not farm_id:
        farm_id = farms_rows[0]["id"]

    # Fetch selected farm
    cur.execute("SELECT * FROM farms WHERE id = ?", (farm_id,))
    farm_row = cur.fetchone()
    if not farm_row:
        farm_row = farms_rows[0]
        farm_id = farm_row["id"]

    # Fetch plots for this farm
    cur.execute("SELECT * FROM plots WHERE farm_id = ? ORDER BY id ASC", (farm_id,))
    plots = [Plot.from_dict(dict(r)) for r in cur.fetchall()]

    farm_dict = dict(farm_row)
    farm_dict["plots"] = plots
    farm = Farm.from_dict(farm_dict)

    # Quick baseline strategy comparison
    comparison = compare_strategies(farm, farm.water_budget, scenario_name="Live Operational")
    demand_matrix = generate_water_demand_matrix(farm.plots)
    plots_dicts = [p.to_dict() for p in farm.plots]

    # Fetch recent runs history for dashboard audit view
    cur.execute(
        """
        SELECT r.id, r.algorithm, r.scenario_name, r.available_water,
               r.total_allocated, r.unmet_demand, r.total_cost, r.total_benefit,
               r.net_return, r.execution_time_ms, r.fairness_index, r.created_at
        FROM optimization_runs r
        WHERE r.farm_id = ?
        ORDER BY r.id DESC LIMIT 8
        """,
        (farm_id,),
    )
    history_runs = [dict(r) for r in cur.fetchall()]

    return render_template(
        "dashboard.html",
        farm=farm,
        farms=[dict(r) for r in farms_rows],
        comparison=comparison,
        demand_matrix=demand_matrix,
        plots_dicts=plots_dicts,
        history=history_runs,
    )


@dashboard_bp.route("/system/health")
@dashboard_bp.route("/health/status")
def view_health():
    """Renders visual system health dashboard."""
    db_status = "connected"
    farms_count = 0
    plots_count = 0

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) as c FROM farms")
        farms_count = cur.fetchone()["c"]
        cur.execute("SELECT COUNT(*) as c FROM plots")
        plots_count = cur.fetchone()["c"]
    except sqlite3.Error as e:
        db_status = f"error: {str(e)}"

    algorithms = [
        {
            "id": "greedy",
            "name_key": "alg_greedy",
            "complexity": "O(N log N)",
            "space": "O(1)",
            "role_key": "role_greedy",
            "badge": "badge-greedy",
            "accent": "#f59e0b",
        },
        {
            "id": "dynamic_programming",
            "name_key": "alg_dp",
            "complexity": "O(N * M * K)",
            "space": "O(N * M)",
            "role_key": "role_dp",
            "badge": "badge-dp",
            "accent": "#0ea5e9",
        },
        {
            "id": "hybrid",
            "name_key": "alg_hybrid",
            "complexity": "O(N log N + N * M' * K)",
            "space": "O(N * M')",
            "role_key": "role_hybrid",
            "badge": "badge-hybrid",
            "accent": "#10b981",
            "is_proposed": True,
        },
    ]

    return render_template(
        "health.html",
        status="healthy" if "error" not in db_status else "degraded",
        db_status=db_status,
        farms_count=farms_count,
        plots_count=plots_count,
        algorithms=algorithms,
        timestamp_utc=datetime.now(timezone.utc).isoformat(),
    )


@dashboard_bp.route("/health")
@dashboard_bp.route("/api/health")
def health_check():
    """System health-check endpoint for container orchestrators and monitoring tools."""
    # When visited from a standard web browser requesting HTML without format=json:
    if (
        request.path in ("/health", "/api/health")
        and request.headers.get("Accept")
        and "text/html" in request.headers.get("Accept")
        and request.args.get("format") != "json"
    ):
        return view_health()

    db_status = "connected"
    farms_count = 0
    plots_count = 0

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) as c FROM farms")
        farms_count = cur.fetchone()["c"]
        cur.execute("SELECT COUNT(*) as c FROM plots")
        plots_count = cur.fetchone()["c"]
    except sqlite3.Error as e:
        db_status = f"error: {str(e)}"

    return jsonify({
        "status": "healthy" if "error" not in db_status else "degraded",
        "service": "CropFlow",
        "objective": "Optimal Irrigation Scheduling with Limited Water",
        "version": "1.0.0",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "database": {
            "status": db_status,
            "farms_registered": farms_count,
            "plots_registered": plots_count,
        },
        "supported_algorithms": [
            {
                "id": "greedy",
                "name": "Greedy Allocation",
                "complexity": "O(N log N)",
                "role": "Rapid urgent triage",
            },
            {
                "id": "dynamic_programming",
                "name": "Dynamic Programming",
                "complexity": "O(N * M * K)",
                "role": "Global yield-payoff optimization",
            },
            {
                "id": "hybrid",
                "name": "Hybrid (Greedy + DP)",
                "complexity": "O(N log N + N * M' * K)",
                "role": "Proposed balanced architecture",
            },
        ],
    }), 200
