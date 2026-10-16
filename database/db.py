"""Database connection and query helpers for CropFlow.

Works both inside Flask application context (using flask.g)
and standalone (for scripts and unit tests).
"""

import os
from pathlib import Path
import sqlite3
from typing import Any, Dict, List, Optional

try:
    from flask import current_app, g
except ImportError:
    current_app = None  # type: ignore
    g = None  # type: ignore

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = str(BASE_DIR / "cropflow.db")
SCHEMA_PATH = str(Path(__file__).resolve().parent / "schema.sql")


def get_db_path() -> str:
    """Determine the active SQLite database path."""
    if current_app and current_app.config.get("DATABASE_PATH"):
        return current_app.config["DATABASE_PATH"]
    return os.getenv("DATABASE_PATH", DEFAULT_DB_PATH)


def get_db_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    """Open or reuse a SQLite database connection with row factory enabled."""
    target_path = db_path or get_db_path()

    if g is not None:
        try:
            if "db" not in g or g.db_path != target_path:
                conn = sqlite3.connect(target_path)
                conn.row_factory = sqlite3.Row
                conn.execute("PRAGMA foreign_keys = ON;")
                g.db = conn
                g.db_path = target_path
            return g.db
        except RuntimeError:
            pass

    conn = sqlite3.connect(target_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def close_db(e: Optional[Exception] = None) -> None:
    """Close the database connection stored in Flask g if present."""
    if g is not None:
        try:
            db = g.pop("db", None)
            if db is not None:
                db.close()
        except RuntimeError:
            pass


def init_db(db_path: Optional[str] = None) -> None:
    """Initialize tables from schema.sql and perform lightweight schema migration if needed."""
    target_path = db_path or get_db_path()
    conn = sqlite3.connect(target_path)
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema_sql = f.read()

    # Split schema to handle index creation safely after potential migrations
    try:
        conn.executescript(schema_sql)
    except sqlite3.OperationalError:
        # Table might already exist without newly added columns
        pass

    # Check farms table columns
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(farms)")
    farm_cols = {row[1] for row in cur.fetchall()}
    if "total_available_water_liters" not in farm_cols and "id" in farm_cols:
        conn.execute("ALTER TABLE farms ADD COLUMN total_available_water_liters REAL DEFAULT 500000.0")
        conn.execute("ALTER TABLE farms ADD COLUMN drought_severity TEXT DEFAULT 'Moderate'")
        conn.execute("ALTER TABLE farms ADD COLUMN drought_factor REAL DEFAULT 0.50")
        conn.execute("ALTER TABLE farms ADD COLUMN window_start TEXT DEFAULT '20:00'")
        conn.execute("ALTER TABLE farms ADD COLUMN window_end TEXT DEFAULT '06:00'")
        conn.execute("ALTER TABLE farms ADD COLUMN window_duration_hours REAL DEFAULT 10.0")

    # Check plots table columns
    cur.execute("PRAGMA table_info(plots)")
    plot_cols = {row[1] for row in cur.fetchall()}
    if "plot_identifier" not in plot_cols and "id" in plot_cols:
        conn.execute("ALTER TABLE plots ADD COLUMN plot_identifier TEXT DEFAULT 'P-101'")
        conn.execute("ALTER TABLE plots ADD COLUMN area REAL DEFAULT 1.0")
        conn.execute("ALTER TABLE plots ADD COLUMN water_required_liters REAL DEFAULT 100000.0")
        conn.execute("ALTER TABLE plots ADD COLUMN cost_per_liter REAL DEFAULT 0.000045")
        conn.execute("ALTER TABLE plots ADD COLUMN remaining_demand_liters REAL DEFAULT 100000.0")
    if "size_hectares" in plot_cols:
        try:
            conn.execute("ALTER TABLE plots DROP COLUMN size_hectares")
        except Exception:
            pass

    # Check optimization_runs table columns
    cur.execute("PRAGMA table_info(optimization_runs)")
    run_cols = {row[1] for row in cur.fetchall()}
    if "objective_value" not in run_cols and "id" in run_cols:
        conn.execute("ALTER TABLE optimization_runs ADD COLUMN objective_value REAL DEFAULT 0.0")
    if "parameters_json" not in run_cols and "id" in run_cols:
        conn.execute("ALTER TABLE optimization_runs ADD COLUMN parameters_json TEXT DEFAULT '{}'")

    # Ensure scenario_settings table exists
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS scenario_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            farm_id INTEGER,
            name TEXT NOT NULL,
            drought_factor REAL NOT NULL DEFAULT 1.0,
            water_override REAL,
            energy_rate_override REAL,
            labor_rate_override REAL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (farm_id) REFERENCES farms (id) ON DELETE CASCADE
        );
        """
    )

    # Ensure indexes exist
    conn.execute("CREATE INDEX IF NOT EXISTS idx_plots_farm_id ON plots (farm_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_runs_farm_id ON optimization_runs (farm_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_allocations_run_id ON allocations (run_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_scenarios_farm_id ON scenario_settings (farm_id)")

    conn.commit()
    conn.close()


def seed_sample_data(db_path: Optional[str] = None, force: bool = False) -> int:
    """Seed sample farm and plots if database is empty or if forced."""
    target_path = db_path or get_db_path()
    init_db(target_path)
    conn = sqlite3.connect(target_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) as cnt FROM farms")
    row = cur.fetchone()
    if row and row["cnt"] > 0 and not force:
        cur.execute("SELECT id FROM farms ORDER BY id ASC LIMIT 1")
        farm_row = cur.fetchone()
        farm_id = farm_row["id"]
        conn.close()
        return farm_id

    if force:
        cur.execute("DELETE FROM scenario_settings")
        cur.execute("DELETE FROM allocations")
        cur.execute("DELETE FROM optimization_runs")
        cur.execute("DELETE FROM plots")
        cur.execute("DELETE FROM farms")

    # Insert sample farm with full parameters
    cur.execute(
        """
        INSERT INTO farms (
            name, location, total_area, total_available_water_liters,
            water_budget, drought_severity, drought_factor,
            window_start, window_end, window_duration_hours,
            reservoir_capacity, energy_rate, labor_rate, pump_capacity
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "Greenfield Valley Agro",
            "Zone 4 - Semi-Arid Basin",
            21.5,
            650000.0,  # 650,000 Liters available
            650.0,     # 650 m3
            "Moderate",
            0.50,
            "20:00",
            "06:00",
            10.0,
            1200000.0,
            0.045,     # $0.045 / m3 energy
            14.0,      # $14.0 / hr labor
            28.0,      # 28 m3/hr pump
        ),
    )
    farm_id = cur.lastrowid

    # Insert realistic diverse plots with unique plot_identifiers
    sample_plots = [
        (
            farm_id,
            "P-101",
            "Plot A - North Wheat",
            4.0,
            "Wheat",
            "Vegetative",
            200000.0,  # required irrigation water in liters
            34.0,      # current moisture %
            70.0,      # target moisture %
            15.0,      # wilting point %
            "Loamy",
            18.0,      # infiltration rate mm/hr
            3,         # priority
            0.000045,  # cost per liter
            130909.0,  # remaining demand liters
            130.91,    # water demand m3
            1600.0,    # crop value $/ha
            0.85,      # Ky sensitivity factor
        ),
        (
            farm_id,
            "P-102",
            "Plot B - Central Corn",
            5.0,
            "Corn",
            "Flowering",  # Highly critical stage!
            300000.0,
            26.0,
            75.0,
            18.0,
            "Clay",
            12.0,
            5,         # Critical priority
            0.000050,
            257894.0,
            257.89,
            2400.0,
            1.40,
        ),
        (
            farm_id,
            "P-103",
            "Plot C - Greenhouse Tomato",
            2.5,
            "Tomato",
            "Flowering",  # High cash value and high sensitivity
            160000.0,
            28.0,
            80.0,
            14.0,
            "Loamy",
            20.0,
            5,
            0.000055,
            126060.0,
            126.06,
            4200.0,
            1.25,
        ),
        (
            farm_id,
            "P-104",
            "Plot D - South Cotton",
            4.5,
            "Cotton",
            "Ripening",  # Low sensitivity in ripening stage
            180000.0,
            38.0,
            65.0,
            10.0,
            "Sandy",
            25.0,
            2,
            0.000040,
            88363.0,
            88.36,
            1800.0,
            0.50,
        ),
        (
            farm_id,
            "P-105",
            "Plot E - East Potato",
            3.0,
            "Potato",
            "Vegetative",
            150000.0,
            30.0,
            72.0,
            13.0,
            "Loamy",
            16.0,
            4,
            0.000045,
            106779.0,
            106.78,
            2100.0,
            0.95,
        ),
        (
            farm_id,
            "P-106",
            "Plot F - West Soybean",
            2.5,
            "Soybean",
            "Initial",
            100000.0,
            42.0,
            65.0,
            17.0,
            "Clay",
            10.0,
            2,
            0.000042,
            47916.0,
            47.92,
            1300.0,
            0.60,
        ),
    ]

    cur.executemany(
        """
        INSERT INTO plots (
            farm_id, plot_identifier, name, area, crop_type, growth_stage,
            water_required_liters, current_moisture, target_moisture,
            wilting_point, soil_type, infiltration_rate, priority,
            cost_per_liter, remaining_demand_liters, water_demand,
            crop_value_per_ha, sensitivity_factor
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        sample_plots,
    )

    # Insert default drought scenario settings for the farm
    sample_scenarios = [
        (farm_id, "Normal Supply", 1.00, None, "100% normal irrigation supply available"),
        (farm_id, "Mild Deficit", 0.75, None, "25% water restriction applied"),
        (farm_id, "Moderate Drought", 0.50, None, "50% water curtailment scenario"),
        (farm_id, "Severe Drought", 0.25, None, "Critical 75% water curtailment scenario"),
        (farm_id, "Emergency Drought", 0.10, None, "Emergency survival supply tier (10%)"),
    ]
    cur.executemany(
        """
        INSERT INTO scenario_settings (farm_id, name, drought_factor, water_override, description)
        VALUES (?, ?, ?, ?, ?)
        """,
        sample_scenarios,
    )

    conn.commit()
    conn.close()
    return farm_id

