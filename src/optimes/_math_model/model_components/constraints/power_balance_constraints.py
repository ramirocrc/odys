from typing import ClassVar

import linopy
import xarray as xr

from optimes._math_model.model_components.constraints.base_constraint import SystemConstraint
from optimes._math_model.model_components.constraints.constraint_names import EnergyModelConstraintName


class PowerBalanceConstraint(SystemConstraint):
    """Linopy power balance constraint ensuring supply equals demand.

    This constraint ensures that at each time period, the total power
    generation plus battery discharge equals the demand plus battery charging.
    """

    _name: ClassVar = EnergyModelConstraintName.POWER_BALANCE
    var_generator_power: linopy.Variable
    var_battery_discharge: linopy.Variable
    var_battery_charge: linopy.Variable
    demand_profile: xr.DataArray

    @property
    def constraint(self) -> linopy.Constraint:
        """Get the power balance constraint expression.

        Returns:
            Linopy expression that equals zero when satisfied.
        """
        generation_total = self.var_generator_power.sum("generators")
        discharge_total = self.var_battery_discharge.sum("batteries")
        charge_total = self.var_battery_charge.sum("batteries")

        return generation_total + discharge_total - charge_total - self.demand_profile == 0
