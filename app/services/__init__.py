"""CropFlow services package."""

from .preprocessing import (
    calculate_plot_demand,
    clean_and_validate_plot,
    generate_water_demand_matrix,
    prepare_farm_dataset,
)
from .scheduler import build_irrigation_schedule
from .simulation import compare_strategies, run_drought_simulation

__all__ = [
    "calculate_plot_demand",
    "clean_and_validate_plot",
    "prepare_farm_dataset",
    "generate_water_demand_matrix",
    "build_irrigation_schedule",
    "compare_strategies",
    "run_drought_simulation",
]
