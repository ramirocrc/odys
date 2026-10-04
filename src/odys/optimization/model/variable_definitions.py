"""Variable definitions for energy system optimization models.

This module defines variable names and types used in energy system
optimization models.
"""

from enum import Enum, unique

from pydantic import BaseModel, ConfigDict

from odys.parameters.dimensions import ModelDimension


class BoundType(Enum):
    """Lower bound type for optimization variables."""

    NON_NEGATIVE = "non_negative"
    UNBOUNDED = "unbounded"


class VariableDefinition(BaseModel):
    """Specification for an optimization variable (name, type, dimensions, bounds)."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
    )

    name: str
    is_binary: bool
    dimensions: list[ModelDimension] | None
    lower_bound_type: BoundType


@unique
class VariableDefinitionRegistry(Enum):
    """All decision variables in the energy system optimization model."""

    VALUE_AT_RISK = VariableDefinition(
        name="cvar_value_at_risk",
        is_binary=False,
        dimensions=None,
        lower_bound_type=BoundType.UNBOUNDED,
    )
    SHORTFALL_REVENUE = VariableDefinition(
        name="cvar_shortfall",
        is_binary=False,
        dimensions=[ModelDimension.Scenarios],
        lower_bound_type=BoundType.NON_NEGATIVE,
    )

    @property
    def var_name(self) -> str:
        """Return the variable name used in the linopy model."""
        return self.value.name

    @property
    def dimensions(self) -> list[ModelDimension] | None:
        """Return the dimensions this variable is defined over."""
        return self.value.dimensions

    @property
    def lower_bound_type(self) -> BoundType:
        """Return the lower bound type for this variable."""
        return self.value.lower_bound_type

    @property
    def is_binary(self) -> bool:
        """Return whether this variable is binary."""
        return self.value.is_binary


CVAR_VARIABLES = [VariableDefinitionRegistry.VALUE_AT_RISK, VariableDefinitionRegistry.SHORTFALL_REVENUE]
