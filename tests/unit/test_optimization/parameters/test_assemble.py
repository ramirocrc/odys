"""Tests for registry-driven parameter assembly (G11a)."""

from datetime import timedelta

from odys import AssetPortfolio, EnergySystem, FixedLoad, Generator, Scenario
from odys.domain.entities.market import EnergyMarket
from odys.domain.objective import Objective, ProfitTerm
from odys.domain.scenarios import StochasticScenario
from odys.optimization.model.registry import AssetRegistry
from odys.optimization.parameters.assemble import build_energy_system_parameters
from odys.optimization.parameters.build_context import ParamBuildContext
from odys.optimization.parameters.generator_parameters import GeneratorParameters
from odys.optimization.parameters.market_parameters import MarketParameters

N_STEPS = 2
TIMESTEP = timedelta(hours=1)


def _empty_ctx(**overrides: object) -> ParamBuildContext:
    base: dict[str, object] = {
        "number_of_steps": 4,
        "timestep": timedelta(hours=1),
        "generators": (),
        "standalone_storages": (),
        "flexible_loads": (),
        "chargers": (),
        "electric_vehicles": (),
        "markets": (),
        "scenarios": (),
        "objective": Objective(profit=ProfitTerm(weight=1.0)),
    }
    base.update(overrides)
    return ParamBuildContext(**base)  # type: ignore[arg-type]


def test_build_asset_parameter_blocks_covers_all_registry_attrs() -> None:
    blocks = AssetRegistry.build_asset_parameter_blocks(_empty_ctx())
    expected = {member.spec.parameters_attr for member in AssetRegistry}
    assert set(blocks) == expected
    assert all(block.is_empty for block in blocks.values())


def test_build_energy_system_parameters_empty_assets() -> None:
    ctx = _empty_ctx(scenarios=(StochasticScenario(name="s1", probability=1.0),))
    params = build_energy_system_parameters(ctx)
    assert params.generators.is_empty
    assert params.markets.is_empty
    assert params.timestep == timedelta(hours=1)
    assert list(params.scenarios.scenario_index.values) == ["s1"]


def test_build_energy_system_parameters_with_generator_and_market() -> None:
    gen = Generator(name="g1", nominal_power=100.0, variable_cost=10.0)
    market = EnergyMarket(name="m1", max_trading_volume_per_step=50.0)
    ctx = _empty_ctx(
        generators=(gen,),
        markets=(market,),
        scenarios=(StochasticScenario(name="s1", probability=1.0),),
    )
    params = build_energy_system_parameters(ctx)
    assert isinstance(params.generators, GeneratorParameters)
    assert isinstance(params.markets, MarketParameters)
    assert not params.generators.is_empty
    assert not params.markets.is_empty
    assert list(params.generators.index.values) == ["g1"]
    assert list(params.markets.index.values) == ["m1"]


def test_energy_system_build_parameters_uses_assembly() -> None:
    gen = Generator(name="g1", nominal_power=100.0, variable_cost=10.0)
    load = FixedLoad(name="load1")
    system = EnergySystem(
        portfolio=AssetPortfolio(assets=[gen, load]),
        timestep=TIMESTEP,
        number_of_steps=N_STEPS,
        scenarios=Scenario(fixed_load_profiles={"load1": [10.0] * N_STEPS}),
    )
    params = system.build_parameters()
    assert not params.generators.is_empty
    assert list(params.generators.index.values) == ["g1"]
    assert params.objective.profit.weight == 1.0
