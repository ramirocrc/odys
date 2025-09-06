"""Variable definitions for energy system optimization models.

This module defines variable names and types used in energy system
optimization models.
"""

from enum import Enum, unique

from pydantic import BaseModel

from optimes._math_model.model_components.sets import EnergyModelDimension


class BoundType(Enum):
    NON_NEGATIVE = "non_negative"
    UNBOUNDED = "unbounded"


class VariableSpec(BaseModel):
    name: str
    is_binary: bool
    asset_dimension: EnergyModelDimension
    lower_bound_type: BoundType


@unique
class ModelVariable(Enum):
    GENERATOR_POWER = VariableSpec(
        name="generator_power",
        is_binary=False,
        asset_dimension=EnergyModelDimension.Generators,
        lower_bound_type=BoundType.NON_NEGATIVE,
    )
    GENERATOR_STATUS = VariableSpec(
        name="generator_status",
        is_binary=True,
        asset_dimension=EnergyModelDimension.Generators,
        lower_bound_type=BoundType.UNBOUNDED,
    )
    GENERATOR_STARTUP = VariableSpec(
        name="generator_startup",
        is_binary=True,
        asset_dimension=EnergyModelDimension.Generators,
        lower_bound_type=BoundType.UNBOUNDED,
    )
    BATTERY_POWER_IN = VariableSpec(
        name="battery_power_in",
        is_binary=False,
        asset_dimension=EnergyModelDimension.Batteries,
        lower_bound_type=BoundType.NON_NEGATIVE,
    )
    BATTERY_POWER_NET = VariableSpec(
        name="battery_net_power",
        is_binary=False,
        asset_dimension=EnergyModelDimension.Batteries,
        lower_bound_type=BoundType.UNBOUNDED,
    )
    BATTERY_POWER_OUT = VariableSpec(
        name="battery_power_out",
        is_binary=False,
        asset_dimension=EnergyModelDimension.Batteries,
        lower_bound_type=BoundType.NON_NEGATIVE,
    )
    BATTERY_SOC = VariableSpec(
        name="battery_soc",
        is_binary=False,
        asset_dimension=EnergyModelDimension.Batteries,
        lower_bound_type=BoundType.NON_NEGATIVE,
    )
    BATTERY_CHARGE_MODE = VariableSpec(
        name="battery_charge_mode",
        is_binary=True,
        asset_dimension=EnergyModelDimension.Batteries,
        lower_bound_type=BoundType.UNBOUNDED,
    )

    @property
    def var_name(self) -> str:
        return self.value.name

    @property
    def asset_dimension(self) -> EnergyModelDimension:
        return self.value.asset_dimension

    @property
    def lower_bound_type(self) -> BoundType:
        return self.value.lower_bound_type

    @property
    def is_binary(self) -> bool:
        return self.value.is_binary

    @classmethod
    def generator_variables(cls) -> list["ModelVariable"]:
        return [var for var in ModelVariable if var.asset_dimension == EnergyModelDimension.Generators]

    @classmethod
    def battery_variables(cls) -> list["ModelVariable"]:
        return [var for var in ModelVariable if var.asset_dimension == EnergyModelDimension.Batteries]
