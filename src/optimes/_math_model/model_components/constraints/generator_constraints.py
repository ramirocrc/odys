from typing import ClassVar

import linopy
import xarray as xr

from optimes._math_model.model_components.constraints.base_constraint import SystemConstraint
from optimes._math_model.model_components.constraints.constraint_names import EnergyModelConstraintName


class GenerationLimitConstraint(SystemConstraint):
    """Generator power limit constraint.

    This constraint ensures that each generator's power output does not
    exceed its nominal power capacity.
    """

    _name: ClassVar = EnergyModelConstraintName.GENERATOR_LIMIT
    var_generator_power: linopy.Variable
    param_generator_nominal_power: xr.DataArray

    @property
    def constraint(self) -> linopy.Constraint:
        return self.var_generator_power <= self.param_generator_nominal_power
