"""Utilities for converting model variables into linopy-compatible parameters."""

from collections.abc import Mapping

import numpy as np
from pydantic import BaseModel, ConfigDict

from odys.optimization.model.variable_definitions import BoundType, VariableDefinitionRegistry
from odys.parameters.context import ModelContext


class LinopyVariableParameters(BaseModel):
    """Parameters needed to add a variable to a linopy model."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
    )

    name: str
    coords: Mapping[str, list[str]]
    lower: float
    binary: bool


def get_linopy_variable_parameters(
    definition: VariableDefinitionRegistry,
    context: ModelContext,
) -> LinopyVariableParameters:
    """Build linopy variable parameters from a variable definition.

    Args:
        definition: Definition of the variable (name, dimensions, bounds).
        context: The shared indexing of the problem, with the coordinates of every dimension.

    Returns:
        Parameters ready to be passed to linopy's ``add_variables``.
    """
    coordinates = [context.coordinates_of(dimension) for dimension in definition.dimensions or []]
    coords: dict[str, list[str]] = {}
    for coordinate in coordinates:
        coords |= coordinate.dimension_coordinates_map

    # linopy ignores the lower bound for binary variables
    lower = -np.inf if definition.is_binary or definition.lower_bound_type is BoundType.UNBOUNDED else 0.0

    return LinopyVariableParameters(
        name=definition.var_name,
        coords=coords,
        lower=lower,
        binary=definition.is_binary,
    )
