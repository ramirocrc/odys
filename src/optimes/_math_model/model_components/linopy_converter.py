from collections.abc import Mapping, Sequence

import numpy as np
from pydantic import BaseModel

from optimes._math_model.model_components.sets import EnergyModelDimension, ModelSet
from optimes._math_model.model_components.variables import BoundType, ModelVariable


class LinopyVariableParameters(BaseModel, arbitrary_types_allowed=True):
    name: str
    coords: Mapping
    dims: Sequence[str]
    lower: np.ndarray | float
    binary: bool


def get_linopy_variable_parameters(
    variable: ModelVariable,
    scenario_set: ModelSet,
    time_set: ModelSet,
    asset_set: ModelSet,
) -> LinopyVariableParameters:
    """Create linopy variable parameters for a system variable.

    Args:
        variable: The system variable to create parameters for
        scenario_set: Scenario dimension set
        time_set: Time dimension set
        asset_set: Asset dimension set (generators or batteries)

    Returns:
        LinopyVariableParameters for the variable

    Raises:
        ValueError: If dimension constraints are not met
    """
    if time_set.dimension != EnergyModelDimension.Time:
        msg = f"time_set should have time dimension, got {time_set.dimension}"
        raise ValueError(msg)

    if scenario_set.dimension != EnergyModelDimension.Scenarios:
        msg = f"scenario_set should have scenarios dimension, got {scenario_set.dimension}"
        raise ValueError(msg)

    if asset_set.dimension != variable.asset_dimension:
        msg = f"asset_set should have dimension {variable.asset_dimension}, got {asset_set.dimension}"
        raise ValueError(msg)

    return LinopyVariableParameters(
        name=variable.var_name,
        coords=scenario_set.coordinates | time_set.coordinates | asset_set.coordinates,
        dims=[scenario_set.dimension.value, time_set.dimension.value, asset_set.dimension.value],
        lower=_get_variable_lower_bound(
            scenario_set=scenario_set,
            time_set=time_set,
            asset_set=asset_set,
            lower_bound_type=variable.lower_bound_type,
            is_binary=variable.is_binary,
        ),
        binary=variable.is_binary,
    )


def _get_variable_lower_bound(
    scenario_set: ModelSet,
    time_set: ModelSet,
    asset_set: ModelSet,
    lower_bound_type: BoundType,
    *,
    is_binary: bool,
) -> np.ndarray | float:
    """Calculate lower bounds for a variable.

    Args:
        scenario_set: Scenario dimension set
        time_set: Time dimension set
        asset_set: Asset dimension set
        lower_bound_type: Type of lower bound
        is_binary: Whether the variable is binary

    Returns:
        Lower bound value or array
    """
    if is_binary:
        return -np.inf  # Required by linopy.add_variable when variable is binary

    shape = len(scenario_set.values), len(time_set.values), len(asset_set.values)

    if lower_bound_type == BoundType.UNBOUNDED:
        return np.full(shape, -np.inf, dtype=float)
    return np.full(shape, 0, dtype=float)
