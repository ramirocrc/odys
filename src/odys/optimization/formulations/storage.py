"""Battery physics shared by every storage-like entity type (stationary storage, electric vehicles)."""

import linopy
import numpy as np
import xarray as xr
from pydantic import BaseModel, ConfigDict

from odys.optimization.constraints.model_constraint import ModelConstraint
from odys.parameters.context import ModelContext
from odys.parameters.coordinates import Coordinates
from odys.parameters.dimensions import ModelDimension
from odys.parameters.entity_arrays import BatteryArrays

TIME = ModelDimension.Time


class StorageVariables(BaseModel):
    """Decision variables of a battery: charge and discharge power, net power, state of charge and mode."""

    model_config = ConfigDict(frozen=True, extra="forbid", arbitrary_types_allowed=True)

    power_in: linopy.Variable
    net_power: linopy.Variable
    power_out: linopy.Variable
    soc: linopy.Variable
    charge_mode: linopy.Variable


class StorageFormulation:
    """The battery model of one storage-like entity type, composed by that type's formulation.

    It is a reusable part, not a `Formulation`: it holds no variables (the
    composing formulation does, and passes them in), and each method returns
    one constraint. Variable and constraint names are prefixed with the
    dimension name ("stationary_storage", "ev"). An optional SOC drop (EV trip
    energy as a fraction of capacity) is subtracted at each step.
    """

    def __init__(
        self,
        coordinates: Coordinates,
        battery: BatteryArrays,
        context: ModelContext,
        soc_drop: xr.DataArray | None = None,
    ) -> None:
        """Initialize the battery model.

        Args:
            coordinates: The labels of the batteries along their dimension, which also names them.
            battery: The battery parameters, vectorized along that dimension.
            context: The shared indexing of the problem.
            soc_drop: SOC lost at each step outside charging (EV trips), if any.
        """
        self.coordinates = coordinates
        self.battery = battery
        self.context = context
        self.soc_drop = soc_drop

    @property
    def dimension(self) -> ModelDimension:
        """Return the dimension the batteries are indexed along."""
        return self.coordinates.dimension

    def name(self, what: str) -> str:
        """Return the model name of a variable or constraint of this entity type, such as `ev_soc`."""
        return f"{self.dimension.value}_{what}"

    def create_variables(self, model: linopy.Model) -> StorageVariables:
        """Add the battery variables: powers and SOC are non-negative, net power is free, the mode is binary."""
        coords = self.context.variable_coords(self.coordinates)
        return StorageVariables(
            power_in=model.add_variables(name=self.name("power_in"), coords=coords, lower=0.0),
            net_power=model.add_variables(name=self.name("net_power"), coords=coords, lower=-np.inf),
            power_out=model.add_variables(name=self.name("power_out"), coords=coords, lower=0.0),
            soc=model.add_variables(name=self.name("soc"), coords=coords, lower=0.0),
            charge_mode=model.add_variables(name=self.name("charge_mode"), coords=coords, binary=True),
        )

    def max_charge_constraint(self, variables: StorageVariables) -> ModelConstraint:
        """Charging power is limited by `max_charge_power`, and only in charging mode."""
        return ModelConstraint(
            constraint=variables.power_in <= variables.charge_mode * self.battery.max_charge_power,
            name=self.name("max_charge_constraint"),
        )

    def max_discharge_constraint(self, variables: StorageVariables) -> ModelConstraint:
        """Discharging power is limited by `max_discharge_power`, and only outside charging mode."""
        max_discharge_power = self.battery.max_discharge_power
        return ModelConstraint(
            constraint=variables.power_out + variables.charge_mode * max_discharge_power <= max_discharge_power,
            name=self.name("max_discharge_constraint"),
        )

    def soc_dynamics_constraint(self, variables: StorageVariables) -> ModelConstraint:
        """SOC follows self-discharge, charging and discharging (with efficiencies) from step to step."""
        dt = self.context.timestep_hours
        battery = self.battery
        soc = variables.soc
        time_coords = soc.coords[TIME.value]
        expression = soc - (
            soc.shift({TIME: 1}) * (1 - battery.self_discharge_rate * dt)
            + battery.efficiency_charging * variables.power_in * dt / battery.capacity
            - 1 / battery.efficiency_discharging * variables.power_out * dt / battery.capacity
        )
        if self.soc_drop is not None:
            expression += self.soc_drop
        return ModelConstraint(
            constraint=expression.where(time_coords != time_coords[0]).to_constraint("=", 0),
            name=self.name("soc_dynamics_constraint"),
        )

    def soc_start_constraint(self, variables: StorageVariables) -> ModelConstraint:
        """The SOC after the first step starts from `soc_start`, less the SOC drop at t=0 (a trip departing then)."""
        dt = self.context.timestep_hours
        battery = self.battery
        first_step = {TIME: variables.soc.coords[TIME.value].values[0]}
        expression = (
            variables.soc.sel(first_step)
            - battery.soc_start
            - battery.efficiency_charging * variables.power_in.sel(first_step) * dt / battery.capacity
            + 1 / battery.efficiency_discharging * variables.power_out.sel(first_step) * dt / battery.capacity
        )
        if self.soc_drop is not None:
            expression += self.soc_drop.isel({TIME: 0})
        return ModelConstraint(
            constraint=expression.to_constraint("=", 0),
            name=self.name("soc_start_constraint"),
        )

    def soc_end_constraint(self, variables: StorageVariables) -> list[ModelConstraint]:
        """The SOC at the last step equals `soc_end`, for the batteries that set one."""
        has_soc_end = self.battery.soc_end.notnull()
        if not has_soc_end.any():
            return []
        last_step = {TIME: variables.soc.coords[TIME.value].values[-1]}
        with_soc_end = {self.dimension: has_soc_end}
        expression = variables.soc.sel(last_step).sel(with_soc_end) - self.battery.soc_end.sel(with_soc_end)
        return [
            ModelConstraint(
                constraint=expression.to_constraint("=", 0),
                name=self.name("soc_end_constraint"),
            ),
        ]

    def soc_min_constraint(self, variables: StorageVariables) -> ModelConstraint:
        """The SOC never falls below `soc_min`."""
        return ModelConstraint(
            constraint=variables.soc >= self.battery.soc_min,
            name=self.name("soc_min_constraint"),
        )

    def soc_max_constraint(self, variables: StorageVariables) -> ModelConstraint:
        """The SOC never exceeds `soc_max`."""
        return ModelConstraint(
            constraint=variables.soc <= self.battery.soc_max,
            name=self.name("soc_max_constraint"),
        )

    def capacity_constraint(self, variables: StorageVariables) -> ModelConstraint:
        """The SOC never exceeds a full battery (1)."""
        return ModelConstraint(
            constraint=(1 * variables.soc).to_constraint("<=", 1),
            name=self.name("capacity_constraint"),
        )

    def net_power_constraint(self, variables: StorageVariables) -> ModelConstraint:
        """Net power is charging minus discharging power."""
        return ModelConstraint(
            constraint=(variables.net_power - variables.power_in + variables.power_out).to_constraint("=", 0),
            name=self.name("net_power_constraint"),
        )

    def power_injection(self, variables: StorageVariables) -> linopy.LinearExpression:
        """Return discharging minus charging power, summed over the batteries."""
        discharge = variables.power_out.sum(self.dimension)
        injection: linopy.LinearExpression = discharge - variables.power_in.sum(self.dimension)
        return injection

    def degradation_cost(self, variables: StorageVariables) -> linopy.LinearExpression:
        """Return the degradation cost per scenario: throughput times step length times cost per MWh."""
        throughput = (variables.power_in + variables.power_out) * self.context.timestep_hours
        cost: linopy.LinearExpression = (throughput * self.battery.degradation_cost).sum([TIME, self.dimension])
        return cost
