from typing import ClassVar

import numpy as np

from optimes._math_model.model_components.variable_names import EnergyModelVariableName
from optimes._math_model.model_components.variables.base_variable import SystemVariable


class BatteryPowerInVariable(SystemVariable):
    _name: ClassVar[EnergyModelVariableName] = EnergyModelVariableName.BATTERY_POWER_IN
    binary: ClassVar[bool] = False

    @property
    def lower(self) -> np.ndarray:
        return self._create_zero_bounds()


class BatteryPowerNetVariable(SystemVariable):
    _name: ClassVar[EnergyModelVariableName] = EnergyModelVariableName.BATTERY_POWER_NET
    binary: ClassVar[bool] = False

    @property
    def lower(self) -> np.ndarray:
        return self._create_infinite_lower_bound()


class BatteryPowerOutVariable(SystemVariable):
    _name: ClassVar[EnergyModelVariableName] = EnergyModelVariableName.BATTERY_POWER_OUT
    binary: ClassVar[bool] = False

    @property
    def lower(self) -> np.ndarray:
        return self._create_zero_bounds()


class BatterySocVariable(SystemVariable):
    _name: ClassVar[EnergyModelVariableName] = EnergyModelVariableName.BATTERY_SOC
    binary: ClassVar[bool] = False

    @property
    def lower(self) -> np.ndarray:
        return self._create_zero_bounds()


class BatteryChargeModeVariable(SystemVariable):
    _name: ClassVar[EnergyModelVariableName] = EnergyModelVariableName.BATTERY_CHARGE_MODE
    binary: ClassVar[bool] = True

    @property
    def lower(self) -> float:
        return -np.inf
