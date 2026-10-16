"""Farm and plot data collection, validation, and preprocessing routes."""

import sqlite3
from flask import Blueprint, jsonify, render_template, request
from app.models.farm import Farm, Plot
from app.services.preprocessing import (
    DEFAULT_CROP_VALUES,
    DEFAULT_SOIL_PROPERTIES,
    DEFAULT_STAGE_SENSITIVITY,
    DROUGHT_SEVERITY_FACTORS,
    ValidationError,
    calculate_remaining_water_demand,
    validate_farm_input,
    validate_plot_input,
)
from database.db import get_db_connection, seed_sample_data

farms_bp = Blueprint("farms", __name__)


@farms_bp.route("/farms")
def view_farms():
    """Render farm and plot data collection UI with responsive forms and validation feedback."""
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) as cnt FROM farms")
    if cur.fetchone()["cnt"] == 0:
        seed_sample_data()

    cur.execute("SELECT id, name, location, total_available_water_liters, water_budget, total_area, drought_severity FROM farms ORDER BY id ASC")
    farms_rows = [dict(r) for r in cur.fetchall()]

    selected_id = request.args.get("farm_id", type=int)
    if not selected_id and farms_rows:
        selected_id = farms_rows[0]["id"]

    farm_data = None
    plots_data = []

    if selected_id:
        cur.execute("SELECT * FROM farms WHERE id = ?", (selected_id,))
        row = cur.fetchone()
        if row:
            farm_data = dict(row)
            cur.execute("SELECT * FROM plots WHERE farm_id = ? ORDER BY id ASC", (selected_id,))
            plots_data = [Plot.from_dict(dict(r)).to_dict() for r in cur.fetchall()]

    return render_template(
        "farms.html",
        farms=farms_rows,
        selected_farm=farm_data,
        plots=plots_data,
        soil_types=list(DEFAULT_SOIL_PROPERTIES.keys()),
        crop_types=list(DEFAULT_CROP_VALUES.keys()),
        stages=list(DEFAULT_STAGE_SENSITIVITY.keys()),
        drought_severities=list(DROUGHT_SEVERITY_FACTORS.keys()),
    )


@farms_bp.route("/api/farms", methods=["GET"])
def list_farms():
    """List all registered farms with water availability and drought settings."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM farms ORDER BY id ASC")
    rows = [dict(r) for r in cur.fetchall()]
    return jsonify({"farms": rows}), 200


@farms_bp.route("/api/farms/<int:farm_id>", methods=["GET"])
def get_farm(farm_id: int):
    """Retrieve full details of a farm including plots and calculated demand."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM farms WHERE id = ?", (farm_id,))
    farm_row = cur.fetchone()
    if not farm_row:
        return jsonify({"error": "Farm not found"}), 404

    cur.execute("SELECT * FROM plots WHERE farm_id = ? ORDER BY id ASC", (farm_id,))
    plots = [Plot.from_dict(dict(r)).to_dict() for r in cur.fetchall()]

    data = dict(farm_row)
    data["plots"] = plots
    return jsonify(data), 200


@farms_bp.route("/api/farms", methods=["POST"])
def create_farm():
    """Create a new farm with validation for available water, drought severity, and time window."""
    payload = request.get_json(silent=True) or {}
    try:
        cleaned = validate_farm_input(payload)
    except ValidationError as ve:
        return jsonify({"error": "Validation failed", "field_errors": ve.errors}), 400

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO farms (
            name, location, total_available_water_liters, water_budget,
            drought_severity, drought_factor, window_start, window_end,
            window_duration_hours, pump_capacity, energy_rate, labor_rate,
            total_area, reservoir_capacity
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            cleaned["name"],
            cleaned["location"],
            cleaned["total_available_water_liters"],
            cleaned["water_budget"],
            cleaned["drought_severity"],
            cleaned["drought_factor"],
            cleaned["window_start"],
            cleaned["window_end"],
            cleaned["window_duration_hours"],
            cleaned["pump_capacity"],
            cleaned["energy_rate"],
            cleaned["labor_rate"],
            0.0,
            cleaned["total_available_water_liters"] * 1.5,
        ),
    )
    conn.commit()
    new_id = cur.lastrowid
    return jsonify({"message": "Farm created successfully", "farm_id": new_id, "farm": cleaned}), 201


@farms_bp.route("/api/farms/<int:farm_id>", methods=["PUT"])
def update_farm(farm_id: int):
    """Update farm parameters with numeric validation."""
    payload = request.get_json(silent=True) or {}
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM farms WHERE id = ?", (farm_id,))
    if not cur.fetchone():
        return jsonify({"error": "Farm not found"}), 404

    try:
        cleaned = validate_farm_input(payload)
    except ValidationError as ve:
        return jsonify({"error": "Validation failed", "field_errors": ve.errors}), 400

    cur.execute(
        """
        UPDATE farms SET
            name = ?, location = ?, total_available_water_liters = ?,
            water_budget = ?, drought_severity = ?, drought_factor = ?,
            window_start = ?, window_end = ?, window_duration_hours = ?,
            pump_capacity = ?, energy_rate = ?, labor_rate = ?
        WHERE id = ?
        """,
        (
            cleaned["name"],
            cleaned["location"],
            cleaned["total_available_water_liters"],
            cleaned["water_budget"],
            cleaned["drought_severity"],
            cleaned["drought_factor"],
            cleaned["window_start"],
            cleaned["window_end"],
            cleaned["window_duration_hours"],
            cleaned["pump_capacity"],
            cleaned["energy_rate"],
            cleaned["labor_rate"],
            farm_id,
        ),
    )
    conn.commit()
    return jsonify({"message": "Farm updated successfully", "farm": cleaned}), 200


@farms_bp.route("/api/farms/<int:farm_id>", methods=["DELETE"])
def delete_farm(farm_id: int):
    """Delete a farm and its associated plots."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM farms WHERE id = ?", (farm_id,))
    conn.commit()
    return jsonify({"message": f"Farm {farm_id} deleted."}), 200


@farms_bp.route("/api/farms/<int:farm_id>/plots", methods=["POST"])
def add_plot(farm_id: int):
    """Add a plot with strict validation for non-negativity, moisture 0-100%, and unique Plot ID."""
    payload = request.get_json(silent=True) or {}
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT id FROM farms WHERE id = ?", (farm_id,))
    if not cur.fetchone():
        return jsonify({"error": "Farm not found"}), 404

    # Fetch existing plot identifiers for uniqueness check
    cur.execute("SELECT plot_identifier FROM plots WHERE farm_id = ?", (farm_id,))
    existing_ids = [row["plot_identifier"] for row in cur.fetchall()]

    try:
        cleaned = validate_plot_input(payload, existing_plot_identifiers=existing_ids)
    except ValidationError as ve:
        return jsonify({"error": "Validation failed", "field_errors": ve.errors}), 400

    try:
        cur.execute(
            """
            INSERT INTO plots (
                farm_id, plot_identifier, name, area, crop_type, growth_stage,
                water_required_liters, current_moisture, target_moisture,
                wilting_point, soil_type, infiltration_rate, priority,
                cost_per_liter, remaining_demand_liters, water_demand,
                crop_value_per_ha, sensitivity_factor
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                farm_id,
                cleaned["plot_identifier"],
                cleaned["name"],
                cleaned["area"],
                cleaned["crop_type"],
                cleaned["growth_stage"],
                cleaned["water_required_liters"],
                cleaned["current_moisture"],
                cleaned["target_moisture"],
                cleaned["wilting_point"],
                cleaned["soil_type"],
                cleaned["infiltration_rate"],
                cleaned["priority"],
                cleaned["cost_per_liter"],
                cleaned["remaining_demand_liters"],
                cleaned["water_demand"],
                cleaned["crop_value_per_ha"],
                cleaned["sensitivity_factor"],
            ),
        )
        new_plot_id = cur.lastrowid

        # Update total farm area
        cur.execute("SELECT SUM(area) as total FROM plots WHERE farm_id = ?", (farm_id,))
        tot_area = cur.fetchone()["total"] or 0.0
        cur.execute("UPDATE farms SET total_area = ? WHERE id = ?", (round(tot_area, 2), farm_id))

        conn.commit()
    except sqlite3.IntegrityError:
        return jsonify({
            "error": "Validation failed",
            "field_errors": {"plot_identifier": f"Plot ID '{cleaned['plot_identifier']}' already exists in this farm."}
        }), 400

    return jsonify({
        "message": "Plot added successfully",
        "plot_id": new_plot_id,
        "plot": cleaned,
    }), 201


@farms_bp.route("/api/plots/<int:plot_id>", methods=["PUT"])
def update_plot(plot_id: int):
    """Update plot parameters with uniqueness and non-negativity validation."""
    payload = request.get_json(silent=True) or {}
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT farm_id, plot_identifier FROM plots WHERE id = ?", (plot_id,))
    existing = cur.fetchone()
    if not existing:
        return jsonify({"error": "Plot not found"}), 404

    farm_id = existing["farm_id"]
    current_identifier = existing["plot_identifier"]

    # Check other plots for duplicate identifier
    cur.execute("SELECT plot_identifier FROM plots WHERE farm_id = ? AND id != ?", (farm_id, plot_id))
    other_ids = [row["plot_identifier"] for row in cur.fetchall()]

    try:
        cleaned = validate_plot_input(payload, existing_plot_identifiers=other_ids)
    except ValidationError as ve:
        return jsonify({"error": "Validation failed", "field_errors": ve.errors}), 400

    cur.execute(
        """
        UPDATE plots SET
            plot_identifier = ?, name = ?, area = ?, crop_type = ?,
            growth_stage = ?, water_required_liters = ?, current_moisture = ?,
            target_moisture = ?, wilting_point = ?, soil_type = ?,
            infiltration_rate = ?, priority = ?, cost_per_liter = ?,
            remaining_demand_liters = ?, water_demand = ?,
            crop_value_per_ha = ?, sensitivity_factor = ?
        WHERE id = ?
        """,
        (
            cleaned["plot_identifier"],
            cleaned["name"],
            cleaned["area"],
            cleaned["crop_type"],
            cleaned["growth_stage"],
            cleaned["water_required_liters"],
            cleaned["current_moisture"],
            cleaned["target_moisture"],
            cleaned["wilting_point"],
            cleaned["soil_type"],
            cleaned["infiltration_rate"],
            cleaned["priority"],
            cleaned["cost_per_liter"],
            cleaned["remaining_demand_liters"],
            cleaned["water_demand"],
            cleaned["crop_value_per_ha"],
            cleaned["sensitivity_factor"],
            plot_id,
        ),
    )

    # Update farm total area
    cur.execute("SELECT SUM(area) as total FROM plots WHERE farm_id = ?", (farm_id,))
    tot_area = cur.fetchone()["total"] or 0.0
    cur.execute("UPDATE farms SET total_area = ? WHERE id = ?", (round(tot_area, 2), farm_id))

    conn.commit()
    return jsonify({"message": "Plot updated successfully", "plot": cleaned}), 200


@farms_bp.route("/api/plots/<int:plot_id>", methods=["DELETE"])
def delete_plot(plot_id: int):
    """Delete a plot."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT farm_id FROM plots WHERE id = ?", (plot_id,))
    existing = cur.fetchone()
    if not existing:
        return jsonify({"error": "Plot not found"}), 404

    farm_id = existing["farm_id"]
    cur.execute("DELETE FROM plots WHERE id = ?", (plot_id,))

    cur.execute("SELECT SUM(area) as total FROM plots WHERE farm_id = ?", (farm_id,))
    tot_area = cur.fetchone()["total"] or 0.0
    cur.execute("UPDATE farms SET total_area = ? WHERE id = ?", (round(tot_area, 2), farm_id))

    conn.commit()
    return jsonify({"message": f"Plot {plot_id} deleted."}), 200


@farms_bp.route("/api/plots/calculate-demand", methods=["POST"])
def api_calculate_demand():
    """Client utility endpoint to preview remaining water demand and view documented assumptions."""
    payload = request.get_json(silent=True) or {}
    try:
        area = float(payload.get("area", 1.0))
        req_liters = float(payload.get("water_required_liters", 100000.0))
        current_m = float(payload.get("current_moisture", 30.0))
        target_m = float(payload.get("target_moisture", 75.0))
        wilting_p = float(payload.get("wilting_point", 15.0))

        if area < 0 or req_liters < 0 or current_m < 0 or current_m > 100:
            return jsonify({
                "error": "Invalid inputs. Area, required water must be non-negative; moisture must be 0-100%."
            }), 400

        result = calculate_remaining_water_demand(
            area_hectares=area,
            water_required_liters=req_liters,
            current_moisture_pct=current_m,
            target_moisture_pct=target_m,
            wilting_point_pct=wilting_p,
        )
        return jsonify(result), 200
    except (ValueError, TypeError) as e:
        return jsonify({"error": f"Invalid numeric input: {str(e)}"}), 400


@farms_bp.route("/api/farms/seed", methods=["POST"])
def reseed_farm_data():
    """Reset and seed the sample Greenfield Valley farm with realistic testing data."""
    farm_id = seed_sample_data(force=True)
    return jsonify({"message": "Sample farm data seeded successfully", "farm_id": farm_id}), 200
