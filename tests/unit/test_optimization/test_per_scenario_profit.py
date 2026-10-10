from datetime import timedelta

import pytest
from linopy.testing import assert_linequal

from odys.domain.entities.battery import Battery
from odys.domain.entities.fixed_load import FixedLoad
from odys.domain.entities.generator import Generator
from odys.domain.entities.portfolio import AssetPortfolio
from odys.domain.entities.stationary_storage import StationaryStorage
from odys.domain.profiles import LoadProfile
from odys.domain.scenario import Scenario
from odys.energy_system import EnergySystem
from odys.optimization.formulations.base import per_scenario_profit
from odys.optimization.formulations.generator import GeneratorFormulation
from odys.optimization.formulations.stationary_storage import StationaryStorageFormulation
from odys.optimization.model.model_builder import build_model
from odys.optimization.problem import OptimizationProblem
from odys.parameters.dimensions import ModelDimension

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
def storage_with_degradation_cost() -> StationaryStorage:
    return StationaryStorage(
        name="storage_with_degradation_cost",
        battery=Battery(
            capacity=STANDARD_CAPACITY,
            max_charge_power=STANDARD_MAX_CHARGE_POWER,
            max_discharge_power=STANDARD_MAX_DISCHARGE_POWER,
            soc_start=STANDARD_SOC_START,
            soc_end=STANDARD_SOC_START,
            degradation_cost=STANDARD_DEGRADATION_COST,
        ),
    )


@pytest.fixture
def storage_without_degradation_cost() -> StationaryStorage:
    return StationaryStorage(
        name="storage_without_degradation_cost",
        battery=Battery(
            capacity=STANDARD_CAPACITY,
            max_charge_power=STANDARD_MAX_CHARGE_POWER,
            max_discharge_power=STANDARD_MAX_DISCHARGE_POWER,
            soc_start=STANDARD_SOC_START,
            soc_end=STANDARD_SOC_START,
        ),
    )


def _built_problem(assets: list[Generator | StationaryStorage], load: FixedLoad) -> OptimizationProblem:
    energy_system = EnergySystem(
        portfolio=AssetPortfolio(assets=[*assets, load]),
        number_of_steps=len(DEMAND_PROFILE),
        timestep=TIMESTEP,
        scenarios=Scenario(profiles=(LoadProfile(load=load, values=DEMAND_PROFILE),)),
    )
    problem = energy_system.build_problem()
    build_model(problem)
    return problem


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
        storage: StationaryStorage = request.getfixturevalue(storage_fixture_name)
        problem = _built_problem([generator1, storage], load1)

        actual_profit = per_scenario_profit(problem.formulations)

        generators = problem.formulation_of(GeneratorFormulation)
        assert generators is not None
        storages = problem.formulation_of(StationaryStorageFormulation)
        assert storages is not None
        timestep_hours = TIMESTEP / timedelta(hours=1)
        expected_profit = -(
            generators.variables.power * generators.arrays.variable_cost
            + generators.variables.startup * generators.arrays.startup_cost
            + generators.variables.shutdown * generators.arrays.shutdown_cost
        ).sum([ModelDimension.Time, GeneratorFormulation.dimension]) - (
            (storages.variables.power_in + storages.variables.power_out)
            * timestep_hours
            * storages.storage.battery.degradation_cost
        ).sum([ModelDimension.Time, StationaryStorageFormulation.dimension])

        assert_linequal(actual_profit, expected_profit)

    def test_profit_requires_no_storages_still_works(self, generator1: Generator, load1: FixedLoad) -> None:
        problem = _built_problem([generator1], load1)

        actual_profit = per_scenario_profit(problem.formulations)

        generators = problem.formulation_of(GeneratorFormulation)
        assert generators is not None
        expected_profit = -(
            generators.variables.power * generators.arrays.variable_cost
            + generators.variables.startup * generators.arrays.startup_cost
            + generators.variables.shutdown * generators.arrays.shutdown_cost
        ).sum([ModelDimension.Time, GeneratorFormulation.dimension])

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
        problem = _built_problem([generator], load1)

        actual_profit = per_scenario_profit(problem.formulations)

        generators = problem.formulation_of(GeneratorFormulation)
        assert generators is not None
        expected_profit = -(
            generators.variables.power * generators.arrays.variable_cost
            + generators.variables.startup * generators.arrays.startup_cost
            + generators.variables.shutdown * generators.arrays.shutdown_cost
        ).sum([ModelDimension.Time, GeneratorFormulation.dimension])

        assert_linequal(actual_profit, expected_profit)
