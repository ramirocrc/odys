"""On/off logic shared by every entity type that can be switched on and off (generators, flexible loads)."""

from functools import cached_property

import linopy
import xarray as xr
from pydantic import BaseModel, ConfigDict

from odys.optimization.constraints.model_constraint import ModelConstraint
from odys.optimization.formulations.base import time_shifted
from odys.parameters.context import ModelContext
from odys.parameters.coordinates import Coordinates
from odys.parameters.dimensions import ModelDimension
from odys.parameters.entity_arrays import CommitmentArrays, CommitmentStateArrays

TIME = ModelDimension.Time


class CommitmentVariables(BaseModel):
    """Decision variables of switching on and off: the binary status, startup and shutdown indicators."""

    model_config = ConfigDict(frozen=True, extra="forbid", arbitrary_types_allowed=True)

    status: linopy.Variable
    startup: linopy.Variable
    shutdown: linopy.Variable


class CommitmentFormulation:
    """The on/off model of one entity type that can be switched on and off, composed by that type's formulation.

    It is a reusable part, not a `Formulation`: it holds no variables (the
    composing formulation does, and passes them in). Variable and constraint
    names are prefixed with the dimension name ("generator", "flexible_load").
    The status is 1 when the entity is on; a startup (shutdown) is 1 at the
    step it turns on (off), counted from its initial status at t=0.
    """

    def __init__(self, coordinates: Coordinates, states: CommitmentStateArrays, context: ModelContext) -> None:
        """Initialize the on/off model.

        Args:
            coordinates: The labels of the entities along their dimension, which also names them.
            states: The minimum times in steps and the initial status of the entities.
            context: The shared indexing of the problem.
        """
        self.coordinates = coordinates
        self.states = states
        self.context = context

    @property
    def dimension(self) -> str:
        """Return the dimension the entities are indexed along."""
        return self.coordinates.dimension

    def name(self, what: str) -> str:
        """Return the model name of a variable or constraint of this entity type, such as `generator_status`."""
        return f"{self.dimension}_{what}"

    def create_variables(self, model: linopy.Model) -> CommitmentVariables:
        """Add the binary status, startup and shutdown indicators per scenario, time and entity."""
        coords = self.context.variable_coords(self.coordinates)
        return CommitmentVariables(
            status=model.add_variables(name=self.name("status"), coords=coords, binary=True),
            startup=model.add_variables(name=self.name("startup"), coords=coords, binary=True),
            shutdown=model.add_variables(name=self.name("shutdown"), coords=coords, binary=True),
        )

    def constraints(self, variables: CommitmentVariables) -> list[ModelConstraint]:
        """Return the on/off constraints: starts and stops from the initial status, minimum up and down times."""
        return [
            self._startup_lower_bound_constraint(variables),
            self._startup_upper_bound_1_constraint(variables),
            self._startup_upper_bound_2_constraint(variables),
            self._shutdown_lower_bound_constraint(variables),
            self._shutdown_upper_bound_1_constraint(variables),
            self._shutdown_upper_bound_2_constraint(variables),
            *self._min_uptime_constraints(variables),
            *self._min_downtime_constraints(variables),
            *self._initial_min_uptime_constraint(variables),
            *self._initial_min_downtime_constraint(variables),
        ]

    def _startup_lower_bound_constraint(self, variables: CommitmentVariables) -> ModelConstraint:
        """Startup indicator active when turning on, from the initial status at t=0."""
        return ModelConstraint(
            constraint=variables.startup >= variables.status - self.previous_status(variables),
            name=self.name("startup_lower_bound_constraint"),
        )

    def _startup_upper_bound_1_constraint(self, variables: CommitmentVariables) -> ModelConstraint:
        """Startup indicator bounded by current status."""
        return ModelConstraint(
            constraint=variables.startup <= variables.status,
            name=self.name("startup_upper_bound_1_constraint"),
        )

    def _startup_upper_bound_2_constraint(self, variables: CommitmentVariables) -> ModelConstraint:
        """Startup indicator bounded by previous status."""
        return ModelConstraint(
            constraint=variables.startup + self.previous_status(variables) <= 1.0,
            name=self.name("startup_upper_bound_2_constraint"),
        )

    def _shutdown_lower_bound_constraint(self, variables: CommitmentVariables) -> ModelConstraint:
        """Shutdown indicator active when turning off, from the initial status at t=0."""
        return ModelConstraint(
            constraint=variables.shutdown >= self.previous_status(variables) - variables.status,
            name=self.name("shutdown_lower_bound_constraint"),
        )

    def _shutdown_upper_bound_1_constraint(self, variables: CommitmentVariables) -> ModelConstraint:
        """Shutdown indicator bounded by previous status."""
        return ModelConstraint(
            constraint=variables.shutdown <= self.previous_status(variables),
            name=self.name("shutdown_upper_bound_1_constraint"),
        )

    def _shutdown_upper_bound_2_constraint(self, variables: CommitmentVariables) -> ModelConstraint:
        """Shutdown indicator bounded by current status."""
        return ModelConstraint(
            constraint=variables.shutdown + variables.status <= 1.0,
            name=self.name("shutdown_upper_bound_2_constraint"),
        )

    def _min_uptime_constraints(self, variables: CommitmentVariables) -> list[ModelConstraint]:
        """Once started, an entity stays on for its minimum up time, counting time on before the horizon.

        One constraint per entity: the steps on in each window of `min_up_steps`, plus the steps on before
        the horizon that fall in it, cover the window whenever the entity shuts down after it.
        """
        constraints = []
        for label in self.coordinates.labels:
            selection = {self.dimension: label}
            min_up_steps = int(self.states.min_up_steps.sel(selection))
            steps_on = variables.status.sel(selection).rolling({TIME: min_up_steps}).sum() + self._steps_before_horizon(
                label,
                min_up_steps,
                initially_on=True,
            )
            constraints.append(
                ModelConstraint(
                    constraint=steps_on >= min_up_steps * time_shifted(variables.shutdown.sel(selection), -1),
                    name=self.name(f"min_uptime_{label}_constraint"),
                ),
            )
        return constraints

    def _min_downtime_constraints(self, variables: CommitmentVariables) -> list[ModelConstraint]:
        """Once stopped, an entity stays off for its minimum down time, counting time off before the horizon.

        One constraint per entity: the steps off in each window of `min_down_steps`, plus the steps off before
        the horizon that fall in it, cover the window whenever the entity starts after it.
        """
        constraints = []
        for label in self.coordinates.labels:
            selection = {self.dimension: label}
            min_down_steps = int(self.states.min_down_steps.sel(selection))
            steps_off = (1 - variables.status.sel(selection)).rolling(
                {TIME: min_down_steps},
            ).sum() + self._steps_before_horizon(label, min_down_steps, initially_on=False)
            constraints.append(
                ModelConstraint(
                    constraint=steps_off >= min_down_steps * time_shifted(variables.startup.sel(selection), -1),
                    name=self.name(f"min_downtime_{label}_constraint"),
                ),
            )
        return constraints

    def _initial_min_uptime_constraint(self, variables: CommitmentVariables) -> list[ModelConstraint]:
        """An entity on for less than its minimum up time before the horizon does not shut down at t=0."""
        states = self.states
        still_up = states.initially_on & (states.initial_steps_in_state < states.min_up_steps)
        return self._no_change_at_first_step(variables.shutdown, still_up, self.name("initial_min_uptime"))

    def _initial_min_downtime_constraint(self, variables: CommitmentVariables) -> list[ModelConstraint]:
        """An entity off for less than its minimum down time before the horizon does not start at t=0."""
        states = self.states
        still_down = ~states.initially_on & (states.initial_steps_in_state < states.min_down_steps)
        return self._no_change_at_first_step(variables.startup, still_down, self.name("initial_min_downtime"))

    def previous_status(self, variables: CommitmentVariables) -> linopy.LinearExpression:
        """Return the status one step earlier, the initial status at t=0."""
        return time_shifted(variables.status, 1, outside_value=self.states.initially_on.astype(float))

    def costs(self, variables: CommitmentVariables, arrays: CommitmentArrays) -> linopy.LinearExpression:
        """Return the startup and shutdown cost at each step of each entity, in currency."""
        cost: linopy.LinearExpression = (
            variables.startup * arrays.startup_cost + variables.shutdown * arrays.shutdown_cost
        )
        return cost

    def _steps_before_horizon(self, label: str, window: int, *, initially_on: bool) -> xr.DataArray:
        """Return, at each step, how many steps of the window ending there the entity spent on (or off) before t=0.

        Without a time in state, the entity has been in its initial state for longer than any window.

        Args:
            label: The entity's label.
            window: The window length in steps (the minimum up or down time).
            initially_on: True to count steps on, False to count steps off.
        """
        selection = {self.dimension: label}
        if bool(self.states.initially_on.sel(selection)) != initially_on:
            return xr.zeros_like(self._step_index)
        steps_in_state = float(self.states.initial_steps_in_state.sel(selection))
        steps_of_window_before_horizon = (window - 1 - self._step_index).clip(min=0)
        steps_in_state_in_window: xr.DataArray = steps_of_window_before_horizon.clip(max=steps_in_state)
        return steps_in_state_in_window

    @cached_property
    def _step_index(self) -> xr.DataArray:
        """Return the position of each step along time (0, 1, ...)."""
        time = self.context.time
        return xr.DataArray(range(len(time.labels)), dims=time.dimension, coords=time.dimension_coordinates_map)

    def _no_change_at_first_step(
        self,
        indicator: linopy.Variable,
        selected: xr.DataArray,
        name: str,
    ) -> list[ModelConstraint]:
        """Return a constraint fixing the startup or shutdown indicator at t=0 to 0 for the selected entities."""
        if not selected.any():
            return []
        first_step = {TIME: self.context.time.labels[0]}
        return [
            ModelConstraint(
                constraint=(1 * indicator.sel(first_step).sel({self.dimension: selected})).to_constraint("=", 0),
                name=f"{name}_constraint",
            ),
        ]
