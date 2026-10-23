"""Model formulation of generators."""

from collections.abc import Sequence
from typing import ClassVar, Self

import linopy
import numpy as np
import xarray as xr
from pydantic import BaseModel, ConfigDict

from odys.domain.entities.generator import Generator
from odys.domain.profiles import AvailableCapacityProfile
from odys.optimization.constraints.constraints_group import constraint
from odys.optimization.constraints.model_constraint import ModelConstraint
from odys.optimization.formulations.base import Formulation, FormulationInputs, time_shifted
from odys.optimization.formulations.commitment import CommitmentFormulation, CommitmentVariables
from odys.parameters.context import ModelContext
from odys.parameters.dimensions import ModelDimension
from odys.parameters.entity_arrays import CommitmentArrays, GeneratorArrays, generator_state_arrays
from odys.parameters.vectorize import vectorize
from odys.results.dispatch import GeneratorDispatch

TIME = ModelDimension.Time
GENERATOR = "generator"


class GeneratorVariables(BaseModel):
    """Decision variables of the generators."""

    model_config = ConfigDict(frozen=True, extra="forbid", arbitrary_types_allowed=True)

    power: linopy.Variable
    commitment: CommitmentVariables


class GeneratorFormulation(Formulation):
    """Generators: power limits, available capacity, startup and shutdown, minimum up and down time, ramping."""

    dimension = GENERATOR
    entity_type = Generator
    power_name: ClassVar[str] = f"{GENERATOR}_power"
    status_name: ClassVar[str] = f"{GENERATOR}_status"
    startup_name: ClassVar[str] = f"{GENERATOR}_startup"
    shutdown_name: ClassVar[str] = f"{GENERATOR}_shutdown"

    def __init__(self, generators: Sequence[Generator], context: ModelContext, model: linopy.Model) -> None:
        """Initialize with the generators of the system.

        Args:
            generators: The generators, at least one.
            context: The shared indexing of the problem.
            model: The model to add the variables to.
        """
        super().__init__(generators, context)
        self.arrays = vectorize(GeneratorArrays, generators, self.coordinates)
        self.commitment_arrays = vectorize(
            CommitmentArrays,
            [generator.commitment for generator in generators],
            self.coordinates,
        )
        self.states = generator_state_arrays(generators, self.coordinates, context)
        self.commitment = CommitmentFormulation(self.coordinates, self.states.commitment, context)
        self.available_capacity = context.profiles(
            AvailableCapacityProfile,
            generators,
            self.coordinates,
            lambda profile: profile.values,
            default=np.inf,
        )
        self.variables = self._create_variables(model)

    @classmethod
    def build(cls, inputs: FormulationInputs) -> Self | None:
        """Return the formulation of the generators, or None if there are none."""
        generators = inputs.of_type(Generator)
        return cls(generators, inputs.context, inputs.model) if generators else None

    def _create_variables(self, model: linopy.Model) -> GeneratorVariables:
        """Add power (MW, non-negative) and the binary status, startup and shutdown indicators."""
        coords = self.context.variable_coords(self.coordinates)
        return GeneratorVariables(
            power=model.add_variables(name=self.power_name, coords=coords, lower=0.0),
            commitment=self.commitment.create_variables(model),
        )

    @constraint
    def _get_generator_max_power_constraint(self) -> ModelConstraint:
        """Generator power limit constraint.

        This constraint ensures that each generator's power output does not
        exceed its nominal power capacity.
        """
        return ModelConstraint(
            constraint=self.variables.power - self.variables.commitment.status * self.arrays.nominal_power <= 0,
            name="generator_max_power_constraint",
        )

    @constraint
    def _get_generator_status_constraint(self) -> ModelConstraint:
        """When on, output is at least a small fraction (1e-5) of nominal power, so `status` = 1 means it produces."""
        epsilon = 1e-5 * self.arrays.nominal_power
        return ModelConstraint(
            constraint=self.variables.power >= self.variables.commitment.status * epsilon,
            name="generator_status_constraint",
        )

    @constraint
    def _get_generator_startup_lower_bound_constraint(self) -> ModelConstraint:
        """Startup indicator active when turning generator on, from its initial status at t=0."""
        return self.commitment.startup_lower_bound_constraint(self.variables.commitment)

    @constraint
    def _get_generator_startup_upper_bound_1_constraint(self) -> ModelConstraint:
        """Startup indicator bounded by current status."""
        return self.commitment.startup_upper_bound_1_constraint(self.variables.commitment)

    @constraint
    def _get_generator_startup_upper_bound_2_constraint(self) -> ModelConstraint:
        """Startup indicator bounded by previous status."""
        return self.commitment.startup_upper_bound_2_constraint(self.variables.commitment)

    @constraint
    def _get_generator_shutdown_lower_bound_constraint(self) -> ModelConstraint:
        """Shutdown indicator active when turning generator off, from its initial status at t=0."""
        return self.commitment.shutdown_lower_bound_constraint(self.variables.commitment)

    @constraint
    def _get_generator_shutdown_upper_bound_1_constraint(self) -> ModelConstraint:
        """Shutdown indicator bounded by previous status."""
        return self.commitment.shutdown_upper_bound_1_constraint(self.variables.commitment)

    @constraint
    def _get_generator_shutdown_upper_bound_2_constraint(self) -> ModelConstraint:
        """Shutdown indicator bounded by current status."""
        return self.commitment.shutdown_upper_bound_2_constraint(self.variables.commitment)

    @constraint
    def _get_min_uptime_constraint(self) -> list[ModelConstraint]:
        """Once started, a generator stays on for its minimum up time, counting time on before the horizon."""
        return self.commitment.min_uptime_constraints(self.variables.commitment)

    @constraint
    def _get_min_downtime_constraint(self) -> list[ModelConstraint]:
        """Once stopped, a generator stays off for its minimum down time, counting time off before the horizon."""
        return self.commitment.min_downtime_constraints(self.variables.commitment)

    @constraint
    def _get_initial_min_uptime_constraint(self) -> list[ModelConstraint]:
        """A generator on for less than its minimum up time before the horizon does not shut down at t=0."""
        return self.commitment.initial_min_uptime_constraint(self.variables.commitment)

    @constraint
    def _get_initial_min_downtime_constraint(self) -> list[ModelConstraint]:
        """A generator off for less than its minimum down time before the horizon does not start at t=0."""
        return self.commitment.initial_min_downtime_constraint(self.variables.commitment)

    @constraint
    def _get_min_power_constraint(self) -> ModelConstraint:
        """When on, output is at least `min_power`."""
        return ModelConstraint(
            constraint=self.variables.power >= self.arrays.min_power * self.variables.commitment.status,
            name="generator_min_power_constraint",
        )

    @constraint
    def _get_max_ramp_up_constraint(self) -> ModelConstraint:
        """Output rises by at most `ramp_up` per hour times the step length, from the initial power at t=0.

        Unlimited when unset.
        """
        max_ramp_up = (self.arrays.ramp_up * self.context.timestep_hours).fillna(self.arrays.nominal_power)
        ramp = self.variables.power - self._previous_power()
        return ModelConstraint(
            constraint=ramp.to_constraint("<=", max_ramp_up),
            name="generator_max_ramp_up_constraint",
        )

    @constraint
    def _get_max_ramp_down_constraint(self) -> ModelConstraint:
        """Output falls by at most `ramp_down` per hour times the step length, from the initial power at t=0.

        Unlimited when unset.
        """
        max_ramp_down = (self.arrays.ramp_down * self.context.timestep_hours).fillna(self.arrays.nominal_power)
        ramp = self._previous_power() - self.variables.power
        return ModelConstraint(
            constraint=ramp.to_constraint("<=", max_ramp_down),
            name="generator_max_ramp_down_constraint",
        )

    @constraint
    def _get_final_power_constraint(self) -> list[ModelConstraint]:
        """Output at the last step equals the final power, for the generators that have a final state."""
        has_final_power = self.states.final_power.notnull()
        if not has_final_power.any():
            return []
        last_step = {TIME: self.context.time.labels[-1]}
        with_final_power = {GENERATOR: has_final_power}
        expression = self.variables.power.sel(last_step).sel(with_final_power) - self.states.final_power.sel(
            with_final_power,
        )
        return [
            ModelConstraint(
                constraint=expression.to_constraint("=", 0),
                name="generator_final_power_constraint",
            ),
        ]

    @constraint
    def _get_available_capacity_constraint(self) -> ModelConstraint:
        """Power is capped by the scenario's available capacity profile (unbounded without one)."""
        return ModelConstraint(
            constraint=self.variables.power <= self.available_capacity,
            name="available_capacity_constraint",
        )

    def _previous_power(self) -> linopy.LinearExpression:
        """Return the power one step earlier, the initial power at t=0."""
        return time_shifted(self.variables.power, 1, outside_value=self.states.initial_power)

    def power_injection(self) -> linopy.LinearExpression:
        """Return the total generator output, per scenario and time."""
        injection: linopy.LinearExpression = self.variables.power.sum(GENERATOR)
        return injection

    def profit(self) -> linopy.LinearExpression:
        """Return minus the generation cost per scenario: variable cost per MWh plus startup and shutdown costs."""
        cost = self.variables.power * self.context.timestep_hours * self.arrays.variable_cost + self.commitment.costs(
            self.variables.commitment,
            self.commitment_arrays,
        )
        profit: linopy.LinearExpression = -cost.sum([TIME, GENERATOR])
        return profit

    def dispatch(self, solution: xr.Dataset) -> GeneratorDispatch:
        """Return the power, status, startups and shutdowns of the generators."""
        data = xr.Dataset(
            {
                "power": solution[self.power_name],
                "status": solution[self.status_name],
                "startup": solution[self.startup_name],
                "shutdown": solution[self.shutdown_name],
            },
        )
        return GeneratorDispatch(data, GENERATOR)
