"""Model formulation of battery storage."""

from collections.abc import Sequence
from typing import ClassVar, Self

import linopy
import xarray as xr

from odys.domain.entities.battery_storage import BatteryStorage
from odys.optimization.constraints.model_constraint import ModelConstraint
from odys.optimization.formulations.base import Formulation, FormulationInputs
from odys.optimization.formulations.storage import StorageFormulation, StorageVariables
from odys.parameters.context import ModelContext
from odys.parameters.entity_arrays import BatteryArrays, battery_storage_state_arrays
from odys.parameters.vectorize import vectorize
from odys.results.dispatch import BatteryStorageDispatch

BATTERY_STORAGE = "battery_storage"


class BatteryStorageFormulation(Formulation):
    """Battery storage: the shared battery model, injecting its net discharge into the bus."""

    dimension = BATTERY_STORAGE
    entity_type = BatteryStorage
    net_power_name: ClassVar[str] = f"{BATTERY_STORAGE}_net_power"
    soc_name: ClassVar[str] = f"{BATTERY_STORAGE}_soc"
    charge_mode_name: ClassVar[str] = f"{BATTERY_STORAGE}_charge_mode"

    def __init__(self, storages: Sequence[BatteryStorage], context: ModelContext, model: linopy.Model) -> None:
        """Initialize with the battery storages of the system.

        Args:
            storages: The battery storages, at least one.
            context: The shared indexing of the problem.
            model: The model to add the variables to.
        """
        super().__init__(storages, context)
        battery = vectorize(BatteryArrays, [storage.battery for storage in storages], self.coordinates)
        states = battery_storage_state_arrays(storages, self.coordinates, context)
        self.storage = StorageFormulation(self.coordinates, battery, states, context)
        self.variables = self._create_variables(model)

    @classmethod
    def build(cls, inputs: FormulationInputs) -> Self | None:
        """Return the formulation of the battery storages, or None if there are none."""
        storages = inputs.of_type(BatteryStorage)
        return cls(storages, inputs.context, inputs.model) if storages else None

    def _create_variables(self, model: linopy.Model) -> StorageVariables:
        """Add the battery variables of every battery storage."""
        return self.storage.create_variables(model)

    def constraints(self) -> list[ModelConstraint]:
        """Return the constraints of the shared battery model."""
        variables = self.variables
        return [
            self.storage.max_charge_constraint(variables),
            self.storage.max_discharge_constraint(variables),
            self.storage.soc_dynamics_constraint(variables),
            self.storage.soc_start_constraint(variables),
            *self.storage.soc_end_constraint(variables),
            self.storage.soc_min_constraint(variables),
            self.storage.soc_max_constraint(variables),
            self.storage.capacity_constraint(variables),
            self.storage.net_power_constraint(variables),
        ]

    def power_injection(self) -> linopy.LinearExpression:
        """Return discharging minus charging power, summed over the storages."""
        return self.storage.power_injection(self.variables)

    def profit(self) -> linopy.LinearExpression:
        """Return minus the degradation cost per scenario."""
        profit: linopy.LinearExpression = -self.storage.degradation_cost(self.variables)
        return profit

    def dispatch(self, solution: xr.Dataset) -> BatteryStorageDispatch:
        """Return the net power, state of charge and charge mode of the battery storages."""
        return BatteryStorageDispatch(self.storage.dispatch_data(solution), BATTERY_STORAGE)
