from datetime import timedelta

import linopy
import pytest

from odys import Scenario
from odys.domain.entities.charger import Charger
from odys.domain.entities.electric_vehicle import ElectricVehicle
from odys.domain.entities.fixed_load import FixedLoad
from odys.domain.entities.generator import Generator
from odys.domain.entities.portfolio import AssetPortfolio
from odys.energy_system import EnergySystem
from odys.optimization.model.dimensions import ModelDimension
from odys.optimization.parameters.energy_system_parameters import EnergySystemParameters


@pytest.fixture
def ev1() -> ElectricVehicle:
    return ElectricVehicle(
        name="ev1",
        capacity=50.0,
        max_charge_power=22.0,
        max_discharge_power=11.0,
        soc_start=0.5,
        trips=(),
    )


@pytest.fixture
def ev2() -> ElectricVehicle:
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
def charger2() -> Charger:
    return Charger(name="charger2", max_power=50.0)


@pytest.fixture
def asset_portfolio_with_chargers(  # noqa: PLR0913
    generator1: Generator,
    generator2: Generator,
    ev1: ElectricVehicle,
    ev2: ElectricVehicle,
    charger1: Charger,
    charger2: Charger,
    load1: FixedLoad,
) -> AssetPortfolio:
    return AssetPortfolio(assets=[generator1, generator2, ev1, ev2, charger1, charger2, load1])


@pytest.fixture
def energy_system_with_chargers(
    asset_portfolio_with_chargers: AssetPortfolio,
    demand_profile_sample: list[float],
) -> EnergySystem:
    return EnergySystem(
        portfolio=asset_portfolio_with_chargers,
        number_of_steps=len(demand_profile_sample),
        timestep=timedelta(hours=1),
        scenarios=Scenario(
            available_capacity_profiles={},
            fixed_load_profiles={"load1": demand_profile_sample},
        ),
    )


@pytest.fixture
def energy_system_parameters(
    energy_system_with_chargers: EnergySystem,
) -> EnergySystemParameters:
    return energy_system_with_chargers.build_parameters()


class TestChargerConstraints:
    @pytest.fixture(autouse=True)
    def setup(  # noqa: PLR0913
        self,
        linopy_model: linopy.Model,
        ev1: ElectricVehicle,
        ev2: ElectricVehicle,
        charger1: Charger,
        charger2: Charger,
        time_index: list[int],
    ) -> None:
        self.linopy_model = linopy_model
        self.ev1 = ev1
        self.ev2 = ev2
        self.charger1 = charger1
        self.charger2 = charger2
        self.time_index = time_index

    def test_constraint_one_ev_per_charger(self) -> None:
        actual_constraint = self.linopy_model.constraints["charger_one_ev_per_charger_constraint"]
        assert isinstance(actual_constraint, linopy.Constraint)
        expected_dims = {ModelDimension.Scenarios.value, ModelDimension.Time.value, ModelDimension.Chargers.value}
        assert expected_dims.issubset(set(actual_constraint.dims))

    def test_constraint_one_charger_per_ev(self) -> None:
        actual_constraint = self.linopy_model.constraints["charger_one_charger_per_ev_constraint"]
        assert isinstance(actual_constraint, linopy.Constraint)
        expected_dims = {ModelDimension.Scenarios.value, ModelDimension.Time.value, ModelDimension.EVs.value}
        assert expected_dims.issubset(set(actual_constraint.dims))

    def test_constraint_no_assignment_while_driving(self) -> None:
        actual_constraint = self.linopy_model.constraints["charger_no_assignment_while_driving_constraint"]
        assert isinstance(actual_constraint, linopy.Constraint)
        expected_dims = {
            ModelDimension.Scenarios.value,
            ModelDimension.Time.value,
            ModelDimension.Chargers.value,
            ModelDimension.EVs.value,
        }
        assert expected_dims.issubset(set(actual_constraint.dims))

    def test_constraint_charger_power_limit(self) -> None:
        actual_constraint = self.linopy_model.constraints["charger_power_limit_constraint"]
        assert isinstance(actual_constraint, linopy.Constraint)
        expected_dims = {ModelDimension.Scenarios.value, ModelDimension.Time.value, ModelDimension.EVs.value}
        assert expected_dims.issubset(set(actual_constraint.dims))

    def test_charger_constraints_present(self) -> None:
        assert isinstance(self.linopy_model.constraints["charger_one_ev_per_charger_constraint"], linopy.Constraint)
        assert isinstance(self.linopy_model.constraints["charger_one_charger_per_ev_constraint"], linopy.Constraint)
        assert isinstance(
            self.linopy_model.constraints["charger_no_assignment_while_driving_constraint"],
            linopy.Constraint,
        )
        assert isinstance(self.linopy_model.constraints["charger_power_limit_constraint"], linopy.Constraint)
