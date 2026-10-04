"""Dimension names used as axes of parameter arrays and model variables."""

from enum import StrEnum


class ModelDimension(StrEnum):
    """Dimension names used as axes of parameter arrays and model variables."""

    Scenarios = "scenario"
    Time = "time"
    Generators = "generator"
    StationaryStorages = "stationary_storage"
    FixedLoads = "fixed_load"
    FlexibleLoads = "flexible_load"
    Markets = "market"
    Chargers = "charger"
    EVs = "ev"
