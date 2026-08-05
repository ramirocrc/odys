"""Electric vehicle-related constraints for the optimization model."""

from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING

from odys.optimization.constraints.constraints_group import ConstraintGroup, constraint
from odys.optimization.constraints.model_constraint import ModelConstraint
from odys.optimization.constraints.storage_constraints import (
    build_capacity_constraint,
    build_max_charge_constraint,
    build_max_discharge_constraint,
    build_net_power_constraint,
    build_soc_dynamics_constraint,
    build_soc_end_constraint,
    build_soc_max_constraint,
    build_soc_min_constraint,
    build_soc_start_constraint,
)
from odys.optimization.model.dimensions import ModelDimension

if TYPE_CHECKING:
    from odys.optimization.model.milp_model import EnergyMILPModel
    from odys.optimization.parameters.entity_parameters.electric_vehicle_parameters import ElectricVehicleParameters


class ElectricVehicleConstraints(ConstraintGroup):
    """Builds constraints for EV charge/discharge, SOC dynamics, and power limits."""

    def __init__(self, milp_model: EnergyMILPModel) -> None:
        """Initialize with the MILP model and electric vehicle parameters."""
        self.model = milp_model
        evs = milp_model.parameters.electric_vehicles
        if evs is None:
            msg = "ElectricVehicleConstraints requires electric vehicles to be present."
            raise ValueError(msg)
        self.params: ElectricVehicleParameters = evs
        self._timestep_hours = milp_model.parameters.timestep / timedelta(hours=1)

    @constraint
    def _get_ev_max_charge_constraint(self) -> ModelConstraint:
        """Maximum charging power limited by max_charge_power when in charging mode."""
        return build_max_charge_constraint(
            power_in=self.model.vars.ev_power_in,
            charge_mode=self.model.vars.ev_charge_mode,
            max_charge_power=self.params.max_charge_power,
            name="ev_max_charge_constraint",
        )

    @constraint
    def _get_ev_max_discharge_constraint(self) -> ModelConstraint:
        """Maximum discharging power limited by max_discharge_power when in discharging mode."""
        return build_max_discharge_constraint(
            power_out=self.model.vars.ev_power_out,
            charge_mode=self.model.vars.ev_charge_mode,
            max_discharge_power=self.params.max_discharge_power,
            name="ev_max_discharge_constraint",
        )

    @constraint
    def _get_ev_soc_dynamics_constraint(self) -> ModelConstraint:
        trip_soc_drop = self.params.trip_energy / self.params.capacity
        return build_soc_dynamics_constraint(
            soc=self.model.vars.ev_soc,
            power_in=self.model.vars.ev_power_in,
            power_out=self.model.vars.ev_power_out,
            self_discharge_rate=self.params.self_discharge_rate,
            efficiency_charging=self.params.efficiency_charging,
            efficiency_discharging=self.params.efficiency_discharging,
            capacity=self.params.capacity,
            timestep_hours=self._timestep_hours,
            name="ev_soc_dynamics_constraint",
            trip_soc_drop=trip_soc_drop,
        )

    @constraint
    def _get_ev_soc_start_constraint(self) -> ModelConstraint:
        trip_soc_drop_t0 = (self.params.trip_energy / self.params.capacity).isel(time=0)
        return build_soc_start_constraint(
            soc=self.model.vars.ev_soc,
            power_in=self.model.vars.ev_power_in,
            power_out=self.model.vars.ev_power_out,
            soc_start=self.params.soc_start,
            efficiency_charging=self.params.efficiency_charging,
            efficiency_discharging=self.params.efficiency_discharging,
            capacity=self.params.capacity,
            timestep_hours=self._timestep_hours,
            name="ev_soc_start_constraint",
            trip_soc_drop=trip_soc_drop_t0,
        )

    @constraint
    def _get_ev_soc_end_constraint(self) -> ModelConstraint | list[ModelConstraint]:
        return build_soc_end_constraint(
            soc=self.model.vars.ev_soc,
            soc_end=self.params.soc_end,
            asset_dimension=ModelDimension.EVs.value,
            name="ev_soc_end_constraint",
        )

    @constraint
    def _get_ev_soc_min_constraint(self) -> ModelConstraint:
        return build_soc_min_constraint(
            soc=self.model.vars.ev_soc,
            soc_min=self.params.soc_min,
            name="ev_soc_min_constraint",
        )

    @constraint
    def _get_ev_soc_max_constraint(self) -> ModelConstraint:
        return build_soc_max_constraint(
            soc=self.model.vars.ev_soc,
            soc_max=self.params.soc_max,
            name="ev_soc_max_constraint",
        )

    @constraint
    def _get_ev_capacity_constraint(self) -> ModelConstraint:
        return build_capacity_constraint(
            soc=self.model.vars.ev_soc,
            name="ev_capacity_constraint",
        )

    @constraint
    def _get_ev_driving_constraint(self) -> ModelConstraint:
        """EVs cannot charge or discharge while driving."""
        power_in = self.model.vars.ev_power_in
        power_out = self.model.vars.ev_power_out
        max_power = self.params.max_charge_power + self.params.max_discharge_power

        return ModelConstraint(
            constraint=power_in + power_out <= max_power * (1 - self.params.is_driving),
            name="ev_driving_constraint",
        )

    @constraint
    def _get_ev_min_soc_departure_constraint(self) -> ModelConstraint:
        """EVs must reach the required SoC by the end of the step before departure."""
        min_soc_before_departure = self.params.min_soc_at_departure.shift({ModelDimension.Time.value: -1}, fill_value=0)

        return ModelConstraint(
            constraint=self.model.vars.ev_soc >= min_soc_before_departure,
            name="ev_min_soc_departure_constraint",
        )

    @constraint
    def _get_ev_net_power_constraint(self) -> ModelConstraint:
        return build_net_power_constraint(
            power_net=self.model.vars.ev_net_power,
            power_in=self.model.vars.ev_power_in,
            power_out=self.model.vars.ev_power_out,
            name="ev_net_power_constraint",
        )
