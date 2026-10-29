"""Model formulation of flexible loads."""

from collections.abc import Sequence
from typing import ClassVar, Self

import linopy
import xarray as xr
from pydantic import BaseModel, ConfigDict

from odys.domain.entities.commitment import Commitment
from odys.domain.entities.flexible_load import FlexibleLoad
from odys.domain.profiles import FlexibleLoadProfile
from odys.optimization.constraints.model_constraint import ModelConstraint
from odys.optimization.formulations.base import Formulation, FormulationInputs, time_shifted
from odys.optimization.formulations.commitment import CommitmentFormulation, CommitmentVariables
from odys.parameters.context import ModelContext
from odys.parameters.dimensions import ModelDimension
from odys.parameters.entity_arrays import CommitmentArrays, FlexibleLoadArrays, flexible_load_state_arrays
from odys.parameters.vectorize import vectorize
from odys.results.dispatch import FlexibleLoadDispatch

TIME = ModelDimension.Time
FLEXIBLE_LOAD = "flexible_load"


class FlexibleLoadVariables(BaseModel):
    """Decision variables of the flexible loads: the consumption, and the on/off indicators when one can switch."""

    model_config = ConfigDict(frozen=True, extra="forbid", arbitrary_types_allowed=True)

    consumption: linopy.Variable
    commitment: CommitmentVariables | None


class FlexibleLoadFormulation(Formulation):
    """Flexible loads: demand the optimizer sets within a range at every step, for a value per MWh.

    A load can also ramp only so fast between two running steps, and, with a commitment, be switched off. The
    on/off indicators exist only when some flexible load has a commitment, so a model without one stays linear;
    the loads without a commitment then stay on.
    """

    dimension = FLEXIBLE_LOAD
    entity_type = FlexibleLoad
    variable_name: ClassVar[str] = f"{FLEXIBLE_LOAD}_consumption"
    status_name: ClassVar[str] = f"{FLEXIBLE_LOAD}_status"
    startup_name: ClassVar[str] = f"{FLEXIBLE_LOAD}_startup"
    shutdown_name: ClassVar[str] = f"{FLEXIBLE_LOAD}_shutdown"

    def __init__(self, flexible_loads: Sequence[FlexibleLoad], context: ModelContext, model: linopy.Model) -> None:
        """Initialize with the flexible loads of the system.

        Args:
            flexible_loads: The flexible loads, at least one.
            context: The shared indexing of the problem.
            model: The model to add the variables to.
        """
        super().__init__(flexible_loads, context)
        self.arrays = vectorize(FlexibleLoadArrays, flexible_loads, self.coordinates)
        self.commitment_arrays = vectorize(
            CommitmentArrays,
            [load.commitment or Commitment() for load in flexible_loads],
            self.coordinates,
        )
        self.states = flexible_load_state_arrays(flexible_loads, self.coordinates, context)
        self.commitment = CommitmentFormulation(self.coordinates, self.states.commitment, context)
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
        self.variables = self._create_variables(model)

    @classmethod
    def build(cls, inputs: FormulationInputs) -> Self | None:
        """Return the formulation of the flexible loads, or None if there are none."""
        flexible_loads = inputs.of_type(FlexibleLoad)
        return cls(flexible_loads, inputs.context, inputs.model) if flexible_loads else None

    def _create_variables(self, model: linopy.Model) -> FlexibleLoadVariables:
        """Add the consumption (MW), and the on/off indicators when some flexible load has a commitment."""
        return FlexibleLoadVariables(
            consumption=model.add_variables(
                name=self.variable_name,
                coords=self.context.variable_coords(self.coordinates),
                lower=0,
            ),
            commitment=self.commitment.create_variables(model) if self._has_commitment else None,
        )

    def constraints(self) -> list[ModelConstraint]:
        """Return the flexible load constraints: consumption bounds, on/off logic and ramps."""
        return [
            self._get_lower_bound_constraint(),
            self._get_upper_bound_constraint(),
            *self._get_always_on_constraint(),
            *self._get_commitment_constraints(),
            *self._get_max_ramp_up_constraint(),
            *self._get_max_ramp_down_constraint(),
        ]

    def _get_lower_bound_constraint(self) -> ModelConstraint:
        """The load consumes at least the lower bound of its profile while it runs."""
        commitment = self.variables.commitment
        lower_bound = self.lower_bounds if commitment is None else commitment.status * self.lower_bounds
        return ModelConstraint(
            constraint=self.variables.consumption >= lower_bound,
            name="flexible_load_lower_bound_constraint",
        )

    def _get_upper_bound_constraint(self) -> ModelConstraint:
        """The load consumes at most the upper bound of its profile while it runs, and nothing while it is off."""
        commitment = self.variables.commitment
        upper_bound = self.upper_bounds if commitment is None else commitment.status * self.upper_bounds
        return ModelConstraint(
            constraint=self.variables.consumption <= upper_bound,
            name="flexible_load_upper_bound_constraint",
        )

    def _get_always_on_constraint(self) -> list[ModelConstraint]:
        """A load without a commitment is always on, when others have on/off indicators."""
        commitment = self.variables.commitment
        always_on = ~self.states.is_switchable
        if commitment is None or not always_on.any():
            return []
        status = 1 * commitment.status.sel({FLEXIBLE_LOAD: always_on})
        return [ModelConstraint(constraint=status.to_constraint("=", 1), name="flexible_load_always_on_constraint")]

    def _get_commitment_constraints(self) -> list[ModelConstraint]:
        """Starts and stops are counted from the initial status, and the minimum up and down times hold."""
        commitment = self.variables.commitment
        return [] if commitment is None else self.commitment.constraints(commitment)

    def _get_max_ramp_up_constraint(self) -> list[ModelConstraint]:
        """Between two running steps, consumption rises by at most `ramp_up` per hour; a start lands anywhere."""
        has_ramp = self.arrays.ramp_up.notnull()
        if not has_ramp.any():
            return []
        increase = self.variables.consumption - self._previous_consumption()
        commitment = self.variables.commitment
        if commitment is not None:
            increase -= commitment.startup * self.upper_bounds
        with_ramp = {FLEXIBLE_LOAD: has_ramp}
        max_increase = (self.arrays.ramp_up * self.context.timestep_hours).sel(with_ramp)
        return [
            ModelConstraint(
                constraint=increase.sel(with_ramp).to_constraint("<=", max_increase),
                name="flexible_load_max_ramp_up_constraint",
            ),
        ]

    def _get_max_ramp_down_constraint(self) -> list[ModelConstraint]:
        """Between two running steps, consumption falls by at most `ramp_down` per hour; a stop drops to 0."""
        has_ramp = self.arrays.ramp_down.notnull()
        if not has_ramp.any():
            return []
        decrease = self._previous_consumption() - self.variables.consumption
        commitment = self.variables.commitment
        if commitment is not None:
            previous_upper_bound = self.upper_bounds.shift({TIME: 1}).fillna(self.states.initial_power)
            decrease -= commitment.shutdown * previous_upper_bound
        with_ramp = {FLEXIBLE_LOAD: has_ramp}
        max_decrease = (self.arrays.ramp_down * self.context.timestep_hours).sel(with_ramp)
        return [
            ModelConstraint(
                constraint=decrease.sel(with_ramp).to_constraint("<=", max_decrease),
                name="flexible_load_max_ramp_down_constraint",
            ),
        ]

    @property
    def _has_commitment(self) -> bool:
        """Return whether some flexible load has a commitment, so the loads get on/off indicators."""
        return bool(self.states.is_switchable.any())

    def _previous_consumption(self) -> linopy.LinearExpression:
        """Return the consumption one step earlier, the initial consumption at t=0."""
        return time_shifted(self.variables.consumption, 1, outside_value=self.states.initial_power)

    def power_injection(self) -> linopy.LinearExpression:
        """Return minus the consumption, summed over flexible loads."""
        injection: linopy.LinearExpression = -self.variables.consumption.sum(FLEXIBLE_LOAD)
        return injection

    def profit(self) -> linopy.LinearExpression:
        """Return the value of the consumption less startup and shutdown costs, per scenario, in currency."""
        value = self.variables.consumption * self.context.timestep_hours * self.arrays.value_of_consumption
        commitment = self.variables.commitment
        if commitment is not None:
            value -= self.commitment.costs(commitment, self.commitment_arrays)
        profit: linopy.LinearExpression = value.sum([TIME, FLEXIBLE_LOAD])
        return profit

    def dispatch(self, solution: xr.Dataset) -> FlexibleLoadDispatch:
        """Return the consumption and the on/off status, startups and shutdowns of the flexible loads.

        Without on/off indicators, every load is on at every step, with no starts and no stops.
        """
        consumption = solution[self.variable_name]
        if self._has_commitment:
            on_off = {
                "status": solution[self.status_name],
                "startup": solution[self.startup_name],
                "shutdown": solution[self.shutdown_name],
            }
        else:
            on_off = {
                "status": xr.ones_like(consumption),
                "startup": xr.zeros_like(consumption),
                "shutdown": xr.zeros_like(consumption),
            }
        return FlexibleLoadDispatch(xr.Dataset({"consumption": consumption, **on_off}), FLEXIBLE_LOAD)
