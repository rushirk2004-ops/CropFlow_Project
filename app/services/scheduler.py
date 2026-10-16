"""Irrigation Scheduling Service.

Transforms water allocation quantities into an actionable, time-slotted irrigation
schedule respecting pump capacities, soil infiltration thresholds, and off-peak tariffs.
"""

from typing import List
from app.models.farm import Farm, Plot
from app.models.result import OptimizationResult, ScheduleItem


def format_hour_to_time_str(hour_float: float) -> str:
    """Format fractional hours (e.g. 20.5) into HH:MM clock format (e.g. 20:30)."""
    norm_hour = hour_float % 24.0
    h = int(norm_hour)
    m = int(round((norm_hour - h) * 60.0))
    if m == 60:
        h = (h + 1) % 24
        m = 0
    return f"{h:02d}:{m:02d}"


def build_irrigation_schedule(
    optimization_result: OptimizationResult,
    farm: Farm,
    start_hour: float = 20.0,  # 8:00 PM night start (evaporation minimization)
) -> OptimizationResult:
    """Construct hour-by-hour operational schedule for allocated irrigation water.

    Enforces:
    1. Maximum infiltration flow rate: Q_plot <= Infiltration (mm/hr) * Area (ha) * 10
    2. Pump operational flow rate: Q <= farm.pump_capacity
    3. Off-peak energy window identification (20:00 - 08:00)
    """
    plot_map = {p.id if p.id is not None else idx: p for idx, p in enumerate(farm.plots)}
    pump_cap = max(5.0, farm.pump_capacity)

    current_clock = start_hour
    schedule_items: List[ScheduleItem] = []

    for alloc_item in optimization_result.allocations:
        plot_key = alloc_item.plot_id
        plot = plot_map.get(plot_key)

        # Fallback if plot_id was index
        if plot is None:
            for idx, p in enumerate(farm.plots):
                if p.name == alloc_item.plot_name:
                    plot = p
                    break

        allocated_vol = alloc_item.allocated_water

        if allocated_vol <= 0.01:
            alloc_item.scheduled_start_hour = round(current_clock % 24.0, 2)
            alloc_item.scheduled_duration_hours = 0.0
            alloc_item.scheduled_flow_rate = 0.0
            continue

        # Infiltration limit: mm/hr * ha * 10 = m3/hr
        inf_rate = plot.infiltration_rate if plot else 15.0
        area_ha = plot.size_hectares if plot else 1.0
        max_soil_flow = max(2.0, inf_rate * area_ha * 10.0)

        # Operating flow rate
        flow_rate = min(pump_cap, max_soil_flow)
        duration_hours = max(0.1, allocated_vol / flow_rate)

        start_time_str = format_hour_to_time_str(current_clock)
        end_clock = current_clock + duration_hours
        end_time_str = format_hour_to_time_str(end_clock)

        # Off peak vs peak check
        mid_clock = (current_clock + (duration_hours / 2.0)) % 24.0
        is_off_peak = (mid_clock >= 20.0) or (mid_clock < 8.0)
        tariff = "Off-Peak (Discounted)" if is_off_peak else "Peak (Standard)"

        energy_unit = farm.energy_rate * (0.85 if is_off_peak else 1.0)
        energy_cost = round(allocated_vol * energy_unit, 2)
        labor_cost = round(duration_hours * farm.labor_rate, 2)

        # Update allocation item metadata
        alloc_item.scheduled_start_hour = round(current_clock % 24.0, 2)
        alloc_item.scheduled_duration_hours = round(duration_hours, 2)
        alloc_item.scheduled_flow_rate = round(flow_rate, 2)

        schedule_items.append(
            ScheduleItem(
                plot_id=alloc_item.plot_id,
                plot_name=alloc_item.plot_name,
                crop_type=alloc_item.crop_type,
                start_time_str=start_time_str,
                end_time_str=end_time_str,
                duration_hours=round(duration_hours, 2),
                water_volume_m3=round(allocated_vol, 2),
                flow_rate_m3h=round(flow_rate, 2),
                tariff_period=tariff,
                energy_cost=energy_cost,
                labor_cost=labor_cost,
            )
        )

        current_clock = end_clock

    optimization_result.schedule = schedule_items
    return optimization_result
