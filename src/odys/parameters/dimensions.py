"""Dimension names used as axes of parameter arrays and model variables."""

from enum import StrEnum


class ModelDimension(StrEnum):
    """The axes every entity type shares: scenario and time.

    Each entity type's own axis is named by its formulation (`GeneratorFormulation.dimension`).
    """

    Scenarios = "scenario"
    Time = "time"
