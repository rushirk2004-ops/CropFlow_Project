"""Optimization result, allocation items, and strategy comparison data models."""

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class AllocationItem:
    """Individual plot allocation result."""

    plot_id: Optional[int]
    plot_name: str
    crop_type: str
    demand: float
    allocated_water: float
    unmet_demand: float
    coverage_pct: float
    yield_preservation_pct: float
    preserved_value: float
    cost: float
    urgency_score: float = 0.0
    scheduled_start_hour: float = 0.0
    scheduled_duration_hours: float = 0.0
    scheduled_flow_rate: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert allocation item to dictionary."""
        return asdict(self)


@dataclass
class ScheduleItem:
    """Actionable irrigation schedule entry for farm operations."""

    plot_id: Optional[int]
    plot_name: str
    crop_type: str
    start_time_str: str
    end_time_str: str
    duration_hours: float
    water_volume_m3: float
    flow_rate_m3h: float
    tariff_period: str
    energy_cost: float
    labor_cost: float

    def to_dict(self) -> Dict[str, Any]:
        """Convert schedule item to dictionary."""
        return asdict(self)


@dataclass
class OptimizationResult:
    """Overall optimization execution result for a single algorithm."""

    algorithm: str
    scenario_name: str
    available_water: float
    total_demand: float
    total_allocated: float
    unmet_demand: float
    water_utilization_pct: float
    total_cost: float
    total_benefit: float
    net_return: float
    execution_time_ms: float
    fairness_index: float
    allocations: List[AllocationItem] = field(default_factory=list)
    schedule: List[ScheduleItem] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert optimization result to dictionary."""
        return {
            "algorithm": self.algorithm,
            "scenario_name": self.scenario_name,
            "available_water": self.available_water,
            "total_demand": self.total_demand,
            "total_allocated": self.total_allocated,
            "unmet_demand": self.unmet_demand,
            "water_utilization_pct": self.water_utilization_pct,
            "total_cost": self.total_cost,
            "total_benefit": self.total_benefit,
            "net_return": self.net_return,
            "execution_time_ms": self.execution_time_ms,
            "fairness_index": self.fairness_index,
            "allocations": [a.to_dict() for a in self.allocations],
            "schedule": [s.to_dict() for s in self.schedule],
        }


@dataclass
class StrategyComparison:
    """Side-by-side comparison among Greedy, Dynamic Programming, and Hybrid strategies."""

    scenario: str
    available_water: float
    total_demand: float
    results: Dict[str, OptimizationResult] = field(default_factory=dict)
    winner_yield: str = "dynamic_programming"
    winner_net_return: str = "hybrid"
    winner_fairness: str = "hybrid"
    insights: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert strategy comparison to dictionary."""
        return {
            "scenario": self.scenario,
            "available_water": self.available_water,
            "total_demand": self.total_demand,
            "results": {k: v.to_dict() for k, v in self.results.items()},
            "winner_yield": self.winner_yield,
            "winner_net_return": self.winner_net_return,
            "winner_fairness": self.winner_fairness,
            "insights": self.insights,
        }
