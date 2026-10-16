import json
import sqlite3
from typing import Any, Dict, Optional
from flask import Blueprint, jsonify, request
from app.algorithms.dynamic_programming import run_dp_allocation
from app.algorithms.greedy import run_greedy_allocation
from app.algorithms.hybrid import run_hybrid_allocation
from app.models.farm import Farm, Plot
from app.models.result import OptimizationResult
from app.services.preprocessing import prepare_farm_dataset
from app.services.scheduler import build_irrigation_schedule
from app.services.simulation import compare_strategies, run_drought_simulation
from database.db import get_db_connection

optimization_bp = Blueprint("optimization", __name__)


def save_optimization_run(
    farm_id: int,
    result: OptimizationResult,
    parameters: Optional[Dict[str, Any]] = None,
) -> int:
    """Save optimization run, algorithm input parameters, and per-plot allocations into SQLite."""
    conn = get_db_connection()
    cur = conn.cursor()

    obj_val = getattr(result, "final_objective", getattr(result, "total_benefit", 0.0))
    params_payload = parameters or {
        "available_water": result.available_water,
        "algorithm": result.algorithm,
        "scenario_name": result.scenario_name,
        "total_demand": result.total_demand,
    }

    cur.execute(
        """
        INSERT INTO optimization_runs (
            farm_id, algorithm, scenario_name, available_water,
            total_demand, total_allocated, unmet_demand,
            water_utilization_pct, total_cost, total_benefit,
            net_return, objective_value, parameters_json,
            execution_time_ms, fairness_index
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            farm_id,
            result.algorithm,
            result.scenario_name,
            result.available_water,
            result.total_demand,
            result.total_allocated,
            result.unmet_demand,
            result.water_utilization_pct,
            result.total_cost,
            result.total_benefit,
            result.net_return,
            float(obj_val),
            json.dumps(params_payload),
            result.execution_time_ms,
            result.fairness_index,
        ),
    )
    run_id = cur.lastrowid

    alloc_rows = []
    for item in result.allocations:
        if item.plot_id is not None:
            alloc_rows.append((
                run_id,
                item.plot_id,
                item.allocated_water,
                item.demand,
                item.coverage_pct,
                0.0,
                item.yield_preservation_pct,
                item.cost,
                item.scheduled_start_hour,
                item.scheduled_duration_hours,
                item.scheduled_flow_rate,
            ))

    if alloc_rows:
        cur.executemany(
            """
            INSERT INTO allocations (
                run_id, plot_id, allocated_water, demand, coverage_pct,
                stress_index, yield_preservation_pct, cost, scheduled_start_hour,
                scheduled_duration_hours, flow_rate
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            alloc_rows,
        )

    conn.commit()
    return run_id


@optimization_bp.route("/api/optimize", methods=["POST"])
def optimize():
    """Execute water allocation optimization using greedy, dynamic programming, or hybrid strategy."""
    payload = request.get_json(silent=True) or {}
    farm_id = payload.get("farm_id")
    algorithm = str(payload.get("algorithm", "hybrid")).lower().strip()
    water_override = payload.get("water_override")
    scenario_name = str(payload.get("scenario_name", "Standard Allocation"))
    save_run = bool(payload.get("save_run", True))

    farm: Farm

    if farm_id:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM farms WHERE id = ?", (farm_id,))
        farm_row = cur.fetchone()
        if not farm_row:
            return jsonify({"error": f"Farm {farm_id} not found."}), 404

        cur.execute("SELECT * FROM plots WHERE farm_id = ? ORDER BY id ASC", (farm_id,))
        plots = [Plot.from_dict(dict(r)) for r in cur.fetchall()]

        water_budget = float(water_override) if water_override is not None else farm_row["water_budget"]

        farm = Farm(
            id=farm_row["id"],
            name=farm_row["name"],
            location=farm_row["location"],
            total_area=farm_row["total_area"],
            water_budget=water_budget,
            reservoir_capacity=farm_row["reservoir_capacity"],
            energy_rate=farm_row["energy_rate"],
            labor_rate=farm_row["labor_rate"],
            pump_capacity=farm_row["pump_capacity"],
            plots=plots,
        )
    else:
        # Raw farm payload
        raw_farm_data = payload.get("farm")
        if not raw_farm_data:
            return jsonify({"error": "Either farm_id or farm object is required."}), 400
        farm, _ = prepare_farm_dataset(raw_farm_data)
        if water_override is not None:
            farm.water_budget = float(water_override)

    if not farm.plots:
        return jsonify({"error": "Farm has no plots to optimize."}), 400

    # If comparison requested
    if algorithm in ["all", "compare"]:
        comparison = compare_strategies(farm, farm.water_budget, scenario_name)
        comp_dict = comparison.to_dict()
        if save_run and farm.id:
            for alg_key, res_obj in comparison.results.items():
                save_optimization_run(farm.id, res_obj)
        return jsonify(comp_dict), 200

    # Individual algorithm run
    result: OptimizationResult
    if algorithm in ["greedy", "g"]:
        result = run_greedy_allocation(
            plots=farm.plots,
            available_water=farm.water_budget,
            energy_rate=farm.energy_rate,
            labor_rate=farm.labor_rate,
            pump_capacity=farm.pump_capacity,
            scenario_name=scenario_name,
        )
    elif algorithm in ["dynamic_programming", "dp"]:
        result = run_dp_allocation(
            plots=farm.plots,
            available_water=farm.water_budget,
            energy_rate=farm.energy_rate,
            labor_rate=farm.labor_rate,
            pump_capacity=farm.pump_capacity,
            scenario_name=scenario_name,
        )
    elif algorithm in ["hybrid", "h", "proposed"]:
        result = run_hybrid_allocation(
            plots=farm.plots,
            available_water=farm.water_budget,
            energy_rate=farm.energy_rate,
            labor_rate=farm.labor_rate,
            pump_capacity=farm.pump_capacity,
            scenario_name=scenario_name,
        )
    else:
        return jsonify({
            "error": f"Unknown algorithm '{algorithm}'. Choose from 'greedy', 'dynamic_programming', 'hybrid', or 'all'."
        }), 400

    # Build actionable schedule
    result = build_irrigation_schedule(result, farm)

    run_id = None
    if save_run and farm.id:
        try:
            run_id = save_optimization_run(farm.id, result)
        except sqlite3.Error:
            pass

    res_dict = result.to_dict()
    res_dict["run_id"] = run_id
    res_dict["farm_id"] = farm.id
    res_dict["farm_name"] = farm.name

    return jsonify(res_dict), 200


@optimization_bp.route("/api/optimize/algorithms", methods=["GET"])
def get_algorithms():
    """Retrieve metadata and descriptions for available optimization algorithms."""
    return jsonify({
        "algorithms": [
            {
                "id": "greedy",
                "name": "Greedy Allocation",
                "complexity": "O(N log N)",
                "type": "Heuristic Priority Queue",
                "description": "Ranks plots by economic urgency ratio and satisfies highest-priority plots first until water runs out.",
                "strengths": "Ultra-fast execution, guarantees full water to top crops.",
                "weaknesses": "May completely starve lower-priority plots causing high crop death.",
            },
            {
                "id": "dynamic_programming",
                "name": "Dynamic Programming",
                "complexity": "O(N * M * K)",
                "type": "Multi-choice Knapsack / Bellman Optimality",
                "description": "Discretizes capacity into quantum states and finds the global maximum yield payoff curve.",
                "strengths": "Mathematically optimal total yield preservation and net economic return.",
                "weaknesses": "Higher computational overhead with fine discretization.",
            },
            {
                "id": "hybrid",
                "name": "Hybrid Approach (Greedy Triage + DP Refinement)",
                "complexity": "O(N log N + N * M' * K)",
                "type": "Proposed Combined Two-Stage Architecture",
                "description": "First ensures minimum survival water to sensitive/flowering crops via greedy triage, then optimizes remaining water via DP.",
                "strengths": "Best balance of fairness, zero-crop-starvation, and high economic return.",
                "weaknesses": "Requires baseline survival parameter tuning.",
            },
        ]
    }), 200


@optimization_bp.route("/api/simulate", methods=["POST"])
def simulate_drought():
    """Run drought scenarios across all 5 supply tiers."""
    payload = request.get_json(silent=True) or {}
    farm_id = payload.get("farm_id", 1)

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM farms WHERE id = ?", (farm_id,))
    farm_row = cur.fetchone()
    if not farm_row:
        return jsonify({"error": "Farm not found"}), 404

    cur.execute("SELECT * FROM plots WHERE farm_id = ? ORDER BY id ASC", (farm_id,))
    plots = [Plot.from_dict(dict(r)) for r in cur.fetchall()]

    farm = Farm(
        id=farm_row["id"],
        name=farm_row["name"],
        location=farm_row["location"],
        total_area=farm_row["total_area"],
        water_budget=farm_row["water_budget"],
        reservoir_capacity=farm_row["reservoir_capacity"],
        energy_rate=farm_row["energy_rate"],
        labor_rate=farm_row["labor_rate"],
        pump_capacity=farm_row["pump_capacity"],
        plots=plots,
    )

    simulation_data = run_drought_simulation(farm)
    return jsonify(simulation_data), 200
