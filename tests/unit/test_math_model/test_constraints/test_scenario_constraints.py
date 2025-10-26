import logging
from datetime import timedelta

import linopy
import pytest
import xarray as xr
from linopy.testing import assert_conequal

from optimes._math_model.model_builder import EnergyAlgebraicModelBuilder
from optimes._math_model.model_components.variables import ModelVariable
from optimes.energy_system_models.assets.generator import PowerGenerator
from optimes.energy_system_models.assets.load import Load
from optimes.energy_system_models.assets.portfolio import AssetPortfolio
from optimes.energy_system_models.assets.storage import Battery
from optimes.energy_system_models.scenarios import Scenario, StochasticScenario
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
def load1() -> Load:
    return Load(name="load1")


@pytest.fixture
def asset_portfolio_sample(
    generator1: PowerGenerator,
    generator2: PowerGenerator,
    battery1: Battery,
    load1: Load,
) -> AssetPortfolio:
    portfolio = AssetPortfolio()
    portfolio.add_asset(generator1)
    portfolio.add_asset(generator2)
    portfolio.add_asset(battery1)
    portfolio.add_asset(load1)
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
        timestep=timedelta(hours=1),
        number_of_steps=len(demand_profile_sample),
        power_unit=PowerUnit.MegaWatt,
        scenarios=Scenario(
            available_capacity_profiles={
                "gen1": [80, 80, 100],
            },
            load_profiles={
                "load1": demand_profile_sample,
            },
        ),
    )


@pytest.fixture
def energy_system_with_multiple_scenarios(
    asset_portfolio_sample: AssetPortfolio,
    demand_profile_sample: list[float],
) -> ValidatedEnergySystem:
    scenarios = [
        StochasticScenario(
            name="scenario_1",
            probability=0.6,
            available_capacity_profiles={
                "gen1": [80, 80, 100],
                "gen2": [150, 150, 150],
            },
            load_profiles={
                "load1": demand_profile_sample,
            },
        ),
        StochasticScenario(
            name="scenario_2",
            probability=0.4,
            available_capacity_profiles={
                "gen1": [90, 70, 80],
                "gen2": [120, 140, 130],
            },
            load_profiles={
                "load1": demand_profile_sample,
            },
        ),
    ]
    return ValidatedEnergySystem(
        portfolio=asset_portfolio_sample,
        timestep=timedelta(hours=1),
        number_of_steps=len(demand_profile_sample),
        power_unit=PowerUnit.MegaWatt,
        scenarios=scenarios,
        enforce_non_anticipativity=True,
    )


@pytest.fixture
def linopy_model(energy_system_sample: ValidatedEnergySystem) -> linopy.Model:
    model_builder = EnergyAlgebraicModelBuilder(energy_system_sample.parameters)
    energy_milp_model = model_builder.build()
    return energy_milp_model.linopy_model


@pytest.fixture
def linopy_model_with_non_anticipativity(energy_system_with_multiple_scenarios: ValidatedEnergySystem) -> linopy.Model:
    model_builder = EnergyAlgebraicModelBuilder(energy_system_with_multiple_scenarios.parameters)
    energy_milp_model = model_builder.build()
    return energy_milp_model.linopy_model


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

        generation_total = self.linopy_model.variables["generator_power"].sum("generator")
        discharge_total = self.linopy_model.variables["battery_power_out"].sum("battery")
        charge_total = self.linopy_model.variables["battery_power_in"].sum("battery")

        # Create demand array with the proper dimensions to match actual constraint
        demand_data = [
            [
                self.demand_profile_sample,  # load1 profile
            ],
        ]
        demand_array = xr.DataArray(
            demand_data,
            coords={
                "scenario": ["deterministic_scenario"],
                "load": ["load1"],
                "time": [str(t) for t in self.time_index],
            },
            dims=["scenario", "load", "time"],
        )

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
                "scenario": ["deterministic_scenario"],
                "generator": ["gen1", "gen2"],
                "time": self.time_index,
            },
            dims=["scenario", "generator", "time"],
        )

        expected_expr = generator_power <= available_capacity_array
        assert_conequal(expected_expr, actual_constraint.lhs <= actual_constraint.rhs)


class TestNonAnticipativityConstraints:
    @pytest.fixture(autouse=True)
    def setup(
        self,
        linopy_model_with_non_anticipativity: linopy.Model,
        time_index: list[int],
    ) -> None:
        self.linopy_model = linopy_model_with_non_anticipativity
        self.time_index = time_index

    def test_non_anticipativity_constraints(self) -> None:
        for variable in ModelVariable:
            # Only test constraints for variables that exist in the model
            if variable.var_name in self.linopy_model.variables:
                constraint_name = f"non_anticipativity_{variable.var_name}_constraint"
                actual_constraint = self.linopy_model.constraints[constraint_name]

                linopy_var = self.linopy_model.variables[variable.var_name]
                first_scenario_var = linopy_var.isel(scenario=0)
                expected_expr = linopy_var - first_scenario_var == 0
                assert_conequal(expected_expr, actual_constraint.lhs == actual_constraint.rhs)
