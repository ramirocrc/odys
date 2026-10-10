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
from odys.optimization.formulations.base import FormulationInputs, VariableFormulation, time_shifted
from odys.parameters.context import ModelContext
from odys.parameters.dimensions import ModelDimension
from odys.parameters.entity_arrays import GeneratorArrays
from odys.parameters.vectorize import vectorize
from odys.results.dispatch import GeneratorDispatch

TIME = ModelDimension.Time
GENERATOR = "generator"


class GeneratorVariables(BaseModel):
    """Decision variables of the generators."""

    model_config = ConfigDict(frozen=True, extra="forbid", arbitrary_types_allowed=True)

    power: linopy.Variable
    status: linopy.Variable
    startup: linopy.Variable
    shutdown: linopy.Variable


class GeneratorFormulation(VariableFormulation[GeneratorVariables]):
    """Generators: power limits, available capacity, startup and shutdown, minimum up and down time, ramping."""

    dimension = GENERATOR
    entity_type = Generator
    power_name: ClassVar[str] = "generator_power"
    status_name: ClassVar[str] = "generator_status"
    startup_name: ClassVar[str] = "generator_startup"
    shutdown_name: ClassVar[str] = "generator_shutdown"

    def __init__(self, generators: Sequence[Generator], context: ModelContext) -> None:
        """Initialize with the generators of the system.

        Args:
            generators: The generators, at least one.
            context: The shared indexing of the problem.
        """
        super().__init__(generators, context)
        self.arrays = vectorize(GeneratorArrays, generators, self.coordinates)
        self.available_capacity = context.profiles(
            AvailableCapacityProfile,
            generators,
            self.coordinates,
            default=np.inf,
        )

    @classmethod
    def build(cls, inputs: FormulationInputs) -> Self | None:
        """Return the formulation of the generators, or None if there are none."""
        generators = inputs.of_type(Generator)
        return cls(generators, inputs.context) if generators else None

    def _create_variables(self, model: linopy.Model) -> GeneratorVariables:
        """Add power (MW, non-negative) and the binary status, startup and shutdown indicators."""
        coords = self.context.variable_coords(self.coordinates)
        return GeneratorVariables(
            power=model.add_variables(name=self.power_name, coords=coords, lower=0.0),
            status=model.add_variables(name=self.status_name, coords=coords, binary=True),
            startup=model.add_variables(name=self.startup_name, coords=coords, binary=True),
            shutdown=model.add_variables(name=self.shutdown_name, coords=coords, binary=True),
        )

    @constraint
    def _get_generator_max_power_constraint(self) -> ModelConstraint:
        """Generator power limit constraint.

        This constraint ensures that each generator's power output does not
        exceed its nominal power capacity.
        """
        return ModelConstraint(
            constraint=self.variables.power - self.variables.status * self.arrays.nominal_power <= 0,
            name="generator_max_power_constraint",
        )

    @constraint
    def _get_generator_status_constraint(self) -> ModelConstraint:
        """When on, output is at least a small fraction (1e-5) of nominal power, so `status` = 1 means it produces."""
        epsilon = 1e-5 * self.arrays.nominal_power
        return ModelConstraint(
            constraint=self.variables.power >= self.variables.status * epsilon,
            name="generator_status_constraint",
        )

    @constraint
    def _get_generator_startup_lower_bound_constraint(self) -> ModelConstraint:
        """Startup indicator active when turning generator on."""
        return ModelConstraint(
            constraint=self.variables.startup >= self.variables.status - time_shifted(self.variables.status, 1),
            name="generator_startup_lower_bound_constraint",
        )

    @constraint
    def _get_generator_startup_upper_bound_1_constraint(self) -> ModelConstraint:
        """Startup indicator bounded by current status."""
        return ModelConstraint(
            constraint=self.variables.startup <= self.variables.status,
            name="generator_startup_upper_bound_1_constraint",
        )

    @constraint
    def _get_generator_startup_upper_bound_2_constraint(self) -> ModelConstraint:
        """Startup indicator bounded by previous status."""
        return ModelConstraint(
            constraint=self.variables.startup + time_shifted(self.variables.status, 1) <= 1.0,
            name="generator_startup_upper_bound_2_constraint",
        )

    @constraint
    def _get_generator_shutdown_lower_bound_constraint(self) -> ModelConstraint:
        """Shutdown indicator active when turning generator off."""
        return ModelConstraint(
            constraint=self.variables.shutdown >= time_shifted(self.variables.status, 1) - self.variables.status,
            name="generator_shutdown_lower_bound_constraint",
        )

    @constraint
    def _get_generator_shutdown_upper_bound_1_constraint(self) -> ModelConstraint:
        """Shutdown indicator bounded by previous status."""
        return ModelConstraint(
            constraint=self.variables.shutdown <= time_shifted(self.variables.status, 1),
            name="generator_shutdown_upper_bound_1_constraint",
        )

    @constraint
    def _get_generator_shutdown_upper_bound_2_constraint(self) -> ModelConstraint:
        """Shutdown indicator bounded by current status."""
        return ModelConstraint(
            constraint=self.variables.shutdown + self.variables.status <= 1.0,
            name="generator_shutdown_upper_bound_2_constraint",
        )

    @constraint
    def _get_min_uptime_constraint(self) -> list[ModelConstraint]:
        """Once started, a generator stays on for at least `min_up_time` steps (one constraint per generator)."""
        constraints = []
        for generator in self.coordinates.labels:
            min_up_time = int(self.arrays.min_up_time.sel({GENERATOR: generator}))
            generator_status = self.variables.status.sel({GENERATOR: generator})
            generator_shutdown = self.variables.shutdown.sel({GENERATOR: generator})
            steps_on = generator_status.rolling({TIME: min_up_time}).sum()
            constraint_generator = steps_on >= min_up_time * time_shifted(generator_shutdown, -1)
            constraints.append(
                ModelConstraint(
                    constraint=constraint_generator,
                    name=f"generator_min_uptime_{generator}_constraint",
                ),
            )
        return constraints

    @constraint
    def _get_min_downtime_constraint(self) -> list[ModelConstraint]:
        """Once stopped, a generator stays off for at least `min_down_time` steps (one constraint per generator)."""
        constraints = []
        for generator in self.coordinates.labels:
            min_down_time = int(self.arrays.min_down_time.sel({GENERATOR: generator}))
            generator_status = self.variables.status.sel({GENERATOR: generator})
            generator_startup = self.variables.startup.sel({GENERATOR: generator})
            steps_off = (1 - generator_status).rolling({TIME: min_down_time}).sum()
            constraint_generator = steps_off >= min_down_time * time_shifted(generator_startup, -1)
            constraints.append(
                ModelConstraint(
                    constraint=constraint_generator,
                    name=f"generator_min_downtime_{generator}_constraint",
                ),
            )
        return constraints

    @constraint
    def _get_min_power_constraint(self) -> ModelConstraint:
        """When on, output is at least `min_power`."""
        return ModelConstraint(
            constraint=self.variables.power >= self.arrays.min_power * self.variables.status,
            name="generator_min_power_constraint",
        )

    @constraint
    def _get_max_ramp_up_constraint(self) -> ModelConstraint:
        """Output rises by at most `ramp_up` per step (unlimited, i.e. nominal power, when unset)."""
        max_ramp_up = self.arrays.ramp_up.fillna(self.arrays.nominal_power)
        ramp = (self.variables.power - time_shifted(self.variables.power, 1)).isel({TIME: slice(1, None)})
        return ModelConstraint(
            constraint=ramp.to_constraint("<=", max_ramp_up),
            name="generator_max_ramp_up_constraint",
        )

    @constraint
    def _get_max_ramp_down_constraint(self) -> ModelConstraint:
        """Output falls by at most `ramp_down` per step (unlimited, i.e. nominal power, when unset)."""
        max_ramp_down = self.arrays.ramp_down.fillna(self.arrays.nominal_power)
        ramp = (time_shifted(self.variables.power, 1) - self.variables.power).isel({TIME: slice(1, None)})
        return ModelConstraint(
            constraint=ramp.to_constraint("<=", max_ramp_down),
            name="generator_max_ramp_down_constraint",
        )

    @constraint
    def _get_available_capacity_constraint(self) -> ModelConstraint:
        """Power is capped by the scenario's available capacity profile (unbounded without one)."""
        return ModelConstraint(
            constraint=self.variables.power <= self.available_capacity,
            name="available_capacity_constraint",
        )

    def power_injection(self) -> linopy.LinearExpression:
        """Return the total generator output, per scenario and time."""
        injection: linopy.LinearExpression = self.variables.power.sum(GENERATOR)
        return injection

    def profit(self) -> linopy.LinearExpression:
        """Return minus the generation cost per scenario: variable cost per MWh plus startup and shutdown costs."""
        cost = (
            self.variables.power * self.context.timestep_hours * self.arrays.variable_cost
            + self.variables.startup * self.arrays.startup_cost
            + self.variables.shutdown * self.arrays.shutdown_cost
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
