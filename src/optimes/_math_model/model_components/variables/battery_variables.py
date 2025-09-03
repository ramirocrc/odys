from abc import ABC
from typing import ClassVar

import numpy as np

from optimes._math_model.model_components.sets import EnergyModelDimension
from optimes._math_model.model_components.variable_names import EnergyModelVariableName
from optimes._math_model.model_components.variables.base_variable import SystemVariable


class BatteryVariable(SystemVariable, ABC):
    asset_dimension: ClassVar[EnergyModelDimension] = EnergyModelDimension.Batteries


class BatteryPowerInVariable(BatteryVariable):
    name: ClassVar[EnergyModelVariableName] = EnergyModelVariableName.BATTERY_POWER_IN
    binary: ClassVar[bool] = False

    @property
    def lower(self) -> np.ndarray:
        return self._create_zero_bounds()


class BatteryPowerNetVariable(BatteryVariable):
    name: ClassVar[EnergyModelVariableName] = EnergyModelVariableName.BATTERY_POWER_NET
    binary: ClassVar[bool] = False

    @property
    def lower(self) -> np.ndarray:
        return self._create_infinite_lower_bound()


class BatteryPowerOutVariable(BatteryVariable):
    name: ClassVar[EnergyModelVariableName] = EnergyModelVariableName.BATTERY_POWER_OUT
    binary: ClassVar[bool] = False

    @property
    def lower(self) -> np.ndarray:
        return self._create_zero_bounds()


class BatterySocVariable(BatteryVariable):
    name: ClassVar[EnergyModelVariableName] = EnergyModelVariableName.BATTERY_SOC
    binary: ClassVar[bool] = False

    @property
    def lower(self) -> np.ndarray:
        return self._create_zero_bounds()


class BatteryChargeModeVariable(BatteryVariable):
    name: ClassVar[EnergyModelVariableName] = EnergyModelVariableName.BATTERY_CHARGE_MODE
    binary: ClassVar[bool] = True

    @property
    def lower(self) -> float:
        return -np.inf
