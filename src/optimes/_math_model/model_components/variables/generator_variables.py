from abc import ABC
from typing import ClassVar

import numpy as np

from optimes._math_model.model_components.sets import EnergyModelDimension
from optimes._math_model.model_components.variable_names import EnergyModelVariableName
from optimes._math_model.model_components.variables.base_variable import SystemVariable


class GeneratorVariable(SystemVariable, ABC):
    asset_dimension: ClassVar[EnergyModelDimension] = EnergyModelDimension.Generators


class GeneratorPowerVariable(GeneratorVariable):
    name: ClassVar[EnergyModelVariableName] = EnergyModelVariableName.GENERATOR_POWER
    binary: ClassVar[bool] = False

    @property
    def lower(self) -> np.ndarray:
        return self._create_zero_bounds()
