"""Model formulation of flexible loads."""

from collections.abc import Sequence
from typing import ClassVar, Self

import linopy
import xarray as xr
from pydantic import BaseModel, ConfigDict

from odys.domain.entities.flexible_load import FlexibleLoad
from odys.domain.profiles import FlexibleLoadProfile
from odys.optimization.constraints.constraints_group import constraint
from odys.optimization.constraints.model_constraint import ModelConstraint
from odys.optimization.formulations.base import FormulationInputs, VariableFormulation
from odys.parameters.context import ModelContext
from odys.parameters.dimensions import ModelDimension
from odys.parameters.entity_arrays import FlexibleLoadArrays
from odys.parameters.vectorize import vectorize
from odys.results.dispatch import FlexibleLoadDispatch

FLEXIBLE_LOAD = "flexible_load"


class FlexibleLoadVariables(BaseModel):
    """Decision variables of the flexible loads."""

    model_config = ConfigDict(frozen=True, extra="forbid", arbitrary_types_allowed=True)

    consumption: linopy.Variable


class FlexibleLoadFormulation(VariableFormulation[FlexibleLoadVariables]):
    """Flexible loads: demand the optimizer sets within a range at every step, for a value per MWh."""

    dimension = FLEXIBLE_LOAD
    entity_type = FlexibleLoad
    variable_name: ClassVar[str] = "flexible_load_consumption"

    def __init__(self, flexible_loads: Sequence[FlexibleLoad], context: ModelContext) -> None:
        """Initialize with the flexible loads of the system.

        Args:
            flexible_loads: The flexible loads, at least one.
            context: The shared indexing of the problem.
        """
        super().__init__(flexible_loads, context)
        self.arrays = vectorize(FlexibleLoadArrays, flexible_loads, self.coordinates)
        self.lower_bounds = context.profiles(
            FlexibleLoadProfile,
            flexible_loads,
            self.coordinates,
            lambda profile: profile.lower_bound,
        )
        self.upper_bounds = context.profiles(
            FlexibleLoadProfile,
            flexible_loads,
            self.coordinates,
            lambda profile: profile.upper_bound,
        )

    @classmethod
    def build(cls, inputs: FormulationInputs) -> Self | None:
        """Return the formulation of the flexible loads, or None if there are none."""
        flexible_loads = inputs.of_type(FlexibleLoad)
        return cls(flexible_loads, inputs.context) if flexible_loads else None

    def _create_variables(self, model: linopy.Model) -> FlexibleLoadVariables:
        """Add the consumption (MW) per scenario, time and flexible load."""
        return FlexibleLoadVariables(
            consumption=model.add_variables(
                name=self.variable_name,
                coords=self.context.variable_coords(self.coordinates),
                lower=0,
            ),
        )

    @constraint
    def _get_lower_bound_constraint(self) -> ModelConstraint:
        """The load consumes at least the lower bound of its profile."""
        return ModelConstraint(
            constraint=self.variables.consumption >= self.lower_bounds,
            name="flexible_load_lower_bound_constraint",
        )

    @constraint
    def _get_upper_bound_constraint(self) -> ModelConstraint:
        """The load consumes at most the upper bound of its profile."""
        return ModelConstraint(
            constraint=self.variables.consumption <= self.upper_bounds,
            name="flexible_load_upper_bound_constraint",
        )

    def power_injection(self) -> linopy.LinearExpression:
        """Return minus the consumption, summed over flexible loads."""
        injection: linopy.LinearExpression = -self.variables.consumption.sum(FLEXIBLE_LOAD)
        return injection

    def profit(self) -> linopy.LinearExpression:
        """Return the value of the consumption per scenario, in currency (energy times value per MWh)."""
        value = self.variables.consumption * self.context.timestep_hours * self.arrays.value_of_consumption
        profit: linopy.LinearExpression = value.sum([ModelDimension.Time, FLEXIBLE_LOAD])
        return profit

    def dispatch(self, solution: xr.Dataset) -> FlexibleLoadDispatch:
        """Return the consumption of the flexible loads."""
        data = xr.Dataset({"consumption": solution[self.variable_name]})
        return FlexibleLoadDispatch(data, FLEXIBLE_LOAD)
