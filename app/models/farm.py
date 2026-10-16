"""Farm and Plot domain models for CropFlow.

Supports manual and simulated farm inputs:
- Plot ID, area, crop type, growth stage
- Required irrigation water in liters
- Current soil moisture % (0-100%)
- Soil type and infiltration rate
- Crop priority (1-5)
- Estimated irrigation cost per liter ($/L)
- Total available water, drought severity, and irrigation time windows.
"""

from typing import Any, Dict, List, Optional


class Plot:
    """Represents an agricultural plot with manually entered or simulated crop and soil properties."""

    def __init__(
        self,
        name: Optional[str] = None,
        area: Optional[float] = None,
        crop_type: str = "Wheat",
        growth_stage: str = "Vegetative",
        soil_type: str = "Loamy",
        current_moisture: float = 30.0,
        target_moisture: float = 75.0,
        water_demand: Optional[float] = None,
        id: Optional[int] = None,
        farm_id: Optional[int] = None,
        wilting_point: float = 15.0,
        infiltration_rate: float = 16.0,
        crop_value_per_ha: float = 1800.0,
        sensitivity_factor: float = 1.0,
        priority: int = 3,
        plot_identifier: Optional[str] = None,
        size_hectares: Optional[float] = None,
        water_required_liters: Optional[float] = None,
        cost_per_liter: float = 0.000045,
        remaining_demand_liters: Optional[float] = None,
        **kwargs: Any,
    ):
        self.id = id
        self.farm_id = farm_id

        # Area handling (area or size_hectares)
        resolved_area = area if area is not None else (size_hectares if size_hectares is not None else 1.0)
        self.area = float(resolved_area)

        # Identifier and Name
        self.plot_identifier = str(plot_identifier or (f"P-{id}" if id else name or "P-101"))
        self.name = str(name or f"Plot {self.plot_identifier}")

        self.crop_type = str(crop_type)
        self.growth_stage = str(growth_stage)
        self.soil_type = str(soil_type)
        self.current_moisture = float(current_moisture)
        self.target_moisture = float(target_moisture)
        self.wilting_point = float(wilting_point)
        self.infiltration_rate = float(infiltration_rate)
        self.priority = int(priority)
        self.cost_per_liter = float(cost_per_liter)
        self.crop_value_per_ha = float(crop_value_per_ha)
        self.sensitivity_factor = float(sensitivity_factor)

        # Water volumes (liters vs m3)
        if remaining_demand_liters is not None:
            self.remaining_demand_liters = float(remaining_demand_liters)
        elif water_demand is not None:
            self.remaining_demand_liters = float(water_demand) * 1000.0
        elif water_required_liters is not None:
            self.remaining_demand_liters = float(water_required_liters)
        else:
            self.remaining_demand_liters = 100000.0

        if water_required_liters is not None:
            self.water_required_liters = float(water_required_liters)
        else:
            self.water_required_liters = self.remaining_demand_liters

    @property
    def size_hectares(self) -> float:
        """Alias for area in hectares."""
        return self.area

    @size_hectares.setter
    def size_hectares(self, val: float) -> None:
        self.area = float(val)

    @property
    def water_demand(self) -> float:
        """Normalized water demand in cubic meters (1 m3 = 1000 Liters)."""
        return round(self.remaining_demand_liters / 1000.0, 3)

    @water_demand.setter
    def water_demand(self, val: float) -> None:
        self.remaining_demand_liters = float(val) * 1000.0

    @property
    def total_potential_value(self) -> float:
        """Total economic value of the plot at maximum yield ($)."""
        return round(self.area * self.crop_value_per_ha, 2)

    @property
    def moisture_stress_index(self) -> float:
        """Normalized soil moisture stress index between 0.0 (no stress) and 1.0 (severe stress)."""
        moisture_range = max(1.0, self.target_moisture - self.wilting_point)
        current_deficit = max(0.0, self.target_moisture - self.current_moisture)
        stress = current_deficit / moisture_range
        return round(min(1.0, max(0.0, stress)), 3)

    @property
    def urgency_score(self) -> float:
        """Urgency score based on economic yield, stage sensitivity Ky, stress index, and priority."""
        stress = self.moisture_stress_index
        ky = max(0.2, self.sensitivity_factor)
        priority_weight = 0.5 + (self.priority * 0.18)
        value_factor = (self.total_potential_value / 1000.0) ** 0.6
        return round(stress * ky * priority_weight * value_factor, 4)

    def calculate_yield_response(self, allocated_water: float) -> float:
        """Calculate preserved yield percentage using FAO-33 water-yield response function.

        Yield/Yield_max = 1 - Ky * (1 - (Allocated / Demand))
        """
        demand_m3 = self.water_demand
        if demand_m3 <= 0:
            return 100.0

        fraction = min(1.0, max(0.0, allocated_water / demand_m3))
        deficit_fraction = 1.0 - fraction
        yield_ratio = 1.0 - (self.sensitivity_factor * deficit_fraction)
        yield_pct = max(0.0, min(1.0, yield_ratio)) * 100.0
        return round(yield_pct, 2)

    def calculate_irrigation_cost(
        self,
        allocated_water: float,
        energy_rate: float = 0.045,
        labor_rate: float = 14.0,
        pump_capacity: float = 25.0,
    ) -> float:
        """Calculate total irrigation cost using cost_per_liter or energy/labor model."""
        if allocated_water <= 0:
            return 0.0

        allocated_liters = allocated_water * 1000.0
        if self.cost_per_liter > 0:
            direct_cost = allocated_liters * self.cost_per_liter
            hours = allocated_water / max(1.0, pump_capacity)
            return round(direct_cost + (hours * labor_rate * 0.25), 2)

        energy_cost = allocated_water * energy_rate
        hours = allocated_water / max(1.0, pump_capacity)
        labor_cost = hours * labor_rate
        return round(energy_cost + labor_cost, 2)

    def to_dict(self) -> Dict[str, Any]:
        """Convert Plot instance to serializable dictionary."""
        return {
            "id": self.id,
            "farm_id": self.farm_id,
            "plot_identifier": self.plot_identifier,
            "name": self.name,
            "area": self.area,
            "size_hectares": self.area,
            "crop_type": self.crop_type,
            "growth_stage": self.growth_stage,
            "water_required_liters": self.water_required_liters,
            "current_moisture": self.current_moisture,
            "target_moisture": self.target_moisture,
            "wilting_point": self.wilting_point,
            "soil_type": self.soil_type,
            "infiltration_rate": self.infiltration_rate,
            "priority": self.priority,
            "cost_per_liter": self.cost_per_liter,
            "remaining_demand_liters": self.remaining_demand_liters,
            "water_demand": self.water_demand,
            "crop_value_per_ha": self.crop_value_per_ha,
            "sensitivity_factor": self.sensitivity_factor,
            "total_potential_value": self.total_potential_value,
            "moisture_stress_index": self.moisture_stress_index,
            "urgency_score": self.urgency_score,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Plot":
        """Build Plot instance from dictionary."""
        plot_id_val = str(data.get("plot_identifier") or data.get("plot_id") or data.get("name") or "P-101")
        area_val = float(data.get("area") if data.get("area") is not None else data.get("size_hectares", 1.0))
        req_liters = float(data.get("water_required_liters") or (float(data.get("water_demand", 100.0)) * 1000.0))
        rem_liters = float(data.get("remaining_demand_liters") or req_liters)

        return cls(
            id=data.get("id"),
            farm_id=data.get("farm_id"),
            plot_identifier=plot_id_val,
            name=str(data.get("name") or f"Plot {plot_id_val}"),
            area=area_val,
            size_hectares=area_val,
            crop_type=str(data.get("crop_type", "Wheat")),
            growth_stage=str(data.get("growth_stage", "Vegetative")),
            water_required_liters=req_liters,
            current_moisture=float(data.get("current_moisture", 30.0)),
            target_moisture=float(data.get("target_moisture", 75.0)),
            wilting_point=float(data.get("wilting_point", 15.0)),
            soil_type=str(data.get("soil_type", "Loamy")),
            infiltration_rate=float(data.get("infiltration_rate", 16.0)),
            priority=int(data.get("priority", 3)),
            cost_per_liter=float(data.get("cost_per_liter", 0.000045)),
            remaining_demand_liters=rem_liters,
            water_demand=round(rem_liters / 1000.0, 3),
            crop_value_per_ha=float(data.get("crop_value_per_ha", 1800.0)),
            sensitivity_factor=float(data.get("sensitivity_factor", 1.0)),
        )


class Farm:
    """Represents a farm with budget, drought severity, and irrigation time windows."""

    def __init__(
        self,
        name: str = "Farm",
        water_budget: Optional[float] = None,
        id: Optional[int] = None,
        location: str = "Central Basin",
        total_area: float = 0.0,
        reservoir_capacity: float = 0.0,
        energy_rate: float = 0.045,
        labor_rate: float = 14.0,
        pump_capacity: float = 25.0,
        plots: Optional[List[Plot]] = None,
        total_available_water_liters: Optional[float] = None,
        drought_severity: str = "Moderate",
        drought_factor: float = 0.50,
        window_start: str = "20:00",
        window_end: str = "06:00",
        window_duration_hours: float = 10.0,
        **kwargs: Any,
    ):
        self.id = id
        self.name = str(name)
        self.location = str(location)
        self.plots = plots or []

        # Liters vs m3
        if total_available_water_liters is not None:
            self.total_available_water_liters = float(total_available_water_liters)
        elif water_budget is not None:
            self.total_available_water_liters = float(water_budget) * 1000.0
        else:
            self.total_available_water_liters = 500000.0

        self.drought_severity = str(drought_severity)
        self.drought_factor = float(drought_factor)
        self.window_start = str(window_start)
        self.window_end = str(window_end)
        self.window_duration_hours = float(window_duration_hours)
        self.total_area = float(total_area or sum(p.area for p in self.plots))
        self.reservoir_capacity = float(reservoir_capacity or (self.total_available_water_liters * 1.5))
        self.energy_rate = float(energy_rate)
        self.labor_rate = float(labor_rate)
        self.pump_capacity = float(pump_capacity)

    @property
    def water_budget(self) -> float:
        """Water budget in cubic meters (m3)."""
        return round(self.total_available_water_liters / 1000.0, 2)

    @water_budget.setter
    def water_budget(self, val: float) -> None:
        self.total_available_water_liters = float(val) * 1000.0

    @property
    def total_demand_liters(self) -> float:
        """Sum of remaining water demands in liters."""
        return round(sum(p.remaining_demand_liters for p in self.plots), 2)

    @property
    def total_demand(self) -> float:
        """Sum of water demands in m3."""
        return round(self.total_demand_liters / 1000.0, 2)

    @property
    def water_balance_liters(self) -> float:
        """Water surplus (+) or deficit (-) in liters."""
        return round(self.total_available_water_liters - self.total_demand_liters, 2)

    @property
    def water_balance(self) -> float:
        """Water surplus (+) or deficit (-) in m3."""
        return round(self.water_budget - self.total_demand, 2)

    @property
    def total_farm_value(self) -> float:
        """Sum of potential crop values across all plots."""
        return round(sum(p.total_potential_value for p in self.plots), 2)

    def to_dict(self) -> Dict[str, Any]:
        """Convert Farm instance to serializable dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "location": self.location,
            "total_area": self.total_area,
            "total_available_water_liters": self.total_available_water_liters,
            "water_budget": self.water_budget,
            "drought_severity": self.drought_severity,
            "drought_factor": self.drought_factor,
            "window_start": self.window_start,
            "window_end": self.window_end,
            "window_duration_hours": self.window_duration_hours,
            "reservoir_capacity": self.reservoir_capacity,
            "energy_rate": self.energy_rate,
            "labor_rate": self.labor_rate,
            "pump_capacity": self.pump_capacity,
            "total_demand_liters": self.total_demand_liters,
            "total_demand": self.total_demand,
            "water_balance_liters": self.water_balance_liters,
            "water_balance": self.water_balance,
            "total_farm_value": self.total_farm_value,
            "plots": [p.to_dict() for p in self.plots],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Farm":
        """Build Farm instance from dictionary."""
        plots_data = data.get("plots", [])
        plots = [
            Plot.from_dict(p) if isinstance(p, dict) else p for p in plots_data
        ]
        water_liters = float(data.get("total_available_water_liters") or (float(data.get("water_budget", 500.0)) * 1000.0))

        return cls(
            id=data.get("id"),
            name=str(data.get("name", "Farm")),
            total_available_water_liters=water_liters,
            water_budget=round(water_liters / 1000.0, 2),
            location=str(data.get("location", "Central Basin")),
            drought_severity=str(data.get("drought_severity", "Moderate")),
            drought_factor=float(data.get("drought_factor", 0.50)),
            window_start=str(data.get("window_start", "20:00")),
            window_end=str(data.get("window_end", "06:00")),
            window_duration_hours=float(data.get("window_duration_hours", 10.0)),
            total_area=float(data.get("total_area", sum(p.area for p in plots))),
            reservoir_capacity=float(data.get("reservoir_capacity", water_liters * 1.5)),
            energy_rate=float(data.get("energy_rate", 0.045)),
            labor_rate=float(data.get("labor_rate", 14.0)),
            pump_capacity=float(data.get("pump_capacity", 25.0)),
            plots=plots,
        )
