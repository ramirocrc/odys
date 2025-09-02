from typing import ClassVar

import numpy as np

from optimes._math_model.model_components.variable_names import EnergyModelVariableName
from optimes._math_model.model_components.variables.base_variable import SystemVariable


class GeneratorPowerVariable(SystemVariable):
    _name: ClassVar[EnergyModelVariableName] = EnergyModelVariableName.GENERATOR_POWER
    binary: ClassVar[bool] = False

    @property
    def lower(self) -> np.ndarray:
        return self._create_zero_bounds()
