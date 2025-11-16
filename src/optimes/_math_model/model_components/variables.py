"""Variable definitions for energy system optimization models.

This module defines variable names and types used in energy system
optimization models.
"""

from enum import Enum, unique

from pydantic import BaseModel

from optimes._math_model.model_components.sets import ModelDimension


class BoundType(Enum):
    NON_NEGATIVE = "non_negative"
    UNBOUNDED = "unbounded"


class VariableSpec(BaseModel):
    name: str
    is_binary: bool
    dimensions: list[ModelDimension]
    lower_bound_type: BoundType


@unique
class ModelVariable(Enum):
    GENERATOR_POWER = VariableSpec(
        name="generator_power",
        is_binary=False,
        dimensions=[ModelDimension.Scenarios, ModelDimension.Time, ModelDimension.Generators],
        lower_bound_type=BoundType.NON_NEGATIVE,
    )
    GENERATOR_STATUS = VariableSpec(
        name="generator_status",
        is_binary=True,
        dimensions=[ModelDimension.Scenarios, ModelDimension.Time, ModelDimension.Generators],
        lower_bound_type=BoundType.UNBOUNDED,
    )
    GENERATOR_STARTUP = VariableSpec(
        name="generator_startup",
        is_binary=True,
        dimensions=[ModelDimension.Scenarios, ModelDimension.Time, ModelDimension.Generators],
        lower_bound_type=BoundType.UNBOUNDED,
    )
    GENERATOR_SHUTDOWN = VariableSpec(
        name="generator_shutdown",
        is_binary=True,
        dimensions=[ModelDimension.Scenarios, ModelDimension.Time, ModelDimension.Generators],
        lower_bound_type=BoundType.UNBOUNDED,
    )
    BATTERY_POWER_IN = VariableSpec(
        name="battery_power_in",
        is_binary=False,
        dimensions=[ModelDimension.Scenarios, ModelDimension.Time, ModelDimension.Batteries],
        lower_bound_type=BoundType.NON_NEGATIVE,
    )
    BATTERY_POWER_NET = VariableSpec(
        name="battery_net_power",
        is_binary=False,
        dimensions=[ModelDimension.Scenarios, ModelDimension.Time, ModelDimension.Batteries],
        lower_bound_type=BoundType.UNBOUNDED,
    )
    BATTERY_POWER_OUT = VariableSpec(
        name="battery_power_out",
        is_binary=False,
        dimensions=[ModelDimension.Scenarios, ModelDimension.Time, ModelDimension.Batteries],
        lower_bound_type=BoundType.NON_NEGATIVE,
    )
    BATTERY_SOC = VariableSpec(
        name="battery_soc",
        is_binary=False,
        dimensions=[ModelDimension.Scenarios, ModelDimension.Time, ModelDimension.Batteries],
        lower_bound_type=BoundType.NON_NEGATIVE,
    )
    BATTERY_CHARGE_MODE = VariableSpec(
        name="battery_charge_mode",
        is_binary=True,
        dimensions=[ModelDimension.Scenarios, ModelDimension.Time, ModelDimension.Batteries],
        lower_bound_type=BoundType.UNBOUNDED,
    )
    MARKET_VOLUME_SOLD = VariableSpec(
        name="market_volume_sold",
        is_binary=False,
        dimensions=[ModelDimension.Scenarios, ModelDimension.Time, ModelDimension.Markets],
        lower_bound_type=BoundType.UNBOUNDED,
    )

    @property
    def var_name(self) -> str:
        return self.value.name

    @property
    def dimensions(self) -> list[ModelDimension]:
        return self.value.dimensions

    @property
    def asset_dimension(self) -> ModelDimension | None:
        """Get the asset dimension (Generators or Batteries) if present."""
        for dim in self.value.dimensions:
            if dim in (ModelDimension.Generators, ModelDimension.Batteries):
                return dim
        return None

    @property
    def lower_bound_type(self) -> BoundType:
        return self.value.lower_bound_type

    @property
    def is_binary(self) -> bool:
        return self.value.is_binary


GENERATOR_VARIABLES = [var for var in ModelVariable if ModelDimension.Generators in var.value.dimensions]
BATTERY_VARIABLES = [var for var in ModelVariable if ModelDimension.Batteries in var.value.dimensions]
MARKET_VARIABLES = [var for var in ModelVariable if ModelDimension.Markets in var.value.dimensions]
