from abc import ABC

import numpy as np

from optimes._math_model.model_components.sets import EnergyModelDimension
from optimes._math_model.model_components.variable_names import EnergyModelVariableName
from optimes._math_model.model_components.variables.base_variable import SystemVariable


class BatteryVariable(SystemVariable, ABC):
    asset_dimension = EnergyModelDimension.Batteries


class BatteryPowerInVariable(BatteryVariable):
    name = EnergyModelVariableName.BATTERY_POWER_IN
    binary = False

    @property
    def lower(self) -> np.ndarray:
        return self._create_zero_bounds()


class BatteryPowerNetVariable(BatteryVariable):
    name = EnergyModelVariableName.BATTERY_POWER_NET
    binary = False

    @property
    def lower(self) -> np.ndarray:
        return self._create_infinite_lower_bound()


class BatteryPowerOutVariable(BatteryVariable):
    name = EnergyModelVariableName.BATTERY_POWER_OUT
    binary = False

    @property
    def lower(self) -> np.ndarray:
        return self._create_zero_bounds()


class BatterySocVariable(BatteryVariable):
    name = EnergyModelVariableName.BATTERY_SOC
    binary = False

    @property
    def lower(self) -> np.ndarray:
        return self._create_zero_bounds()


class BatteryChargeModeVariable(BatteryVariable):
    name = EnergyModelVariableName.BATTERY_CHARGE_MODE
    binary = True

    @property
    def lower(self) -> float:
        return -np.inf
