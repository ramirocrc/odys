"""Variable definitions for energy system optimization models.

This module defines variable names and types used in energy system
optimization models.
"""

from enum import Enum, unique

import numpy as np
from pydantic import BaseModel

from optimes._math_model.model_components.sets import EnergyModelDimension, EnergyModelSet


@unique
class EnergyModelVariableName(str, Enum):
    """Enumeration of variable names used in the energy model."""

    GENERATOR_POWER = "generator_power"
    BATTERY_SOC = "battery_soc"
    BATTERY_POWER_NET = "battery_net_power"
    BATTERY_POWER_IN = "battery_power_in"
    BATTERY_POWER_OUT = "battery_power_out"
    BATTERY_CHARGE_MODE = "battery_charge_mode"

    def __str__(self) -> str:
        return self.value


class LinopyVariableParameters(BaseModel, arbitrary_types_allowed=True):
    name: str
    coords: dict
    dims: list[str]
    lower: np.ndarray | float
    binary: bool


class VariableLowerBoundType(Enum):
    Zero = 0
    Unbounded = 1


class SystemVariableMetadata(BaseModel):
    name: EnergyModelVariableName
    binary: bool
    asset_dimension: EnergyModelDimension
    bounds: VariableLowerBoundType


class SystemVariable2(Enum):
    GENERATOR_POWER = SystemVariableMetadata(
        name=EnergyModelVariableName.GENERATOR_POWER,
        binary=False,
        asset_dimension=EnergyModelDimension.Generators,
        bounds=VariableLowerBoundType.Zero,
    )
    BATTERY_POWER_IN = SystemVariableMetadata(
        name=EnergyModelVariableName.BATTERY_POWER_IN,
        binary=False,
        asset_dimension=EnergyModelDimension.Batteries,
        bounds=VariableLowerBoundType.Zero,
    )
    BATTERY_POWER_NET = SystemVariableMetadata(
        name=EnergyModelVariableName.BATTERY_POWER_NET,
        binary=False,
        asset_dimension=EnergyModelDimension.Batteries,
        bounds=VariableLowerBoundType.Unbounded,
    )
    BATTERY_POWER_OUT = SystemVariableMetadata(
        name=EnergyModelVariableName.BATTERY_POWER_OUT,
        binary=False,
        asset_dimension=EnergyModelDimension.Batteries,
        bounds=VariableLowerBoundType.Zero,
    )
    BATTERY_SOC = SystemVariableMetadata(
        name=EnergyModelVariableName.BATTERY_SOC,
        binary=False,
        asset_dimension=EnergyModelDimension.Batteries,
        bounds=VariableLowerBoundType.Zero,
    )
    BATTERY_CHARGE_MODE = SystemVariableMetadata(
        name=EnergyModelVariableName.BATTERY_CHARGE_MODE,
        binary=True,
        asset_dimension=EnergyModelDimension.Batteries,
        bounds=VariableLowerBoundType.Unbounded,
    )

    @classmethod
    def generator_variables(cls) -> list["SystemVariable2"]:
        return [var for var in SystemVariable2 if var.value.asset_dimension == EnergyModelDimension.Generators]

    @classmethod
    def battery_variables(cls) -> list["SystemVariable2"]:
        return [var for var in SystemVariable2 if var.value.asset_dimension == EnergyModelDimension.Batteries]

    def get_linopy_variable_parameters(
        self,
        time_set: EnergyModelSet,
        asset_set: EnergyModelSet,
    ) -> LinopyVariableParameters:
        if time_set.dimension != time_set.dimension:
            msg = f"time_set should have time dimension, got {time_set.dimension}"
            raise ValueError(msg)

        if asset_set.dimension != self.value.asset_dimension:
            msg = f"asset_set should have dimension {self.value.asset_dimension}, got {asset_set.dimension}"
            raise ValueError(msg)

        return LinopyVariableParameters(
            name=self.value.name,
            coords=time_set.coordinates | asset_set.coordinates,
            dims=[time_set.dimension.value, asset_set.dimension.value],
            lower=self._get_lower_bound(time_set, asset_set),
            binary=self.value.binary,
        )

    def _get_lower_bound(
        self,
        time_set: EnergyModelSet,
        asset_set: EnergyModelSet,
    ) -> np.ndarray | float:
        if self.value.binary:
            return -np.inf
        shape = len(time_set.values), len(asset_set.values)
        if self.value.bounds == VariableLowerBoundType.Unbounded:
            return self._create_infinite_lower_bound(shape)
        return self._create_zero_bounds(shape)

    @staticmethod
    def _create_zero_bounds(shape: tuple[int, int]) -> np.ndarray:
        """Create a zero bounds matrix."""
        return np.zeros(shape, dtype=float)

    @staticmethod
    def _create_infinite_lower_bound(shape: tuple[int, int]) -> np.ndarray:
        """Create unbounded bounds matrix."""
        return np.full(shape, -np.inf, dtype=float)
