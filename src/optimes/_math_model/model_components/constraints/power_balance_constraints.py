import linopy
import xarray as xr

from optimes._math_model.model_components.constraints.model_constraint import ModelConstraint
from optimes._math_model.model_components.sets import EnergyModelDimension


def get_power_balance_constraint(
    var_generator_power: linopy.Variable,
    var_battery_discharge: linopy.Variable,
    var_battery_charge: linopy.Variable,
    param_demand_profile: xr.DataArray,
) -> ModelConstraint:
    """Linopy power balance constraint ensuring supply equals demand.

    This constraint ensures that at each time period, the total power
    generation plus battery discharge equals the demand plus battery charging.
    """
    generation_total = var_generator_power.sum(EnergyModelDimension.Generators.value)
    discharge_total = var_battery_discharge.sum(EnergyModelDimension.Batteries.value)
    charge_total = var_battery_charge.sum(EnergyModelDimension.Batteries.value)

    expression = generation_total + discharge_total - charge_total - param_demand_profile == 0
    return ModelConstraint(
        name="power_balance_constraint",
        constraint=expression,
    )
