"""Standalone storage-related constraints for the optimization model."""

from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING

from odys.optimization.constraints.constraints_group import ConstraintGroup, constraint
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
    from odys.optimization.constraints.model_constraint import ModelConstraint
    from odys.optimization.model.milp_model import EnergyMILPModel
    from odys.optimization.parameters.entity_parameters.standalone_storage_parameters import StandaloneStorageParameters


class StandaloneStorageConstraints(ConstraintGroup):
    """Builds constraints for standalone storage charge/discharge, SOC dynamics, and power limits."""

    def __init__(self, milp_model: EnergyMILPModel) -> None:
        """Initialize with the MILP model and standalone storage parameters."""
        self.model = milp_model
        storages = milp_model.parameters.standalone_storages
        if storages is None:
            msg = "StandaloneStorageConstraints requires standalone storages to be present."
            raise ValueError(msg)
        self.params: StandaloneStorageParameters = storages
        self._timestep_hours = milp_model.parameters.timestep / timedelta(hours=1)

    @constraint
    def _get_standalone_storage_max_charge_constraint(self) -> ModelConstraint:
        """Maximum charging power limited by max_charge_power when in charging mode."""
        return build_max_charge_constraint(
            power_in=self.model.vars.standalone_storage_power_in,
            charge_mode=self.model.vars.standalone_storage_charge_mode,
            max_charge_power=self.params.max_charge_power,
            name="standalone_storage_max_charge_constraint",
        )

    @constraint
    def _get_standalone_storage_max_discharge_constraint(self) -> ModelConstraint:
        """Maximum discharging power limited by max_discharge_power when in discharging mode."""
        return build_max_discharge_constraint(
            power_out=self.model.vars.standalone_storage_power_out,
            charge_mode=self.model.vars.standalone_storage_charge_mode,
            max_discharge_power=self.params.max_discharge_power,
            name="standalone_storage_max_discharge_constraint",
        )

    @constraint
    def _get_standalone_storage_soc_dynamics_constraint(self) -> ModelConstraint:
        return build_soc_dynamics_constraint(
            soc=self.model.vars.standalone_storage_soc,
            power_in=self.model.vars.standalone_storage_power_in,
            power_out=self.model.vars.standalone_storage_power_out,
            self_discharge_rate=self.params.self_discharge_rate,
            efficiency_charging=self.params.efficiency_charging,
            efficiency_discharging=self.params.efficiency_discharging,
            capacity=self.params.capacity,
            timestep_hours=self._timestep_hours,
            name="standalone_storage_soc_dynamics_constraint",
        )

    @constraint
    def _get_standalone_storage_soc_start_constraint(self) -> ModelConstraint:
        return build_soc_start_constraint(
            soc=self.model.vars.standalone_storage_soc,
            power_in=self.model.vars.standalone_storage_power_in,
            power_out=self.model.vars.standalone_storage_power_out,
            soc_start=self.params.soc_start,
            efficiency_charging=self.params.efficiency_charging,
            efficiency_discharging=self.params.efficiency_discharging,
            capacity=self.params.capacity,
            timestep_hours=self._timestep_hours,
            name="standalone_storage_soc_start_constraint",
        )

    @constraint
    def _get_standalone_storage_soc_end_constraint(self) -> ModelConstraint | list[ModelConstraint]:
        return build_soc_end_constraint(
            soc=self.model.vars.standalone_storage_soc,
            soc_end=self.params.soc_end,
            asset_dimension=ModelDimension.StandaloneStorages.value,
            name="standalone_storage_soc_end_constraint",
        )

    @constraint
    def _get_standalone_storage_soc_min_constraint(self) -> ModelConstraint:
        return build_soc_min_constraint(
            soc=self.model.vars.standalone_storage_soc,
            soc_min=self.params.soc_min,
            name="standalone_storage_soc_min_constraint",
        )

    @constraint
    def _get_standalone_storage_soc_max_constraint(self) -> ModelConstraint:
        return build_soc_max_constraint(
            soc=self.model.vars.standalone_storage_soc,
            soc_max=self.params.soc_max,
            name="standalone_storage_soc_max_constraint",
        )

    @constraint
    def _get_standalone_storage_capacity_constraint(self) -> ModelConstraint:
        return build_capacity_constraint(
            soc=self.model.vars.standalone_storage_soc,
            name="standalone_storage_capacity_constraint",
        )

    @constraint
    def _get_standalone_storage_net_power_constraint(self) -> ModelConstraint:
        return build_net_power_constraint(
            power_net=self.model.vars.standalone_storage_net_power,
            power_in=self.model.vars.standalone_storage_power_in,
            power_out=self.model.vars.standalone_storage_power_out,
            name="standalone_storage_net_power_constraint",
        )
