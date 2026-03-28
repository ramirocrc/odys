"""Storage-related constraints for the optimization model."""

from datetime import timedelta

from odys.math_model.milp_model import EnergyMILPModel
from odys.math_model.model_components.constraints.constraints_group import ConstraintGroup, constraint
from odys.math_model.model_components.constraints.model_constraint import ModelConstraint
from odys.math_model.model_components.parameters.storage_parameters import StorageParameters
from odys.math_model.model_components.sets import ModelDimension


class StorageConstraints(ConstraintGroup):
    """Builds constraints for storage charge/discharge, SOC dynamics, and power limits."""

    def __init__(self, milp_model: EnergyMILPModel, params: StorageParameters) -> None:
        """Initialize with the MILP model and storage parameters."""
        self.model = milp_model
        self.params = params
        self._timestep_hours = milp_model.parameters.timestep / timedelta(hours=1)

    @constraint
    def _get_storage_max_charge_constraint(self) -> ModelConstraint:
        return ModelConstraint(
            constraint=self.model.storage_power_in <= self.model.storage_charge_mode * self.params.max_power,
            name="storage_max_charge_constraint",
        )

    @constraint
    def _get_storage_max_discharge_constraint(self) -> ModelConstraint:
        return ModelConstraint(
            constraint=self.model.storage_power_out + self.model.storage_charge_mode * self.params.max_power
            <= self.params.max_power,
            name="storage_max_discharge_constraint",
        )

    @constraint
    def _get_storage_soc_dynamics_constraint(self) -> ModelConstraint:
        time_coords = self.model.storage_soc.coords[ModelDimension.Time.value]
        dt = self._timestep_hours
        constraint_expr = self.model.storage_soc - (
            self.model.storage_soc.shift(time=1)
            + self.params.efficiency_charging * self.model.storage_power_in * dt / self.params.capacity
            - 1 / self.params.efficiency_discharging * self.model.storage_power_out * dt / self.params.capacity
        )
        return ModelConstraint(
            constraint=constraint_expr.where(time_coords > time_coords[0]) == 0,
            name="storage_soc_dynamics_constraint",
        )

    @constraint
    def _get_storage_soc_start_constraint(self) -> ModelConstraint:
        t0 = self.model.storage_soc.coords[ModelDimension.Time.value][0]
        soc_t0 = self.model.storage_soc.sel(time=t0)
        charge_t0 = self.model.storage_power_in.sel(time=t0)
        discharge_t0 = self.model.storage_power_out.sel(time=t0)
        dt = self._timestep_hours
        constraint_expr = (
            soc_t0
            - self.params.soc_start
            - self.params.efficiency_charging * charge_t0 * dt / self.params.capacity
            + 1 / self.params.efficiency_discharging * discharge_t0 * dt / self.params.capacity
        )
        return ModelConstraint(
            constraint=constraint_expr == 0,
            name="storage_soc_start_constraint",
        )

    @constraint
    def _get_storage_soc_end_constraint(self) -> ModelConstraint:
        time_coords = self.model.storage_soc.coords[ModelDimension.Time.value]
        last_time = time_coords.values[-1]
        return ModelConstraint(
            constraint=self.model.storage_soc.sel(time=last_time) - self.params.soc_end == 0,
            name="storage_soc_end_constraint",
        )

    @constraint
    def _get_storage_soc_min_constraint(self) -> ModelConstraint:
        return ModelConstraint(
            constraint=self.model.storage_soc >= self.params.soc_min,
            name="storage_soc_min_constraint",
        )

    @constraint
    def _get_storage_soc_max_constraint(self) -> ModelConstraint:
        return ModelConstraint(
            constraint=self.model.storage_soc <= self.params.soc_max,
            name="storage_soc_max_constraint",
        )

    @constraint
    def _get_storage_capacity_constraint(self) -> ModelConstraint:
        return ModelConstraint(
            constraint=self.model.storage_soc <= 1,  # pyrefly: ignore
            name="storage_capacity_constraint",
        )

    @constraint
    def _get_storage_net_power_constraint(self) -> ModelConstraint:
        return ModelConstraint(
            constraint=self.model.storage_power_net == self.model.storage_power_in - self.model.storage_power_out,
            name="storage_net_power_constraint",
        )
