"""Unit tests for the optimization problem and the formulation registry."""

from datetime import timedelta

import pytest

from odys.domain.entities.fixed_load import FixedLoad
from odys.domain.entities.flexible_load import FlexibleLoad
from odys.domain.entities.generator import Generator
from odys.domain.entities.portfolio import AssetPortfolio
from odys.domain.exceptions import OdysError
from odys.domain.profiles import LoadProfile
from odys.domain.scenario import Scenario
from odys.energy_system import EnergySystem
from odys.optimization.formulations import FORMULATIONS
from odys.optimization.formulations.charging import ChargingFormulation
from odys.optimization.formulations.electric_vehicle import ElectricVehicleFormulation
from odys.optimization.formulations.energy_market import EnergyMarketFormulation
from odys.optimization.formulations.fixed_load import FixedLoadFormulation
from odys.optimization.formulations.flexible_load import FlexibleLoadFormulation
from odys.optimization.formulations.generator import GeneratorFormulation
from odys.optimization.formulations.stationary_storage import StationaryStorageFormulation
from odys.optimization.model.model_builder import build_model
from odys.optimization.problem import OptimizationProblem

NUMBER_OF_STEPS = 2
DEMAND = [10.0, 20.0]
FLEXIBLE_BASE = [40.0, 50.0]
GENERATOR = Generator(name="gen", nominal_power=500.0, variable_cost=1.0)
FIXED_LOAD = FixedLoad(name="load")
FLEXIBLE_LOAD = FlexibleLoad(name="flex", max_increase=5.0, max_decrease=5.0, value_of_consumption=40.0)


def _problem(*loads: FixedLoad | FlexibleLoad) -> OptimizationProblem:
    return EnergySystem(
        portfolio=AssetPortfolio([GENERATOR, *loads]),
        timestep=timedelta(hours=1),
        number_of_steps=NUMBER_OF_STEPS,
        scenarios=Scenario(
            profiles=tuple(
                LoadProfile(load=load, values=DEMAND if isinstance(load, FixedLoad) else FLEXIBLE_BASE)
                for load in loads
            ),
        ),
    ).build_problem()


def test_formulations_follow_the_power_balance_order() -> None:
    assert (
        GeneratorFormulation,
        EnergyMarketFormulation,
        FixedLoadFormulation,
        FlexibleLoadFormulation,
        StationaryStorageFormulation,
        ElectricVehicleFormulation,
        ChargingFormulation,
    ) == FORMULATIONS


def test_problem_builds_one_formulation_per_present_entity_type_in_registry_order() -> None:
    problem = _problem(FLEXIBLE_LOAD, FIXED_LOAD)

    assert [type(formulation) for formulation in problem.formulations] == [
        GeneratorFormulation,
        FixedLoadFormulation,
        FlexibleLoadFormulation,
    ]


def test_problem_does_not_build_formulations_for_absent_entity_types() -> None:
    problem = _problem(FIXED_LOAD)

    assert problem.formulation_of(FixedLoadFormulation) is not None
    assert problem.formulation_of(FlexibleLoadFormulation) is None


def test_problem_exposes_the_legacy_context_and_objective() -> None:
    problem = _problem(FIXED_LOAD)

    assert problem.context is problem.legacy.context
    assert problem.objective is problem.legacy.objective


def test_problem_is_built_into_one_model_only() -> None:
    problem = _problem(FLEXIBLE_LOAD)
    build_model(problem)

    with pytest.raises(OdysError, match="already has variables; build a new problem for each model"):
        build_model(problem)
