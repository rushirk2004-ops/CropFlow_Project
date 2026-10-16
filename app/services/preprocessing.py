"""Data Preprocessing and Validation Service for CropFlow.

This module processes manually entered or simulated agronomic inputs for farm plots:
- Plot ID, area, crop type, growth stage
- Required irrigation water in liters
- Current soil moisture percentage (0-100%)
- Soil type and infiltration rate
- Crop priority (1-5)
- Estimated irrigation cost per liter
- Total available water, drought severity, and irrigation time windows.

NOTE: This system relies strictly on manual data entry or simulated agricultural
scenarios; no real-time telemetry or active sensor streaming is used.

Assumptions for Calculating Remaining Water Demand:
--------------------------------------------------
1. Field Capacity (FC) & Wilting Point (WP):
   Each soil type defines optimal Field Capacity (Target Moisture) and Permanent Wilting Point (WP).
   Standard agronomic baselines:
     - Loamy: FC = 75%, WP = 14%
     - Clay:  FC = 80%, WP = 18%
     - Sandy: FC = 65%, WP = 9%
2. Soil Moisture Deficit Ratio (R_deficit):
   R_deficit = max(0.0, min(1.0, (FC - Current Moisture) / max(1.0, FC - WP)))
   - If Current Moisture >= Target Moisture (FC), R_deficit = 0.0 (no irrigation needed).
   - If Current Moisture <= Wilting Point (WP), R_deficit = 1.0 (full irrigation required).
3. Gross Water Need (W_gross):
   W_gross is the baseline required irrigation water (in liters) for the crop stage.
   If not explicitly provided by the user, it is derived from root zone depth (0.5m)
   across the plot area: W_gross = Area (ha) * 10,000 m2/ha * 0.5m * 1000 L/m3 * (FC - WP)/100.
4. Net Remaining Demand (D_rem in Liters):
   D_rem = round(W_gross * R_deficit, 2)
   Water already in the root zone above wilting point reduces the required irrigation volume.
"""

import sqlite3
from typing import Any, Dict, List, Optional, Tuple
from app.models.farm import Farm, Plot

DEFAULT_SOIL_PROPERTIES = {
    "Sandy": {"infiltration_rate": 25.0, "wilting_point": 9.0, "field_capacity": 65.0},
    "Loamy": {"infiltration_rate": 16.0, "wilting_point": 14.0, "field_capacity": 75.0},
    "Clay": {"infiltration_rate": 10.0, "wilting_point": 18.0, "field_capacity": 80.0},
}

DEFAULT_STAGE_SENSITIVITY = {
    "Flowering": 1.35,
    "Yield Formation": 1.25,
    "Vegetative": 0.90,
    "Initial": 0.65,
    "Ripening": 0.50,
}

DEFAULT_CROP_VALUES = {
    "Tomato": 4200.0,
    "Potato": 2200.0,
    "Corn": 2400.0,
    "Cotton": 1850.0,
    "Wheat": 1600.0,
    "Soybean": 1400.0,
    "Rice": 2000.0,
    "Sugarcane": 2800.0,
}

DROUGHT_SEVERITY_FACTORS = {
    "None": 0.00,
    "Mild": 0.25,
    "Moderate": 0.50,
    "Severe": 0.75,
    "Extreme": 0.90,
}


class ValidationError(Exception):
    """Exception raised when an agronomic input fails numeric or domain validation."""

    def __init__(self, errors: Dict[str, str]):
        super().__init__("; ".join(f"{k}: {v}" for k, v in errors.items()))
        self.errors = errors


def calculate_remaining_water_demand(
    area_hectares: float,
    water_required_liters: float,
    current_moisture_pct: float,
    target_moisture_pct: float = 75.0,
    wilting_point_pct: float = 15.0,
) -> Dict[str, Any]:
    """Calculate the remaining water demand in liters based on documented assumptions.

    Assumptions:
    1. If current soil moisture is at or exceeds target moisture, remaining demand is 0 L.
    2. Effective deficit fraction = (target_moisture - current_moisture) / (target_moisture - wilting_point).
    3. Remaining demand = water_required_liters * deficit_fraction.
    """
    if current_moisture_pct >= target_moisture_pct:
        return {
            "remaining_demand_liters": 0.0,
            "deficit_ratio": 0.0,
            "soil_status": "Saturated / At Field Capacity",
            "assumptions_applied": [
                f"Current soil moisture ({current_moisture_pct}%) >= target moisture ({target_moisture_pct}%).",
                "No irrigation required at this time.",
            ],
        }

    available_water_range = max(1.0, target_moisture_pct - wilting_point_pct)
    current_deficit = max(0.0, target_moisture_pct - current_moisture_pct)
    deficit_ratio = min(1.0, current_deficit / available_water_range)

    # If baseline liters not supplied, calculate volumetric estimate
    base_liters = water_required_liters
    if base_liters <= 0:
        # 1 ha = 10,000 m2; root depth = 0.5 m; 1 m3 = 1000 L
        root_depth_m = 0.5
        vol_m3 = area_hectares * 10000.0 * root_depth_m * (available_water_range / 100.0)
        base_liters = vol_m3 * 1000.0

    remaining_liters = round(base_liters * deficit_ratio, 2)

    return {
        "remaining_demand_liters": remaining_liters,
        "deficit_ratio": round(deficit_ratio, 4),
        "soil_status": "Moisture Deficit Active",
        "assumptions_applied": [
            f"Available water capacity range = {target_moisture_pct}% - {wilting_point_pct}% = {available_water_range:.1f}%.",
            f"Current root zone moisture deficit = {current_deficit:.1f}%.",
            f"Deficit ratio = {current_deficit:.1f} / {available_water_range:.1f} = {deficit_ratio:.2%}.",
            f"Remaining demand = {base_liters:,.0f} L * {deficit_ratio:.2%} = {remaining_liters:,.2f} Liters.",
        ],
    }


def validate_plot_input(
    plot_data: Dict[str, Any],
    existing_plot_identifiers: Optional[List[str]] = None,
    current_plot_id: Optional[int] = None,
) -> Dict[str, Any]:
    """Validate plot inputs, enforce bounds and non-negativity, and compute remaining water demand.

    Raises:
        ValidationError: if any validation rule is violated.
    """
    errors: Dict[str, str] = {}
    cleaned: Dict[str, Any] = {}

    # 1. Plot Identifier & Uniqueness
    plot_id = str(plot_data.get("plot_identifier") or plot_data.get("plot_id") or "").strip()
    if not plot_id:
        errors["plot_identifier"] = "Plot ID is required (e.g. 'P-101' or 'Plot-A')."
    elif existing_plot_identifiers and plot_id in existing_plot_identifiers:
        errors["plot_identifier"] = f"Plot ID '{plot_id}' already exists in this farm. Plot IDs must be unique within a farm."
    cleaned["plot_identifier"] = plot_id
    cleaned["name"] = str(plot_data.get("name") or f"Plot {plot_id}").strip()

    # 2. Area (hectares)
    try:
        area = float(plot_data.get("area") if plot_data.get("area") is not None else plot_data.get("size_hectares", 1.0))
        if area <= 0:
            errors["area"] = "Plot area must be a positive number greater than 0 (hectares)."
        else:
            cleaned["area"] = round(area, 2)
            cleaned["size_hectares"] = cleaned["area"]
    except (ValueError, TypeError):
        errors["area"] = "Plot area must be a valid numeric value."

    # 3. Crop Type & Growth Stage
    crop = str(plot_data.get("crop_type", "Wheat")).strip().capitalize()
    if not crop:
        errors["crop_type"] = "Crop type is required."
    cleaned["crop_type"] = crop

    stage = str(plot_data.get("growth_stage", "Vegetative")).strip().capitalize()
    if stage not in DEFAULT_STAGE_SENSITIVITY:
        stage = "Vegetative"
    cleaned["growth_stage"] = stage

    # 4. Soil Type & Infiltration Rate
    soil = str(plot_data.get("soil_type", "Loamy")).strip().capitalize()
    if soil not in DEFAULT_SOIL_PROPERTIES:
        soil = "Loamy"
    cleaned["soil_type"] = soil

    soil_defaults = DEFAULT_SOIL_PROPERTIES[soil]

    try:
        inf = float(plot_data.get("infiltration_rate", soil_defaults["infiltration_rate"]))
        if inf <= 0:
            errors["infiltration_rate"] = "Infiltration rate must be a positive number greater than 0 (mm/hr)."
        else:
            cleaned["infiltration_rate"] = round(inf, 1)
    except (ValueError, TypeError):
        errors["infiltration_rate"] = "Infiltration rate must be a valid numeric value."

    # 5. Soil Moisture Percentage (0 to 100%)
    try:
        moisture = float(plot_data.get("current_moisture", 30.0))
        if moisture < 0.0 or moisture > 100.0:
            errors["current_moisture"] = "Current soil moisture must be between 0.0% and 100.0%."
        else:
            cleaned["current_moisture"] = round(moisture, 1)
    except (ValueError, TypeError):
        errors["current_moisture"] = "Soil moisture percentage must be a valid numeric value."

    # Target moisture & wilting point
    try:
        target_m = float(plot_data.get("target_moisture", soil_defaults["field_capacity"]))
        if target_m < 0.0 or target_m > 100.0:
            errors["target_moisture"] = "Target soil moisture must be between 0.0% and 100.0%."
        else:
            cleaned["target_moisture"] = round(target_m, 1)
    except (ValueError, TypeError):
        cleaned["target_moisture"] = soil_defaults["field_capacity"]

    try:
        wp = float(plot_data.get("wilting_point", soil_defaults["wilting_point"]))
        if wp < 0.0 or wp > 100.0:
            errors["wilting_point"] = "Wilting point must be between 0.0% and 100.0%."
        else:
            cleaned["wilting_point"] = round(wp, 1)
    except (ValueError, TypeError):
        cleaned["wilting_point"] = soil_defaults["wilting_point"]

    # 6. Required Irrigation Water in Liters
    try:
        req_liters = float(plot_data.get("water_required_liters", 0.0))
        if req_liters < 0:
            errors["water_required_liters"] = "Required irrigation water in liters cannot be negative."
        else:
            cleaned["water_required_liters"] = round(req_liters, 2)
    except (ValueError, TypeError):
        errors["water_required_liters"] = "Required irrigation water must be a valid numeric value."

    # 7. Crop Priority (1 to 5)
    try:
        prio = int(plot_data.get("priority", 3))
        if prio < 1 or prio > 5:
            errors["priority"] = "Crop priority must be an integer between 1 (lowest) and 5 (critical)."
        else:
            cleaned["priority"] = prio
    except (ValueError, TypeError):
        errors["priority"] = "Crop priority must be an integer between 1 and 5."

    # 8. Estimated Irrigation Cost per Liter ($/L)
    try:
        cost_l = float(plot_data.get("cost_per_liter", 0.000045))
        if cost_l < 0:
            errors["cost_per_liter"] = "Estimated irrigation cost per liter cannot be negative."
        else:
            cleaned["cost_per_liter"] = round(cost_l, 6)
    except (ValueError, TypeError):
        errors["cost_per_liter"] = "Cost per liter must be a valid numeric value."

    # Crop economic market value & Ky sensitivity
    try:
        val = float(plot_data.get("crop_value_per_ha", DEFAULT_CROP_VALUES.get(crop, 1800.0)))
        if val < 0:
            errors["crop_value_per_ha"] = "Crop value per hectare cannot be negative."
        cleaned["crop_value_per_ha"] = round(val, 2)
    except (ValueError, TypeError):
        cleaned["crop_value_per_ha"] = DEFAULT_CROP_VALUES.get(crop, 1800.0)

    try:
        ky = float(plot_data.get("sensitivity_factor", DEFAULT_STAGE_SENSITIVITY.get(stage, 0.90)))
        if ky < 0:
            errors["sensitivity_factor"] = "Sensitivity factor Ky cannot be negative."
        cleaned["sensitivity_factor"] = round(ky, 2)
    except (ValueError, TypeError):
        cleaned["sensitivity_factor"] = DEFAULT_STAGE_SENSITIVITY.get(stage, 0.90)

    if errors:
        raise ValidationError(errors)

    # 9. Calculate Remaining Water Demand using documented assumptions
    calc_res = calculate_remaining_water_demand(
        area_hectares=cleaned["area"],
        water_required_liters=cleaned["water_required_liters"],
        current_moisture_pct=cleaned["current_moisture"],
        target_moisture_pct=cleaned["target_moisture"],
        wilting_point_pct=cleaned["wilting_point"],
    )

    cleaned["remaining_demand_liters"] = calc_res["remaining_demand_liters"]
    cleaned["water_demand"] = round(calc_res["remaining_demand_liters"] / 1000.0, 3)
    cleaned["calculation_details"] = calc_res

    return cleaned


def validate_farm_input(farm_data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate farm-level parameters, total available water, drought severity, and time windows.

    Raises:
        ValidationError: if any field fails validation.
    """
    errors: Dict[str, str] = {}
    cleaned: Dict[str, Any] = {}

    # Farm Name
    name = str(farm_data.get("name", "")).strip()
    if not name:
        errors["name"] = "Farm name is required."
    cleaned["name"] = name
    cleaned["location"] = str(farm_data.get("location", "Zone Agricultural Basin")).strip()

    # Total Available Water in Liters (non-negative)
    try:
        raw_water = farm_data.get("total_available_water_liters")
        if raw_water is None:
            raw_water = float(farm_data.get("water_budget", 500.0)) * 1000.0
        avail_liters = float(raw_water)
        if avail_liters < 0:
            errors["total_available_water_liters"] = "Total available water in liters cannot be negative."
        else:
            cleaned["total_available_water_liters"] = round(avail_liters, 2)
            cleaned["water_budget"] = round(avail_liters / 1000.0, 2)
    except (ValueError, TypeError):
        errors["total_available_water_liters"] = "Total available water must be a valid number."

    # Drought Severity
    severity = str(farm_data.get("drought_severity", "Moderate")).strip().capitalize()
    if severity not in DROUGHT_SEVERITY_FACTORS:
        severity = "Moderate"
    cleaned["drought_severity"] = severity
    cleaned["drought_factor"] = DROUGHT_SEVERITY_FACTORS[severity]

    # Irrigation Time Window
    w_start = str(farm_data.get("window_start", "20:00")).strip()
    w_end = str(farm_data.get("window_end", "06:00")).strip()
    cleaned["window_start"] = w_start
    cleaned["window_end"] = w_end

    try:
        dur = float(farm_data.get("window_duration_hours", 10.0))
        if dur <= 0 or dur > 24.0:
            errors["window_duration_hours"] = "Irrigation window duration must be between 0.5 and 24 hours."
        else:
            cleaned["window_duration_hours"] = round(dur, 1)
    except (ValueError, TypeError):
        cleaned["window_duration_hours"] = 10.0

    # Economics
    try:
        pump = float(farm_data.get("pump_capacity", 25.0))
        if pump <= 0:
            errors["pump_capacity"] = "Pump flow capacity must be greater than 0 (m3/h)."
        cleaned["pump_capacity"] = round(pump, 1)
    except (ValueError, TypeError):
        cleaned["pump_capacity"] = 25.0

    try:
        energy = float(farm_data.get("energy_rate", 0.045))
        if energy < 0:
            errors["energy_rate"] = "Energy rate cannot be negative."
        cleaned["energy_rate"] = round(energy, 4)
    except (ValueError, TypeError):
        cleaned["energy_rate"] = 0.045

    try:
        labor = float(farm_data.get("labor_rate", 14.0))
        if labor < 0:
            errors["labor_rate"] = "Labor rate cannot be negative."
        cleaned["labor_rate"] = round(labor, 2)
    except (ValueError, TypeError):
        cleaned["labor_rate"] = 14.0

    if errors:
        raise ValidationError(errors)

    return cleaned


def prepare_farm_dataset(farm_data: Dict[str, Any]) -> Tuple[Farm, List[str]]:
    """Validate farm and all child plots, enforcing plot ID uniqueness within the farm."""
    cleaned_farm = validate_farm_input(farm_data)
    warnings: List[str] = []

    plots_raw = farm_data.get("plots", [])
    cleaned_plots: List[Plot] = []
    seen_identifiers: List[str] = []

    for item in plots_raw:
        if isinstance(item, Plot):
            if item.plot_identifier in seen_identifiers:
                raise ValidationError({"plot_identifier": f"Duplicate plot ID '{item.plot_identifier}' within farm."})
            seen_identifiers.append(item.plot_identifier)
            cleaned_plots.append(item)
            continue

        item_dict = dict(item)
        cleaned_plot_dict = validate_plot_input(item_dict, existing_plot_identifiers=seen_identifiers)
        seen_identifiers.append(cleaned_plot_dict["plot_identifier"])
        cleaned_plots.append(Plot.from_dict(cleaned_plot_dict))

    total_area = sum(p.area for p in cleaned_plots)

    farm = Farm(
        id=farm_data.get("id"),
        name=cleaned_farm["name"],
        location=cleaned_farm["location"],
        total_available_water_liters=cleaned_farm["total_available_water_liters"],
        drought_severity=cleaned_farm["drought_severity"],
        drought_factor=cleaned_farm["drought_factor"],
        window_start=cleaned_farm["window_start"],
        window_end=cleaned_farm["window_end"],
        window_duration_hours=cleaned_farm["window_duration_hours"],
        total_area=round(total_area, 2),
        reservoir_capacity=float(farm_data.get("reservoir_capacity", cleaned_farm["total_available_water_liters"] * 1.5)),
        energy_rate=cleaned_farm["energy_rate"],
        labor_rate=cleaned_farm["labor_rate"],
        pump_capacity=cleaned_farm["pump_capacity"],
        plots=cleaned_plots,
    )

    return farm, warnings


def generate_water_demand_matrix(plots: List[Plot]) -> Dict[str, Any]:
    """Generate aggregate water demand matrix and distribution breakdown."""
    total_liters = sum(p.remaining_demand_liters for p in plots)
    total_area = sum(p.area for p in plots)

    by_stage: Dict[str, float] = {}
    by_crop: Dict[str, float] = {}
    by_soil: Dict[str, float] = {}

    for p in plots:
        by_stage[p.growth_stage] = round(by_stage.get(p.growth_stage, 0.0) + p.remaining_demand_liters, 2)
        by_crop[p.crop_type] = round(by_crop.get(p.crop_type, 0.0) + p.remaining_demand_liters, 2)
        by_soil[p.soil_type] = round(by_soil.get(p.soil_type, 0.0) + p.remaining_demand_liters, 2)

    return {
        "total_demand_liters": round(total_liters, 2),
        "total_demand_m3": round(total_liters / 1000.0, 3),
        "total_area_ha": round(total_area, 2),
        "demand_by_stage_liters": by_stage,
        "demand_by_crop_liters": by_crop,
        "demand_by_soil_liters": by_soil,
    }


# Backwards-compatibility aliases
clean_and_validate_plot = validate_plot_input
calculate_plot_demand = calculate_remaining_water_demand
