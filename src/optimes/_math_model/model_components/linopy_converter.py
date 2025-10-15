from collections.abc import Mapping, Sequence

import numpy as np
from pydantic import BaseModel

from optimes._math_model.model_components.sets import (
    BatteryIndex,
    GeneratorIndex,
    ModelIndex,
    ScenarioIndex,
    TimeIndex,
)
from optimes._math_model.model_components.variables import BoundType, ModelVariable


class LinopyVariableParameters(BaseModel, arbitrary_types_allowed=True):
    name: str
    coords: Mapping
    dims: Sequence[str]
    lower: np.ndarray | float
    binary: bool


def get_linopy_variable_parameters(
    variable: ModelVariable,
    scenario_index: ScenarioIndex,
    time_index: TimeIndex,
    generator_index: GeneratorIndex | None = None,
    battery_index: BatteryIndex | None = None,
) -> LinopyVariableParameters:
    """Create linopy variable parameters for a system variable.

    Args:
        variable: The system variable to create parameters for
        scenario_index: Scenario dimension set
        time_index: Time dimension set
        generator_index: Generator dimension set (required if variable has generator dimension)
        battery_index: Battery dimension set (required if variable has battery dimension)

    Returns:
        LinopyVariableParameters for the variable

    Raises:
        ValueError: If dimension constraints are not met
    """
    coords = scenario_index.coordinates | time_index.coordinates
    dims = [scenario_index.dimension, time_index.dimension]
    dimension_sets = [scenario_index, time_index]

    if generator_index:
        coords |= generator_index.coordinates
        dims.append(generator_index.dimension)
        dimension_sets.append(generator_index)

    if battery_index:
        coords |= battery_index.coordinates
        dims.append(battery_index.dimension)
        dimension_sets.append(battery_index)

    return LinopyVariableParameters(
        name=variable.var_name,
        coords=coords,
        dims=dims,
        lower=_get_variable_lower_bound(
            dimension_sets=dimension_sets,
            lower_bound_type=variable.lower_bound_type,
            is_binary=variable.is_binary,
        ),
        binary=variable.is_binary,
    )


def _get_variable_lower_bound(
    dimension_sets: list[ModelIndex],
    lower_bound_type: BoundType,
    *,
    is_binary: bool,
) -> np.ndarray | float:
    """Calculate lower bounds for a variable.

    Args:
        dimension_sets: List of dimension sets for the variable
        lower_bound_type: Type of lower bound
        is_binary: Whether the variable is binary

    Returns:
        Lower bound value or array
    """
    if is_binary:
        return -np.inf  # Required by linopy.add_variable when variable is binary

    shape = tuple(len(dim_set.values) for dim_set in dimension_sets)

    if lower_bound_type == BoundType.UNBOUNDED:
        return np.full(shape, -np.inf, dtype=float)
    return np.full(shape, 0, dtype=float)
