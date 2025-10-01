import logging
from datetime import timedelta

import linopy
import pytest
import xarray as xr
from linopy.testing import assert_conequal

from optimes._math_model.model_builder import EnergyAlgebraicModelBuilder
from optimes.energy_system_models.assets.generator import PowerGenerator
from optimes.energy_system_models.assets.portfolio import AssetPortfolio
from optimes.energy_system_models.assets.storage import Battery
from optimes.energy_system_models.scenarios import Scenario
from optimes.energy_system_models.units import PowerUnit
from optimes.energy_system_models.validated_energy_system import ValidatedEnergySystem

logger = logging.getLogger(__name__)


@pytest.fixture
def generator1() -> PowerGenerator:
    return PowerGenerator(
        name="gen1",
        nominal_power=100.0,
        variable_cost=20.0,
    )


@pytest.fixture
def generator2() -> PowerGenerator:
    return PowerGenerator(
        name="gen2",
        nominal_power=150.0,
        variable_cost=25.0,
    )


@pytest.fixture
def battery1() -> Battery:
    return Battery(
        name="batt1",
        max_power=200.0,
        capacity=100.0,
        efficiency_charging=0.9,
        efficiency_discharging=0.8,
        soc_start=25.0,
        soc_end=50.0,
    )


@pytest.fixture
def asset_portfolio_sample(
    generator1: PowerGenerator,
    generator2: PowerGenerator,
    battery1: Battery,
) -> AssetPortfolio:
    portfolio = AssetPortfolio()
    portfolio.add_asset(generator1)
    portfolio.add_asset(generator2)
    portfolio.add_asset(battery1)
    return portfolio


@pytest.fixture
def demand_profile_sample() -> list[float]:
    return [150, 200, 150]


@pytest.fixture
def time_index(demand_profile_sample: list[float]) -> list[int]:
    return list(range(len(demand_profile_sample)))


@pytest.fixture
def energy_system_sample(
    asset_portfolio_sample: AssetPortfolio,
    demand_profile_sample: list[float],
) -> ValidatedEnergySystem:
    return ValidatedEnergySystem(
        portfolio=asset_portfolio_sample,
        demand_profile=demand_profile_sample,
        timestep=timedelta(hours=1),
        power_unit=PowerUnit.MegaWatt,
        scenario=Scenario(
            available_capacity_profiles={
                "gen1": [80, 80, 100],
            },
        ),
    )


@pytest.fixture
def linopy_model(energy_system_sample: ValidatedEnergySystem) -> linopy.Model:
    model_builder = EnergyAlgebraicModelBuilder(energy_system_sample.parameters)
    return model_builder.build()


class TestScenarioConstraints:
    @pytest.fixture(autouse=True)
    def setup(
        self,
        linopy_model: linopy.Model,
        demand_profile_sample: list[float],
        time_index: list[int],
    ) -> None:
        self.linopy_model = linopy_model
        self.demand_profile_sample = demand_profile_sample
        self.time_index = time_index

    def test_constraint_power_balance(self) -> None:
        actual_constraint = self.linopy_model.constraints["power_balance_constraint"]

        generation_total = self.linopy_model.variables["generator_power"].sum("generators")
        discharge_total = self.linopy_model.variables["battery_power_out"].sum("batteries")
        charge_total = self.linopy_model.variables["battery_power_in"].sum("batteries")

        demand_array = xr.DataArray(self.demand_profile_sample, coords=[self.time_index], dims=["time"])
        expected_expr = generation_total + discharge_total - charge_total == demand_array

        assert_conequal(expected_expr, actual_constraint.lhs == actual_constraint.rhs)

    def test_constraint_available_capacity_profiles(self) -> None:
        actual_constraint = self.linopy_model.constraints["available_capacity_constraint"]
        generator_power = self.linopy_model.variables["generator_power"]

        # Need to include scenario dimension as our system now uses scenarios
        available_capacity_data = [
            [
                [80, 80, 100],  # gen1
                [150, 150, 150],  # gen2 defaults to its nominal power
            ],
        ]

        available_capacity_array = xr.DataArray(
            available_capacity_data,
            coords={
                "scenarios": ["deterministic_scenario"],
                "generators": ["gen1", "gen2"],
                "time": self.time_index,
            },
            dims=["scenarios", "generators", "time"],
        )

        expected_expr = generator_power <= available_capacity_array
        assert_conequal(expected_expr, actual_constraint.lhs <= actual_constraint.rhs)
