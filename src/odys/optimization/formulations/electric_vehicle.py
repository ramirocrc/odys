"""Model formulation of electric vehicles."""

from collections.abc import Sequence
from typing import ClassVar, Self

import linopy
import xarray as xr

from odys.domain.entities.electric_vehicle import ElectricVehicle
from odys.optimization.constraints.model_constraint import ModelConstraint
from odys.optimization.formulations.base import Formulation, FormulationInputs
from odys.optimization.formulations.storage import StorageFormulation, StorageVariables
from odys.parameters.context import ModelContext
from odys.parameters.dimensions import ModelDimension
from odys.parameters.entity_arrays import ElectricVehicleTripArrays, electric_vehicle_arrays
from odys.results.dispatch import ElectricVehicleDispatch

EV = "ev"


class ElectricVehicleFormulation(Formulation):
    """Electric vehicles: the shared battery model with trip energy drawn from the battery while driving.

    A vehicle cannot charge or discharge while driving and must reach its departure SOC
    before each trip. It charges and discharges only through a charger (`ChargingFormulation`).
    """

    dimension = EV
    entity_type = ElectricVehicle
    power_in_name: ClassVar[str] = f"{EV}_power_in"
    net_power_name: ClassVar[str] = f"{EV}_net_power"
    soc_name: ClassVar[str] = f"{EV}_soc"
    charge_mode_name: ClassVar[str] = f"{EV}_charge_mode"

    def __init__(
        self,
        electric_vehicles: Sequence[ElectricVehicle],
        context: ModelContext,
        model: linopy.Model,
    ) -> None:
        """Initialize with the electric vehicles of the system.

        Args:
            electric_vehicles: The electric vehicles, at least one.
            context: The shared indexing of the problem.
            model: The model to add the variables to.
        """
        super().__init__(electric_vehicles, context)
        arrays = electric_vehicle_arrays(electric_vehicles, self.coordinates, context)
        self.trips: ElectricVehicleTripArrays = arrays.trips
        self.storage = StorageFormulation(
            self.coordinates,
            arrays.battery,
            arrays.states,
            context,
            soc_drop=arrays.trips.trip_energy / arrays.battery.capacity,
        )
        self.variables = self._create_variables(model)

    @classmethod
    def build(cls, inputs: FormulationInputs) -> Self | None:
        """Return the formulation of the electric vehicles, or None if there are none."""
        electric_vehicles = inputs.of_type(ElectricVehicle)
        return cls(electric_vehicles, inputs.context, inputs.model) if electric_vehicles else None

    def _create_variables(self, model: linopy.Model) -> StorageVariables:
        """Add the battery variables of every electric vehicle."""
        return self.storage.create_variables(model)

    def constraints(self) -> list[ModelConstraint]:
        """Return the constraints of the shared battery model, with driving and the SOC needed at departure."""
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
            self._get_ev_driving_constraint(),
            self._get_ev_min_soc_departure_constraint(),
            self.storage.net_power_constraint(variables),
        ]

    def _get_ev_driving_constraint(self) -> ModelConstraint:
        """A vehicle cannot charge or discharge while driving."""
        battery = self.storage.battery
        max_power = battery.max_charge_power + battery.max_discharge_power
        return ModelConstraint(
            constraint=self.variables.power_in + self.variables.power_out <= max_power * (1 - self.trips.is_driving),
            name="ev_driving_constraint",
        )

    def _get_ev_min_soc_departure_constraint(self) -> ModelConstraint:
        """A vehicle reaches its departure SOC by the end of the step before the trip."""
        min_soc_before_departure = self.trips.min_soc_at_departure.shift({ModelDimension.Time: -1}, fill_value=0)
        return ModelConstraint(
            constraint=self.variables.soc >= min_soc_before_departure,
            name="ev_min_soc_departure_constraint",
        )

    def power_injection(self) -> linopy.LinearExpression:
        """Return discharging minus charging power (V2G minus charging), summed over the vehicles."""
        return self.storage.power_injection(self.variables)

    def profit(self) -> linopy.LinearExpression:
        """Return minus the battery degradation cost per scenario."""
        profit: linopy.LinearExpression = -self.storage.degradation_cost(self.variables)
        return profit

    def dispatch(self, solution: xr.Dataset) -> ElectricVehicleDispatch:
        """Return the net power, state of charge and charge mode of the electric vehicles."""
        return ElectricVehicleDispatch(self.storage.dispatch_data(solution), EV)
