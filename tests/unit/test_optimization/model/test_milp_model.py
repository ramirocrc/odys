from datetime import timedelta

import pytest
from linopy.testing import assert_linequal

from odys.domain.entities.fixed_load import FixedLoad
from odys.domain.entities.generator import Generator
from odys.domain.entities.portfolio import AssetPortfolio
from odys.domain.entities.standalone_storage import StandaloneStorage
from odys.domain.scenarios import Scenario
from odys.energy_system import EnergySystem
from odys.optimization.model.dimensions import ModelDimension
from odys.optimization.model.milp_model import EnergyMILPModel
from odys.optimization.model.model_builder import build_model

STANDARD_NOMINAL_POWER = 100.0
STANDARD_VARIABLE_COST = 20.0
STANDARD_CAPACITY = 100.0
STANDARD_MAX_CHARGE_POWER = 50.0
STANDARD_MAX_DISCHARGE_POWER = 50.0
STANDARD_SOC_START = 0.5
STANDARD_DEGRADATION_COST = 5.0
STANDARD_STARTUP_COST = 10.0
STANDARD_SHUTDOWN_COST = 15.0
TIMESTEP = timedelta(hours=1)

DEMAND_PROFILE: list[float] = [50.0, 80.0, 60.0]


@pytest.fixture
def load1() -> FixedLoad:
    return FixedLoad(name="load1")


@pytest.fixture
def generator1() -> Generator:
    return Generator(
        name="gen1",
        nominal_power=STANDARD_NOMINAL_POWER,
        variable_cost=STANDARD_VARIABLE_COST,
    )


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


@pytest.fixture
def storage_with_degradation_cost() -> StandaloneStorage:
    return StandaloneStorage(
        name="storage_with_degradation_cost",
        capacity=STANDARD_CAPACITY,
        max_charge_power=STANDARD_MAX_CHARGE_POWER,
        max_discharge_power=STANDARD_MAX_DISCHARGE_POWER,
        soc_start=STANDARD_SOC_START,
        soc_end=STANDARD_SOC_START,
        degradation_cost=STANDARD_DEGRADATION_COST,
    )


@pytest.fixture
def storage_without_degradation_cost() -> StandaloneStorage:
    return StandaloneStorage(
        name="storage_without_degradation_cost",
        capacity=STANDARD_CAPACITY,
        max_charge_power=STANDARD_MAX_CHARGE_POWER,
        max_discharge_power=STANDARD_MAX_DISCHARGE_POWER,
        soc_start=STANDARD_SOC_START,
        soc_end=STANDARD_SOC_START,
    )


def _build_milp_model(assets: list[Generator | StandaloneStorage], load: FixedLoad) -> EnergyMILPModel:
    energy_system = EnergySystem(
        portfolio=AssetPortfolio(assets=[*assets, load]),
        number_of_steps=len(DEMAND_PROFILE),
        timestep=TIMESTEP,
        scenarios=Scenario(
            available_capacity_profiles={},
            fixed_load_profiles={load.name: DEMAND_PROFILE},
        ),
    )
    return build_model(energy_system.build_parameters())


class TestPerScenarioProfitDegradationCost:
    @pytest.mark.parametrize(
        "storage_fixture_name",
        ["storage_with_degradation_cost", "storage_without_degradation_cost"],
    )
    def test_profit_includes_storage_degradation_cost_term(
        self,
        storage_fixture_name: str,
        request: pytest.FixtureRequest,
        generator1: Generator,
        load1: FixedLoad,
    ) -> None:
        storage: StandaloneStorage = request.getfixturevalue(storage_fixture_name)
        model = _build_milp_model([generator1, storage], load1)

        actual_profit = model.per_scenario_profit()

        generators = model.parameters.generators
        assert generators is not None
        storages = model.parameters.standalone_storages
        assert storages is not None
        timestep_hours = TIMESTEP / timedelta(hours=1)
        expected_profit = -(
            model.vars.generator_power * generators.variable_cost
            + model.vars.generator_startup * generators.startup_cost
            + model.vars.generator_shutdown * generators.shutdown_cost
        ).sum([ModelDimension.Time, ModelDimension.Generators]) - (
            (model.vars.standalone_storage_power_in + model.vars.standalone_storage_power_out)
            * timestep_hours
            * storages.degradation_cost
        ).sum([ModelDimension.Time, ModelDimension.StandaloneStorages])

        assert_linequal(actual_profit, expected_profit)

    def test_profit_requires_no_storages_still_works(self, generator1: Generator, load1: FixedLoad) -> None:
        model = _build_milp_model([generator1], load1)

        actual_profit = model.per_scenario_profit()

        generators = model.parameters.generators
        assert generators is not None
        expected_profit = -(
            model.vars.generator_power * generators.variable_cost
            + model.vars.generator_startup * generators.startup_cost
            + model.vars.generator_shutdown * generators.shutdown_cost
        ).sum([ModelDimension.Time, ModelDimension.Generators])

        assert_linequal(actual_profit, expected_profit)


class TestPerScenarioProfitShutdownCost:
    @pytest.mark.parametrize(
        "generator_fixture_name",
        ["generator_with_shutdown_cost", "generator_without_shutdown_cost"],
    )
    def test_profit_includes_shutdown_cost_term(
        self,
        generator_fixture_name: str,
        request: pytest.FixtureRequest,
        load1: FixedLoad,
    ) -> None:
        generator: Generator = request.getfixturevalue(generator_fixture_name)
        model = _build_milp_model([generator], load1)

        actual_profit = model.per_scenario_profit()

        generators = model.parameters.generators
        assert generators is not None
        expected_profit = -(
            model.vars.generator_power * generators.variable_cost
            + model.vars.generator_startup * generators.startup_cost
            + model.vars.generator_shutdown * generators.shutdown_cost
        ).sum([ModelDimension.Time, ModelDimension.Generators])

        assert_linequal(actual_profit, expected_profit)
