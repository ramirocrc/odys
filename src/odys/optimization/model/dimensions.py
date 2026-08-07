"""Dimension names used as axes in the optimization model."""

from enum import StrEnum


class ModelDimension(StrEnum):
    """Dimension names used as axes in the optimization model."""

    Scenarios = "scenario"
    Time = "time"
    Generators = "generator"
    StandaloneStorages = "standalone_storage"
    FlexibleLoads = "flexible_load"
    Markets = "market"
    Chargers = "charger"
    EVs = "ev"
