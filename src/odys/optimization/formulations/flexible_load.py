"""Model formulation of flexible loads."""

from collections.abc import Sequence
from typing import ClassVar, Self

import linopy
import numpy as np
from pydantic import BaseModel, ConfigDict

from odys.domain.entities.flexible_load import FlexibleLoad
from odys.domain.profiles import LoadProfile
from odys.optimization.constraints.constraints_group import constraint
from odys.optimization.constraints.model_constraint import ModelConstraint
from odys.optimization.formulations.base import FormulationInputs, VariableFormulation
from odys.parameters.context import ModelContext
from odys.parameters.dimensions import ModelDimension
from odys.parameters.entity_arrays import FlexibleLoadArrays
from odys.parameters.vectorize import vectorize


class FlexibleLoadVariables(BaseModel):
    """Decision variables of the flexible loads."""

    model_config = ConfigDict(frozen=True, extra="forbid", arbitrary_types_allowed=True)

    load_adjustment: linopy.Variable


class FlexibleLoadFormulation(VariableFormulation[FlexibleLoadVariables]):
    """Flexible loads: a base demand the optimizer can raise or lower within bounds, for a value per MWh."""

    variable_name: ClassVar[str] = "load_adjustment"

    def __init__(self, flexible_loads: Sequence[FlexibleLoad], context: ModelContext) -> None:
        """Initialize with the flexible loads of the system.

        Args:
            flexible_loads: The flexible loads, at least one.
            context: The shared indexing of the problem.
        """
        super().__init__(context)
        self.coordinates = context.coordinates_of(ModelDimension.FlexibleLoads)
        self.arrays = vectorize(FlexibleLoadArrays, flexible_loads, self.coordinates)
        self.base_profiles = context.profiles(LoadProfile, flexible_loads, ModelDimension.FlexibleLoads)

    @classmethod
    def build(cls, inputs: FormulationInputs) -> Self | None:
        """Return the formulation of the flexible loads, or None if there are none."""
        flexible_loads = inputs.of_type(FlexibleLoad)
        return cls(flexible_loads, inputs.context) if flexible_loads else None

    def _create_variables(self, model: linopy.Model) -> FlexibleLoadVariables:
        """Add the load adjustment (MW, positive raises the load) per scenario, time and flexible load."""
        return FlexibleLoadVariables(
            load_adjustment=model.add_variables(
                name=self.variable_name,
                coords=self.context.variable_coords(self.coordinates),
                lower=-np.inf,
            ),
        )

    @constraint
    def _get_adjustment_lower_bound_constraint(self) -> ModelConstraint:
        """The load cannot decrease by more than `max_decrease`."""
        return ModelConstraint(
            constraint=self.variables.load_adjustment >= -self.arrays.max_decrease,
            name="flexible_load_adjustment_lower_bound_constraint",
        )

    @constraint
    def _get_adjustment_upper_bound_constraint(self) -> ModelConstraint:
        """The load cannot increase by more than `max_increase`."""
        return ModelConstraint(
            constraint=self.variables.load_adjustment <= self.arrays.max_increase,
            name="flexible_load_adjustment_upper_bound_constraint",
        )

    def power_injection(self) -> linopy.LinearExpression:
        """Return minus the adjusted demand (base profile plus adjustment), summed over flexible loads."""
        adjustment = self.variables.load_adjustment.sum(ModelDimension.FlexibleLoads)
        injection: linopy.LinearExpression = -adjustment - self.base_profiles.sum(ModelDimension.FlexibleLoads)
        return injection

    def profit(self) -> linopy.LinearExpression:
        """Return the value of the adjusted consumption per scenario, in currency (energy times value per MWh)."""
        value = self.variables.load_adjustment * self.context.timestep_hours * self.arrays.value_of_consumption
        profit: linopy.LinearExpression = value.sum([ModelDimension.Time, ModelDimension.FlexibleLoads])
        return profit
