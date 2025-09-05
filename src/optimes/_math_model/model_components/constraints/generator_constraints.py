import linopy
import xarray as xr

from optimes._math_model.model_components.constraints.model_constraint import ModelConstraint


def get_generator_max_power_constraint(
    var_generator_power: linopy.Variable,
    param_generator_nominal_power: xr.DataArray,
) -> ModelConstraint:
    """Generator power limit constraint.

    This constraint ensures that each generator's power output does not
    exceed its nominal power capacity.
    """
    constraint = var_generator_power <= param_generator_nominal_power
    return ModelConstraint(
        constraint=constraint,
        name="generator_max_power_constraint",
    )
