"""Unit tests for the optimization problem and the formulation registry."""

from datetime import timedelta

import pytest

from odys.domain.entities.base import Asset, EnergyEntity
from odys.domain.entities.battery import Battery
from odys.domain.entities.charger import Charger
from odys.domain.entities.electric_vehicle import ElectricVehicle
from odys.domain.entities.fixed_load import FixedLoad
from odys.domain.entities.flexible_load import FlexibleLoad
from odys.domain.entities.generator import Generator
from odys.domain.entities.market import EnergyMarket
from odys.domain.entities.portfolio import AssetPortfolio
from odys.domain.entities.stationary_storage import StationaryStorage
from odys.domain.exceptions import OdysError, OdysValidationError
from odys.domain.profiles import LoadProfile, PriceProfile
from odys.domain.scenario import Scenario
from odys.energy_system import EnergySystem
from odys.optimization.formulations import FORMULATIONS, validate_entities_supported
from odys.optimization.formulations.base import Formulation
from odys.optimization.formulations.charging import ChargingFormulation
from odys.optimization.formulations.electric_vehicle import ElectricVehicleFormulation
from odys.optimization.formulations.energy_market import EnergyMarketFormulation
from odys.optimization.formulations.fixed_load import FixedLoadFormulation
from odys.optimization.formulations.flexible_load import FlexibleLoadFormulation
from odys.optimization.formulations.generator import GeneratorFormulation
from odys.optimization.formulations.stationary_storage import StationaryStorageFormulation
from odys.optimization.model.model_builder import build_model
from odys.optimization.objective_terms.profit import ProfitTermFormulation
from odys.optimization.problem import OptimizationProblem
from odys.parameters.dimensions import ModelDimension

NUMBER_OF_STEPS = 2
DEMAND = [10.0, 20.0]
FLEXIBLE_BASE = [40.0, 50.0]
GENERATOR = Generator(name="gen", nominal_power=500.0, variable_cost=1.0)
FIXED_LOAD = FixedLoad(name="load")
FLEXIBLE_LOAD = FlexibleLoad(name="flex", max_increase=5.0, max_decrease=5.0, value_of_consumption=40.0)
BATTERY = Battery(capacity=10.0, max_charge_power=5.0, max_discharge_power=5.0, soc_start=0.5)
ONE_OF_EACH_ENTITY: tuple[EnergyEntity, ...] = (
    GENERATOR,
    FIXED_LOAD,
    FLEXIBLE_LOAD,
    StationaryStorage(name="storage", battery=BATTERY),
    ElectricVehicle(name="ev", battery=BATTERY, trips=()),
    Charger(name="charger", max_power=5.0),
    EnergyMarket(name="market", max_trading_volume_per_step=50.0),
)


class _UnsupportedHeatPump(Asset):
    """An asset type no formulation models."""


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


def test_problem_holds_one_term_formulation_per_objective_term() -> None:
    problem = _problem(FIXED_LOAD)

    assert [type(term) for term in problem.objective_terms] == [ProfitTermFormulation]


def test_problem_is_built_into_one_model_only() -> None:
    problem = _problem(FLEXIBLE_LOAD)
    build_model(problem)

    with pytest.raises(OdysError, match="already has variables; build a new problem for each model"):
        build_model(problem)


def _problem_with_one_entity_of_each_type() -> OptimizationProblem:
    assets = [entity for entity in ONE_OF_EACH_ENTITY if isinstance(entity, Asset)]
    markets = [entity for entity in ONE_OF_EACH_ENTITY if isinstance(entity, EnergyMarket)]
    return EnergySystem(
        portfolio=AssetPortfolio(assets),
        markets=markets,
        timestep=timedelta(hours=1),
        number_of_steps=NUMBER_OF_STEPS,
        scenarios=Scenario(
            profiles=(
                LoadProfile(load=FIXED_LOAD, values=DEMAND),
                LoadProfile(load=FLEXIBLE_LOAD, values=FLEXIBLE_BASE),
                *(PriceProfile(market=market, values=DEMAND) for market in markets),
            ),
        ),
    ).build_problem()


def test_formulation_dimensions_are_unique_and_distinct_from_scenario_and_time() -> None:
    dimensions = [formulation_type.dimension for formulation_type in FORMULATIONS]

    assert len(set(dimensions)) == len(dimensions)
    assert not {ModelDimension.Scenarios.value, ModelDimension.Time.value} & set(dimensions)


@pytest.mark.parametrize("formulation_type", FORMULATIONS, ids=lambda kind: kind.__name__)
def test_formulation_is_indexed_by_the_entities_of_its_entity_type(formulation_type: type[Formulation]) -> None:
    formulation = _problem_with_one_entity_of_each_type().formulation_of(formulation_type)

    assert formulation is not None
    expected = tuple(entity.name for entity in ONE_OF_EACH_ENTITY if isinstance(entity, formulation_type.entity_type))
    assert formulation.coordinates.dimension == formulation_type.dimension
    assert formulation.coordinates.labels == expected


def test_validate_entities_supported_accepts_every_modelled_entity_type() -> None:
    validate_entities_supported(ONE_OF_EACH_ENTITY)


def test_validate_entities_supported_rejects_an_entity_type_without_formulation() -> None:
    with pytest.raises(OdysValidationError, match=r"HeatPump is not supported by the optimizer: 'heat_pump'"):
        validate_entities_supported((GENERATOR, _UnsupportedHeatPump(name="heat_pump")))
