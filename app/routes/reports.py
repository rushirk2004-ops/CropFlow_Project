"""Results analysis, historical run comparisons, and report export endpoints."""

import csv
import io
import json
import sqlite3
from flask import Blueprint, Response, jsonify, render_template, request
from app.models.farm import Farm, Plot
from app.services.simulation import compare_strategies
from database.db import get_db_connection, seed_sample_data

reports_bp = Blueprint("reports", __name__)


@reports_bp.route("/results")
def view_results():
    """Results, comparative analytics, and irrigation schedule view."""
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) as cnt FROM farms")
    if cur.fetchone()["cnt"] == 0:
        seed_sample_data()

    cur.execute("SELECT id, name, water_budget FROM farms ORDER BY id ASC")
    farms_rows = [dict(r) for r in cur.fetchall()]

    farm_id = request.args.get("farm_id", type=int)
    if not farm_id and farms_rows:
        farm_id = farms_rows[0]["id"]

    water_budget = request.args.get("water_budget", type=float)

    # Fetch farm
    cur.execute("SELECT * FROM farms WHERE id = ?", (farm_id,))
    farm_row = cur.fetchone()
    if not farm_row:
        farm_row = farms_rows[0]
        farm_id = farm_row["id"]

    cur.execute("SELECT * FROM plots WHERE farm_id = ? ORDER BY id ASC", (farm_id,))
    plots = [Plot.from_dict(dict(r)) for r in cur.fetchall()]

    active_budget = water_budget if water_budget is not None else farm_row["water_budget"]

    farm = Farm(
        id=farm_row["id"],
        name=farm_row["name"],
        location=farm_row["location"],
        total_area=farm_row["total_area"],
        water_budget=active_budget,
        reservoir_capacity=farm_row["reservoir_capacity"],
        energy_rate=farm_row["energy_rate"],
        labor_rate=farm_row["labor_rate"],
        pump_capacity=farm_row["pump_capacity"],
        plots=plots,
    )

    comparison = compare_strategies(farm, farm.water_budget, scenario_name="Comparative Analysis")

    # Fetch recent runs history
    cur.execute(
        """
        SELECT r.id, r.algorithm, r.scenario_name, r.available_water,
               r.total_allocated, r.net_return, r.fairness_index, r.created_at
        FROM optimization_runs r
        WHERE r.farm_id = ?
        ORDER BY r.id DESC LIMIT 10
        """,
        (farm_id,),
    )
    history_runs = [dict(r) for r in cur.fetchall()]

    return render_template(
        "results.html",
        farm=farm,
        farms=farms_rows,
        comparison=comparison,
        history=history_runs,
    )


@reports_bp.route("/api/reports/history", methods=["GET"])
def get_run_history():
    """List historical optimization executions for a farm."""
    farm_id = request.args.get("farm_id", type=int)
    conn = get_db_connection()
    cur = conn.cursor()

    if farm_id:
        cur.execute(
            """
            SELECT * FROM optimization_runs WHERE farm_id = ?
            ORDER BY id DESC LIMIT 50
            """,
            (farm_id,),
        )
    else:
        cur.execute("SELECT * FROM optimization_runs ORDER BY id DESC LIMIT 50")

    runs = [dict(r) for r in cur.fetchall()]
    return jsonify({"runs": runs}), 200


@reports_bp.route("/api/reports/run/<int:run_id>", methods=["GET"])
def get_run_details(run_id: int):
    """Retrieve detailed per-plot allocations for a saved optimization run."""
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM optimization_runs WHERE id = ?", (run_id,))
    run_row = cur.fetchone()
    if not run_row:
        return jsonify({"error": "Run not found"}), 404

    cur.execute(
        """
        SELECT a.*, p.name as plot_name, p.crop_type, p.area as size_hectares
        FROM allocations a
        JOIN plots p ON a.plot_id = p.id
        WHERE a.run_id = ?
        ORDER BY a.id ASC
        """,
        (run_id,),
    )
    alloc_rows = [dict(r) for r in cur.fetchall()]

    data = dict(run_row)
    data["allocations"] = alloc_rows
    return jsonify(data), 200


@reports_bp.route("/api/reports/export/<int:run_id>", methods=["GET"])
def export_run_report(run_id: int):
    """Export run allocations as CSV or JSON."""
    fmt = request.args.get("format", "csv").lower()
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM optimization_runs WHERE id = ?", (run_id,))
    run_row = cur.fetchone()
    if not run_row:
        return jsonify({"error": "Run not found"}), 404

    cur.execute(
        """
        SELECT a.*, p.name as plot_name, p.crop_type, p.area as size_hectares
        FROM allocations a
        JOIN plots p ON a.plot_id = p.id
        WHERE a.run_id = ?
        ORDER BY a.id ASC
        """,
        (run_id,),
    )
    alloc_rows = [dict(r) for r in cur.fetchall()]

    if fmt == "json":
        data = dict(run_row)
        data["allocations"] = alloc_rows
        return Response(
            json.dumps(data, indent=2),
            mimetype="application/json",
            headers={"Content-Disposition": f"attachment;filename=cropflow_run_{run_id}.json"},
        )

    # CSV format
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Run ID", "Algorithm", "Plot Name", "Crop Type", "Plot Size (ha)",
        "Water Demand (m3)", "Allocated Water (m3)", "Coverage (%)",
        "Preserved Yield (%)", "Cost ($)", "Start Hour", "Duration (h)", "Flow Rate (m3/h)"
    ])

    for a in alloc_rows:
        writer.writerow([
            run_id,
            run_row["algorithm"],
            a["plot_name"],
            a["crop_type"],
            a.get("size_hectares", 1.0),
            a["demand"],
            a["allocated_water"],
            a["coverage_pct"],
            a["yield_preservation_pct"],
            a["cost"],
            a["scheduled_start_hour"],
            a["scheduled_duration_hours"],
            a["flow_rate"],
        ])

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename=cropflow_run_{run_id}.csv"},
    )


@reports_bp.route("/api/reports/compare-runs", methods=["GET", "POST"])
def compare_historical_runs():
    """Retrieve and compare multiple historical optimization runs side-by-side."""
    run_ids = []
    if request.method == "POST":
        payload = request.get_json(silent=True) or {}
        run_ids = payload.get("run_ids", [])
    else:
        raw_ids = request.args.get("run_ids", "")
        if raw_ids:
            try:
                run_ids = [int(i.strip()) for i in raw_ids.split(",") if i.strip().isdigit()]
            except ValueError:
                pass

    if not run_ids:
        return jsonify({"error": "Provide at least two run_ids to compare (e.g., ?run_ids=1,2)."}), 400

    conn = get_db_connection()
    cur = conn.cursor()

    placeholders = ",".join("?" for _ in run_ids)
    cur.execute(
        f"""
        SELECT * FROM optimization_runs
        WHERE id IN ({placeholders})
        ORDER BY id ASC
        """,
        run_ids,
    )
    run_rows = [dict(r) for r in cur.fetchall()]

    if not run_rows:
        return jsonify({"error": "None of the specified runs were found."}), 404

    # Fetch allocations for each run
    runs_data = []
    for r in run_rows:
        r_id = r["id"]
        cur.execute(
            """
            SELECT a.*, p.name as plot_name, p.crop_type, p.area as size_hectares
            FROM allocations a
            JOIN plots p ON a.plot_id = p.id
            WHERE a.run_id = ?
            ORDER BY a.id ASC
            """,
            (r_id,),
        )
        r["allocations"] = [dict(a) for a in cur.fetchall()]
        runs_data.append(r)

    winner_yield = max(runs_data, key=lambda x: x["total_benefit"])["id"]
    winner_net = max(runs_data, key=lambda x: x["net_return"])["id"]
    winner_fairness = max(runs_data, key=lambda x: x["fairness_index"])["id"]

    return jsonify({
        "runs": runs_data,
        "count": len(runs_data),
        "winners": {
            "highest_yield_run_id": winner_yield,
            "highest_net_return_run_id": winner_net,
            "highest_fairness_run_id": winner_fairness,
        },
    }), 200


@reports_bp.route("/api/scenarios", methods=["GET", "POST"])
def manage_scenarios():
    """Retrieve or create scenario settings for a farm."""
    conn = get_db_connection()
    cur = conn.cursor()

    if request.method == "POST":
        payload = request.get_json(silent=True) or {}
        farm_id = payload.get("farm_id")
        name = str(payload.get("name", "")).strip()
        drought_factor = float(payload.get("drought_factor", 1.0))
        water_override = payload.get("water_override")
        description = payload.get("description", "")

        if not farm_id or not name:
            return jsonify({"error": "farm_id and name are required."}), 400

        cur.execute(
            """
            INSERT INTO scenario_settings (farm_id, name, drought_factor, water_override, description)
            VALUES (?, ?, ?, ?, ?)
            """,
            (farm_id, name, drought_factor, water_override, description),
        )
        conn.commit()
        return jsonify({"id": cur.lastrowid, "message": "Scenario created successfully."}), 201

    # GET
    farm_id = request.args.get("farm_id", type=int)
    if farm_id:
        cur.execute("SELECT * FROM scenario_settings WHERE farm_id = ? ORDER BY drought_factor DESC", (farm_id,))
    else:
        cur.execute("SELECT * FROM scenario_settings ORDER BY id ASC")

    scenarios = [dict(r) for r in cur.fetchall()]
    return jsonify({"scenarios": scenarios}), 200

