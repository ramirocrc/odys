"""Model formulation of chargers: which electric vehicle each charger serves, and at what power."""

from collections.abc import Sequence
from typing import ClassVar, Self

import linopy
from pydantic import BaseModel, ConfigDict

from odys.domain.entities.charger import Charger
from odys.domain.exceptions import OdysError
from odys.optimization.constraints.constraints_group import constraint
from odys.optimization.constraints.model_constraint import ModelConstraint
from odys.optimization.formulations.base import FormulationInputs, VariableFormulation
from odys.optimization.formulations.electric_vehicle import ElectricVehicleFormulation
from odys.parameters.context import ModelContext
from odys.parameters.dimensions import ModelDimension
from odys.parameters.entity_arrays import ChargerArrays
from odys.parameters.vectorize import vectorize


class ChargingVariables(BaseModel):
    """Decision variables of the chargers."""

    model_config = ConfigDict(frozen=True, extra="forbid", arbitrary_types_allowed=True)

    assignment: linopy.Variable


class ChargingFormulation(VariableFormulation[ChargingVariables]):
    """Chargers: assign electric vehicles to chargers and cap their power by the charger's rating.

    It couples to the `ElectricVehicleFormulation` it receives: the vehicles' power
    variables and trip schedule. Chargers inject nothing into the power balance;
    the vehicles do.
    """

    assignment_name: ClassVar[str] = "charger_ev_assignment"

    def __init__(
        self,
        chargers: Sequence[Charger],
        context: ModelContext,
        electric_vehicles: ElectricVehicleFormulation,
    ) -> None:
        """Initialize with the chargers of the system and the electric vehicles they serve.

        Args:
            chargers: The chargers, at least one.
            context: The shared indexing of the problem.
            electric_vehicles: The formulation of the vehicles the chargers serve.
        """
        super().__init__(context)
        self.coordinates = context.coordinates_of(ModelDimension.Chargers)
        self.arrays = vectorize(ChargerArrays, chargers, self.coordinates)
        self.electric_vehicles = electric_vehicles

    @classmethod
    def build(cls, inputs: FormulationInputs) -> Self | None:
        """Return the formulation of the chargers, or None if there are none.

        Raises:
            OdysError: If there are chargers but no electric vehicle formulation was built before.
        """
        chargers = inputs.of_type(Charger)
        if not chargers:
            return None
        electric_vehicles = inputs.formulation_of(ElectricVehicleFormulation)
        if electric_vehicles is None:
            msg = "ChargingFormulation must be built after an ElectricVehicleFormulation."
            raise OdysError(msg)
        return cls(chargers, inputs.context, electric_vehicles)

    def _create_variables(self, model: linopy.Model) -> ChargingVariables:
        """Add the binary assignment of each vehicle to each charger, per scenario and time."""
        coords = self.context.variable_coords(self.coordinates, self.context.coordinates_of(ModelDimension.EVs))
        return ChargingVariables(
            assignment=model.add_variables(name=self.assignment_name, coords=coords, binary=True),
        )

    @constraint
    def _get_charger_one_ev_per_charger_constraint(self) -> ModelConstraint:
        """Each charger serves at most one vehicle at a time."""
        return ModelConstraint(
            constraint=self.variables.assignment.sum(ModelDimension.EVs) <= 1,
            name="charger_one_ev_per_charger_constraint",
        )

    @constraint
    def _get_charger_one_charger_per_ev_constraint(self) -> ModelConstraint:
        """Each vehicle is connected to at most one charger at a time."""
        return ModelConstraint(
            constraint=self.variables.assignment.sum(ModelDimension.Chargers) <= 1,
            name="charger_one_charger_per_ev_constraint",
        )

    @constraint
    def _get_charger_no_assignment_while_driving_constraint(self) -> ModelConstraint:
        """A driving vehicle cannot be assigned to a charger."""
        return ModelConstraint(
            constraint=self.variables.assignment <= 1 - self.electric_vehicles.trips.is_driving,
            name="charger_no_assignment_while_driving_constraint",
        )

    @constraint
    def _get_charger_power_limit_constraint(self) -> ModelConstraint:
        """A vehicle's charging and discharging power is capped by its assigned charger's `max_power`.

        With no charger assigned the cap is 0, so a vehicle charges or discharges (V2G) only through a charger.
        """
        available_power = (self.variables.assignment * self.arrays.max_power).sum(ModelDimension.Chargers)
        vehicles = self.electric_vehicles.variables
        return ModelConstraint(
            constraint=vehicles.power_in + vehicles.power_out <= available_power,
            name="charger_power_limit_constraint",
        )

    def power_injection(self) -> None:
        """Return None: chargers are outside the power balance; the vehicles they serve inject."""
