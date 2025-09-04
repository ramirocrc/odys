"""Variable definitions for energy system optimization models.

This module defines variable names and types used in energy system
optimization models.
"""

from enum import Enum, unique

import numpy as np
from pydantic import BaseModel

from optimes._math_model.model_components.sets import EnergyModelDimension, EnergyModelSet


class LinopyVariableParameters(BaseModel, arbitrary_types_allowed=True):
    name: str
    coords: dict
    dims: list[str]
    lower: np.ndarray | float
    binary: bool


class VariableLowerBoundType(Enum):
    NON_NEGATIVE = "non_negative"
    UNBOUNDED = "unbounded"


class SystemVariableSpec(BaseModel):
    name: str
    is_binary: bool
    asset_dimension: EnergyModelDimension
    lower_bound_type: VariableLowerBoundType


@unique
class SystemVariable(Enum):
    GENERATOR_POWER = SystemVariableSpec(
        name="generator_power",
        is_binary=False,
        asset_dimension=EnergyModelDimension.Generators,
        lower_bound_type=VariableLowerBoundType.NON_NEGATIVE,
    )
    BATTERY_POWER_IN = SystemVariableSpec(
        name="battery_power_in",
        is_binary=False,
        asset_dimension=EnergyModelDimension.Batteries,
        lower_bound_type=VariableLowerBoundType.NON_NEGATIVE,
    )
    BATTERY_POWER_NET = SystemVariableSpec(
        name="battery_net_power",
        is_binary=False,
        asset_dimension=EnergyModelDimension.Batteries,
        lower_bound_type=VariableLowerBoundType.UNBOUNDED,
    )
    BATTERY_POWER_OUT = SystemVariableSpec(
        name="battery_power_out",
        is_binary=False,
        asset_dimension=EnergyModelDimension.Batteries,
        lower_bound_type=VariableLowerBoundType.NON_NEGATIVE,
    )
    BATTERY_SOC = SystemVariableSpec(
        name="battery_soc",
        is_binary=False,
        asset_dimension=EnergyModelDimension.Batteries,
        lower_bound_type=VariableLowerBoundType.NON_NEGATIVE,
    )
    BATTERY_CHARGE_MODE = SystemVariableSpec(
        name="battery_charge_mode",
        is_binary=True,
        asset_dimension=EnergyModelDimension.Batteries,
        lower_bound_type=VariableLowerBoundType.UNBOUNDED,
    )

    @property
    def var_name(self) -> str:
        return self.value.name

    @property
    def asset_dimension(self) -> EnergyModelDimension:
        return self.value.asset_dimension

    @property
    def lower_bound_type(self) -> VariableLowerBoundType:
        return self.value.lower_bound_type

    @property
    def is_binary(self) -> bool:
        return self.value.is_binary

    @classmethod
    def generator_variables(cls) -> list["SystemVariable"]:
        return [var for var in SystemVariable if var.asset_dimension == EnergyModelDimension.Generators]

    @classmethod
    def battery_variables(cls) -> list["SystemVariable"]:
        return [var for var in SystemVariable if var.asset_dimension == EnergyModelDimension.Batteries]

    @classmethod
    def variables_to_report(cls) -> list["SystemVariable"]:
        return [
            cls.GENERATOR_POWER,
            cls.BATTERY_POWER_NET,
        ]


def get_linopy_variable_parameters(
    variable: SystemVariable,
    time_set: EnergyModelSet,
    asset_set: EnergyModelSet,
) -> LinopyVariableParameters:
    """Create linopy variable parameters for a system variable.

    Args:
        variable: The system variable to create parameters for
        time_set: Time dimension set
        asset_set: Asset dimension set (generators or batteries)

    Returns:
        LinopyVariableParameters for the variable

    Raises:
        ValueError: If dimension constraints are not met
    """
    if time_set.dimension != EnergyModelDimension.Time:
        msg = f"time_set should have time dimension, got {time_set.dimension}"
        raise ValueError(msg)

    if asset_set.dimension != variable.asset_dimension:
        msg = f"asset_set should have dimension {variable.asset_dimension}, got {asset_set.dimension}"
        raise ValueError(msg)

    return LinopyVariableParameters(
        name=variable.var_name,
        coords=time_set.coordinates | asset_set.coordinates,
        dims=[time_set.dimension.value, asset_set.dimension.value],
        lower=_get_variable_lower_bound(
            time_set=time_set,
            asset_set=asset_set,
            lower_bound_type=variable.lower_bound_type,
            is_binary=variable.is_binary,
        ),
        binary=variable.is_binary,
    )


def _get_variable_lower_bound(
    time_set: EnergyModelSet,
    asset_set: EnergyModelSet,
    lower_bound_type: VariableLowerBoundType,
    *,
    is_binary: bool,
) -> np.ndarray | float:
    """Calculate lower bounds for a variable.

    Args:
        time_set: Time dimension set
        asset_set: Asset dimension set
        lower_bound_type: Type of lower bound
        is_binary: Whether the variable is binary

    Returns:
        Lower bound value or array
    """
    if is_binary:
        return -np.inf  # Required by linopy.add_variable when variable is binary

    shape = len(time_set.values), len(asset_set.values)
    if lower_bound_type == VariableLowerBoundType.UNBOUNDED:
        return np.full(shape, -np.inf, dtype=float)
    return np.full(shape, 0, dtype=float)
