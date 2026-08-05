from datetime import timedelta

import linopy
import pytest

from odys import Scenario
from odys.domain.entities.charger import Charger
from odys.domain.entities.electric_vehicle import ElectricVehicle
from odys.domain.entities.fixed_load import FixedLoad
from odys.domain.entities.generator import Generator
from odys.domain.entities.portfolio import AssetPortfolio
from odys.domain.entities.trip import Trip
from odys.energy_system import EnergySystem
from odys.optimization.model.dimensions import ModelDimension
from odys.parameters.energy_system_parameters import EnergySystemParameters


@pytest.fixture
def ev_with_trips() -> ElectricVehicle:
    return ElectricVehicle(
        name="ev1",
        capacity=50.0,
        max_charge_power=22.0,
        max_discharge_power=11.0,
        efficiency_charging=0.9,
        efficiency_discharging=0.85,
        soc_start=0.5,
        trips=(Trip(name="trip1", start_time=1, end_time=2, energy_consumption=5.0, min_soc_at_departure=0.3),),
    )


@pytest.fixture
def ev_no_trips() -> ElectricVehicle:
    return ElectricVehicle(
        name="ev2",
        capacity=75.0,
        max_charge_power=50.0,
        max_discharge_power=0.0,
        soc_start=0.8,
        trips=(),
    )


@pytest.fixture
def charger1() -> Charger:
    return Charger(name="charger1", max_power=22.0)


@pytest.fixture
def asset_portfolio_with_evs(  # noqa: PLR0913
    generator1: Generator,
    generator2: Generator,
    ev_with_trips: ElectricVehicle,
    ev_no_trips: ElectricVehicle,
    charger1: Charger,
    load1: FixedLoad,
) -> AssetPortfolio:
    return AssetPortfolio(assets=[generator1, generator2, ev_with_trips, ev_no_trips, charger1, load1])


@pytest.fixture
def energy_system_with_evs(
    asset_portfolio_with_evs: AssetPortfolio,
    demand_profile_sample: list[float],
) -> EnergySystem:
    return EnergySystem(
        portfolio=asset_portfolio_with_evs,
        number_of_steps=len(demand_profile_sample),
        timestep=timedelta(hours=1),
        scenarios=Scenario(
            available_capacity_profiles={},
            fixed_load_profiles={"load1": demand_profile_sample},
        ),
    )


@pytest.fixture
def energy_system_parameters(
    energy_system_with_evs: EnergySystem,
) -> EnergySystemParameters:
    return energy_system_with_evs.build_parameters()


class TestElectricVehicleConstraints:
    @pytest.fixture(autouse=True)
    def setup(
        self,
        linopy_model: linopy.Model,
        ev_with_trips: ElectricVehicle,
        ev_no_trips: ElectricVehicle,
        time_index: list[int],
    ) -> None:
        self.linopy_model = linopy_model
        self.ev_with_trips = ev_with_trips
        self.ev_no_trips = ev_no_trips
        self.time_index = time_index

    def test_constraint_ev_driving(self) -> None:
        actual_constraint = self.linopy_model.constraints["ev_driving_constraint"]
        assert isinstance(actual_constraint, linopy.Constraint)
        expected_dims = {ModelDimension.Scenarios.value, ModelDimension.Time.value, ModelDimension.EVs.value}
        assert expected_dims.issubset(set(actual_constraint.dims))

    def test_constraint_ev_driving_has_no_masked_entries(self) -> None:
        """Trip arrays with mismatching time coords silently mask every constraint entry."""
        actual_constraint = self.linopy_model.constraints["ev_driving_constraint"]
        assert bool((actual_constraint.labels != -1).all())

    def test_constraint_ev_min_soc_departure_has_no_masked_entries(self) -> None:
        """Trip arrays with mismatching time coords silently mask every constraint entry."""
        actual_constraint = self.linopy_model.constraints["ev_min_soc_departure_constraint"]
        assert bool((actual_constraint.labels != -1).all())

    def test_constraint_ev_min_soc_departure(self) -> None:
        actual_constraint = self.linopy_model.constraints["ev_min_soc_departure_constraint"]
        assert isinstance(actual_constraint, linopy.Constraint)
        expected_dims = {ModelDimension.Scenarios.value, ModelDimension.Time.value, ModelDimension.EVs.value}
        assert expected_dims.issubset(set(actual_constraint.dims))

    def test_constraint_ev_soc_dynamics_includes_trip_energy(self) -> None:
        actual_constraint = self.linopy_model.constraints["ev_soc_dynamics_constraint"]
        assert isinstance(actual_constraint, linopy.Constraint)

    def test_constraint_ev_soc_start_includes_trip_energy(self) -> None:
        actual_constraint = self.linopy_model.constraints["ev_soc_start_constraint"]
        assert isinstance(actual_constraint, linopy.Constraint)
