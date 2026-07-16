from datetime import timedelta

import pytest
from linopy.testing import assert_linequal

from odys.domain.entities.generator import Generator
from odys.domain.entities.load import Load
from odys.domain.entities.portfolio import AssetPortfolio
from odys.domain.scenarios import Scenario
from odys.energy_system import EnergySystem
from odys.optimization.model.milp_model import EnergyMILPModel
from odys.optimization.model.model_builder import build_model
from odys.optimization.model.sets import ModelDimension

STANDARD_NOMINAL_POWER = 100.0
STANDARD_VARIABLE_COST = 20.0
STANDARD_STARTUP_COST = 10.0
STANDARD_SHUTDOWN_COST = 15.0

DEMAND_PROFILE: list[float] = [50.0, 80.0, 60.0]


@pytest.fixture
def load1() -> Load:
    return Load(name="load1")


@pytest.fixture
def generator_with_shutdown_cost() -> Generator:
    return Generator(
        name="gen_with_shutdown_cost",
        nominal_power=STANDARD_NOMINAL_POWER,
        variable_cost=STANDARD_VARIABLE_COST,
        startup_cost=STANDARD_STARTUP_COST,
        shutdown_cost=STANDARD_SHUTDOWN_COST,
    )


@pytest.fixture
def generator_without_shutdown_cost() -> Generator:
    return Generator(
        name="gen_without_shutdown_cost",
        nominal_power=STANDARD_NOMINAL_POWER,
        variable_cost=STANDARD_VARIABLE_COST,
        startup_cost=STANDARD_STARTUP_COST,
    )


def _build_milp_model(generators: list[Generator], load: Load) -> EnergyMILPModel:
    energy_system = EnergySystem(
        portfolio=AssetPortfolio(assets=[*generators, load]),
        number_of_steps=len(DEMAND_PROFILE),
        timestep=timedelta(hours=1),
        scenarios=Scenario(
            available_capacity_profiles={},
            load_profiles={load.name: DEMAND_PROFILE},
        ),
    )
    return build_model(energy_system.build_parameters())


class TestPerScenarioProfitShutdownCost:
    @pytest.mark.parametrize(
        "generator_fixture_name",
        ["generator_with_shutdown_cost", "generator_without_shutdown_cost"],
    )
    def test_profit_includes_shutdown_cost_term(
        self,
        generator_fixture_name: str,
        request: pytest.FixtureRequest,
        load1: Load,
    ) -> None:
        generator: Generator = request.getfixturevalue(generator_fixture_name)
        model = _build_milp_model([generator], load1)

        actual_profit = model.per_scenario_profit()

        expected_profit = -(
            model.generator_power * model.parameters.generators.variable_cost
            + model.generator_startup * model.parameters.generators.startup_cost
            + model.generator_shutdown * model.parameters.generators.shutdown_cost.fillna(0.0)
        ).sum([ModelDimension.Time, ModelDimension.Generators])

        assert_linequal(actual_profit, expected_profit)
