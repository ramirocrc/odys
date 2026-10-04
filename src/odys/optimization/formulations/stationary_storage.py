"""Model formulation of stationary storage."""

from collections.abc import Sequence
from typing import ClassVar, Self

import linopy

from odys.domain.entities.stationary_storage import StationaryStorage
from odys.optimization.constraints.constraints_group import constraint
from odys.optimization.constraints.model_constraint import ModelConstraint
from odys.optimization.formulations.base import FormulationInputs, VariableFormulation
from odys.optimization.formulations.storage import StorageFormulation, StorageVariables
from odys.parameters.context import ModelContext
from odys.parameters.dimensions import ModelDimension
from odys.parameters.entity_arrays import BatteryArrays
from odys.parameters.vectorize import vectorize


class StationaryStorageFormulation(VariableFormulation[StorageVariables]):
    """Stationary storage: the shared battery model, injecting its net discharge into the bus."""

    net_power_name: ClassVar[str] = f"{ModelDimension.StationaryStorages.value}_net_power"
    soc_name: ClassVar[str] = f"{ModelDimension.StationaryStorages.value}_soc"
    charge_mode_name: ClassVar[str] = f"{ModelDimension.StationaryStorages.value}_charge_mode"

    def __init__(self, storages: Sequence[StationaryStorage], context: ModelContext) -> None:
        """Initialize with the stationary storages of the system.

        Args:
            storages: The stationary storages, at least one.
            context: The shared indexing of the problem.
        """
        super().__init__(context)
        coordinates = context.coordinates_of(ModelDimension.StationaryStorages)
        battery = vectorize(BatteryArrays, [storage.battery for storage in storages], coordinates)
        self.storage = StorageFormulation(coordinates, battery, context)

    @classmethod
    def build(cls, inputs: FormulationInputs) -> Self | None:
        """Return the formulation of the stationary storages, or None if there are none."""
        storages = inputs.of_type(StationaryStorage)
        return cls(storages, inputs.context) if storages else None

    def _create_variables(self, model: linopy.Model) -> StorageVariables:
        """Add the battery variables of every stationary storage."""
        return self.storage.create_variables(model)

    @constraint
    def _get_stationary_storage_max_charge_constraint(self) -> ModelConstraint:
        """Charging power is limited by `max_charge_power`, and only in charging mode."""
        return self.storage.max_charge_constraint(self.variables)

    @constraint
    def _get_stationary_storage_max_discharge_constraint(self) -> ModelConstraint:
        """Discharging power is limited by `max_discharge_power`, and only outside charging mode."""
        return self.storage.max_discharge_constraint(self.variables)

    @constraint
    def _get_stationary_storage_soc_dynamics_constraint(self) -> ModelConstraint:
        """SOC follows self-discharge, charging and discharging from step to step."""
        return self.storage.soc_dynamics_constraint(self.variables)

    @constraint
    def _get_stationary_storage_soc_start_constraint(self) -> ModelConstraint:
        """The SOC after the first step starts from `soc_start`."""
        return self.storage.soc_start_constraint(self.variables)

    @constraint
    def _get_stationary_storage_soc_end_constraint(self) -> list[ModelConstraint]:
        """The SOC at the last step equals `soc_end`, where set."""
        return self.storage.soc_end_constraint(self.variables)

    @constraint
    def _get_stationary_storage_soc_min_constraint(self) -> ModelConstraint:
        """The SOC never falls below `soc_min`."""
        return self.storage.soc_min_constraint(self.variables)

    @constraint
    def _get_stationary_storage_soc_max_constraint(self) -> ModelConstraint:
        """The SOC never exceeds `soc_max`."""
        return self.storage.soc_max_constraint(self.variables)

    @constraint
    def _get_stationary_storage_capacity_constraint(self) -> ModelConstraint:
        """The SOC never exceeds a full battery."""
        return self.storage.capacity_constraint(self.variables)

    @constraint
    def _get_stationary_storage_net_power_constraint(self) -> ModelConstraint:
        """Net power is charging minus discharging power."""
        return self.storage.net_power_constraint(self.variables)

    def power_injection(self) -> linopy.LinearExpression:
        """Return discharging minus charging power, summed over the storages."""
        return self.storage.power_injection(self.variables)

    def profit(self) -> linopy.LinearExpression:
        """Return minus the degradation cost per scenario."""
        profit: linopy.LinearExpression = -self.storage.degradation_cost(self.variables)
        return profit
