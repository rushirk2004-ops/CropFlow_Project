-- CropFlow Database Schema
-- SQLite table definitions for Farms, Plots, Optimization Runs, Plot Allocations, and Scenario Settings.
-- Supports farm data collection, strict validation, and remaining water demand preprocessing.

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS farms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    location TEXT,
    total_area REAL DEFAULT 0.0,
    total_available_water_liters REAL NOT NULL,
    water_budget REAL NOT NULL, -- Synchronized in m3 or liters for backwards-compatibility
    drought_severity TEXT DEFAULT 'Moderate', -- None, Mild, Moderate, Severe, Extreme
    drought_factor REAL DEFAULT 0.50,         -- Water reduction multiplier (0.00 to 0.90)
    window_start TEXT DEFAULT '20:00',         -- Irrigation start window
    window_end TEXT DEFAULT '06:00',           -- Irrigation end window
    window_duration_hours REAL DEFAULT 10.0,   -- Time window in hours
    reservoir_capacity REAL DEFAULT 0.0,
    energy_rate REAL DEFAULT 0.045,            -- Pumping energy rate ($/m3)
    labor_rate REAL DEFAULT 14.0,              -- Labor rate ($/hour)
    pump_capacity REAL DEFAULT 25.0,           -- Pump flow capacity (m3/h)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS plots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    farm_id INTEGER NOT NULL,
    plot_identifier TEXT NOT NULL,             -- Unique plot identifier within a farm (e.g. P-101)
    name TEXT NOT NULL,
    area REAL NOT NULL,                        -- Area in hectares
    crop_type TEXT NOT NULL,                   -- Wheat, Corn, Tomato, Cotton, etc.
    growth_stage TEXT NOT NULL,                -- Initial, Vegetative, Flowering, Ripening
    water_required_liters REAL NOT NULL,       -- Gross baseline irrigation requirement in liters
    current_moisture REAL NOT NULL,            -- Current soil moisture percentage (0 - 100%)
    target_moisture REAL DEFAULT 75.0,         -- Soil field capacity target moisture %
    wilting_point REAL DEFAULT 15.0,           -- Permanent wilting point %
    soil_type TEXT NOT NULL,                   -- Sandy, Loamy, Clay
    infiltration_rate REAL NOT NULL,           -- Soil infiltration rate in mm/hour
    priority INTEGER NOT NULL,                 -- Crop priority scale (1 to 5)
    cost_per_liter REAL NOT NULL,              -- Estimated irrigation cost ($/liter)
    remaining_demand_liters REAL NOT NULL,     -- Preprocessed net water demand in liters
    water_demand REAL NOT NULL,                -- Stored water demand (liters / m3)
    crop_value_per_ha REAL DEFAULT 1800.0,     -- Economic crop market value ($/ha)
    sensitivity_factor REAL DEFAULT 1.0,       -- FAO-33 Ky yield sensitivity factor
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(farm_id, plot_identifier),
    FOREIGN KEY (farm_id) REFERENCES farms (id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS optimization_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    farm_id INTEGER,
    algorithm TEXT NOT NULL,
    scenario_name TEXT DEFAULT 'Standard',
    available_water REAL NOT NULL,
    total_demand REAL NOT NULL,
    total_allocated REAL NOT NULL,
    unmet_demand REAL NOT NULL,
    water_utilization_pct REAL NOT NULL,
    total_cost REAL NOT NULL,
    total_benefit REAL NOT NULL,
    net_return REAL NOT NULL,
    objective_value REAL DEFAULT 0.0,          -- Standardized objective value
    parameters_json TEXT DEFAULT '{}',         -- Serialized input parameters
    execution_time_ms REAL NOT NULL,
    fairness_index REAL DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (farm_id) REFERENCES farms (id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS allocations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL,
    plot_id INTEGER NOT NULL,
    allocated_water REAL NOT NULL,
    demand REAL NOT NULL,
    coverage_pct REAL NOT NULL,
    stress_index REAL DEFAULT 0.0,
    yield_preservation_pct REAL DEFAULT 0.0,
    cost REAL NOT NULL,
    scheduled_start_hour REAL DEFAULT 0.0,
    scheduled_duration_hours REAL DEFAULT 0.0,
    flow_rate REAL DEFAULT 0.0,
    FOREIGN KEY (run_id) REFERENCES optimization_runs (id) ON DELETE CASCADE,
    FOREIGN KEY (plot_id) REFERENCES plots (id) ON DELETE CASCADE
);

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

CREATE INDEX IF NOT EXISTS idx_plots_farm_id ON plots (farm_id);
CREATE INDEX IF NOT EXISTS idx_plots_identifier ON plots (farm_id, plot_identifier);
CREATE INDEX IF NOT EXISTS idx_runs_farm_id ON optimization_runs (farm_id);
CREATE INDEX IF NOT EXISTS idx_allocations_run_id ON allocations (run_id);
CREATE INDEX IF NOT EXISTS idx_scenarios_farm_id ON scenario_settings (farm_id);
