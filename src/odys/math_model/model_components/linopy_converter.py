"""Utilities for converting model variables into linopy-compatible parameters."""

from collections.abc import Mapping, Sequence

import numpy as np
from pydantic import BaseModel, ConfigDict

from odys.math_model.model_components.sets import (
    ModelIndex,
)
from odys.math_model.model_components.variables import BoundType


class LinopyVariableParameters(BaseModel):
    """Parameters needed to add a variable to a linopy model."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str
    coords: Mapping[str, list[str]]
    dims: Sequence[str]
    lower: np.ndarray | float
    binary: bool


def get_variable_lower_bound(
    indeces: list[ModelIndex],
    lower_bound_type: BoundType,
    *,
    is_binary: bool,
) -> np.ndarray | float:
    """Calculate lower bounds for a variable.

    Args:
        indeces: List of dimension sets for the variable
        lower_bound_type: Type of lower bound
        is_binary: Whether the variable is binary

    Returns:
        Lower bound value or array
    """
    if is_binary:
        return -np.inf  # Required by linopy.add_variable when variable is binary

    shape = tuple(len(dim_set.values) for dim_set in indeces)

    if lower_bound_type == BoundType.UNBOUNDED:
        return np.full(shape, -np.inf, dtype=float)
    return np.full(shape, 0, dtype=float)
