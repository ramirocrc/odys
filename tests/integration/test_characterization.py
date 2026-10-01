"""Characterization tests: pin today's optimal objective values before the architecture refactor.

These values were recorded from the solver at commit 7c67484 (after the timestep-scaling fix), not
derived by hand. They guard the refactor in
`docs/architecture/roadmap.md`: every step must reproduce them. Only the objective value is pinned,
because MILPs often have several optimal dispatches; dispatch itself is covered by the other
integration tests.
"""

import runpy
from collections.abc import Callable
from datetime import timedelta
from pathlib import Path

import pytest

from odys import (
    AllowedTradeDirection,
    AssetPortfolio,
    EnergyMarket,
    EnergySystem,
    FixedLoad,
    FlexibleLoad,
    Generator,
    OptimalDispatchResults,
    Scenario,
    SolverConfig,
    StationaryStorage,
)

EXAMPLES_DIR = Path(__file__).parents[2] / "examples"
EXACT_MIP = SolverConfig(mip_rel_gap=0.0)
DEFAULT_MIP_GAP = 1e-4

HALF_HOUR = timedelta(minutes=30)
ONE_HOUR = timedelta(hours=1)

# Each storage, generator and capacity feature below changes the optimum when removed, so a broken
# constraint shows up as a different objective.
COMMITMENT_LOAD = [45.0, 100.0, 100.0, 20.0, 20.0, 100.0, 100.0, 100.0, 20.0, 100.0, 20.0]
BASELOAD_CAPACITY = [100.0, 100.0, 100.0, 100.0, 100.0, 100.0, 70.0, 100.0, 100.0, 100.0, 100.0]
STORAGE_LOAD = [30.0, 30.0, 50.0, 70.0, 70.0, 40.0, 30.0, 30.0]
STORAGE_PRICES = [20.0, 15.0, 40.0, 90.0, 110.0, 60.0, 25.0, 20.0]
FLEXIBLE_BASE = [20.0, 20.0, 25.0, 25.0, 25.0, 25.0, 20.0, 20.0]

RECORDED_EXAMPLE_OBJECTIVES = {
    "basic_dispatch": -49_500.0,
    "battery_dispatch": -35_750.0,
    "market_arbitrage": -78_400.0,
    "flexible_load_market": -78_600.0,
    "ev_fleet_optimization": 5.21,
    "cvar_market_risk_expected_profit": 448_000.0,
    "cvar_market_risk_penalized_cvar": 866_500.0,
}
RECORDED_UNIT_COMMITMENT_OBJECTIVE = -46_960.0
RECORDED_STORAGE_MARKET_OBJECTIVE = -12_077.865502913086


def _run_example(module_name: str, function_name: str) -> object:
    namespace = runpy.run_path(str(EXAMPLES_DIR / f"{module_name}.py"))
    example: Callable[[], object] = namespace[function_name]
    return example()


def _single_example_result(module_name: str) -> OptimalDispatchResults:
    result = _run_example(module_name, f"run_{module_name}")
    assert isinstance(result, OptimalDispatchResults)
    return result


def _cvar_example_results() -> tuple[OptimalDispatchResults, OptimalDispatchResults]:
    results = _run_example("cvar_market_risk", "run_cvar_market_risk")
    assert isinstance(results, tuple)
    expected_profit, penalized_cvar = results
    assert isinstance(expected_profit, OptimalDispatchResults)
    assert isinstance(penalized_cvar, OptimalDispatchResults)
    return expected_profit, penalized_cvar


def _assert_optimal_with_objective(result: OptimalDispatchResults, expected: float, *, rel: float) -> None:
    assert result.termination_condition == "optimal"
    assert result.objective_value == pytest.approx(expected, rel=rel)


@pytest.mark.parametrize(
    "module_name",
    ["basic_dispatch", "battery_dispatch", "market_arbitrage", "flexible_load_market", "ev_fleet_optimization"],
)
def test_example_objective_is_unchanged(module_name: str) -> None:
    result = _single_example_result(module_name)
    _assert_optimal_with_objective(result, RECORDED_EXAMPLE_OBJECTIVES[module_name], rel=DEFAULT_MIP_GAP)


def test_cvar_example_objectives_are_unchanged() -> None:
    expected_profit, penalized_cvar = _cvar_example_results()
    _assert_optimal_with_objective(
        expected_profit,
        RECORDED_EXAMPLE_OBJECTIVES["cvar_market_risk_expected_profit"],
        rel=DEFAULT_MIP_GAP,
    )
    _assert_optimal_with_objective(
        penalized_cvar,
        RECORDED_EXAMPLE_OBJECTIVES["cvar_market_risk_penalized_cvar"],
        rel=DEFAULT_MIP_GAP,
    )


def _unit_commitment_system() -> EnergySystem:
    baseload = Generator(
        name="baseload",
        nominal_power=100.0,
        variable_cost=20.0,
        min_power=40.0,
        ramp_up=50.0,
        ramp_down=50.0,
        min_up_time=3,
        min_down_time=3,
        startup_cost=300.0,
        shutdown_cost=50.0,
    )
    peaker = Generator(
        name="peaker",
        nominal_power=120.0,
        variable_cost=80.0,
        startup_cost=10.0,
    )
    return EnergySystem(
        portfolio=AssetPortfolio([baseload, peaker, FixedLoad(name="demand")]),
        timestep=ONE_HOUR,
        number_of_steps=len(COMMITMENT_LOAD),
        scenarios=Scenario(
            available_capacity_profiles={"baseload": BASELOAD_CAPACITY},
            fixed_load_profiles={"demand": COMMITMENT_LOAD},
        ),
    )


def _storage_and_market_system() -> EnergySystem:
    battery = StationaryStorage(
        name="battery",
        capacity=40.0,
        max_charge_power=20.0,
        max_discharge_power=15.0,
        efficiency_charging=0.95,
        efficiency_discharging=0.9,
        soc_start=0.5,
        soc_end=0.5,
        soc_min=0.1,
        soc_max=0.9,
        degradation_cost=2.0,
        self_discharge_rate=0.01,
    )
    flexible = FlexibleLoad(name="process", max_increase=10.0, max_decrease=15.0, value_of_consumption=50.0)
    market = EnergyMarket(
        name="grid",
        max_trading_volume_per_step=150.0,
        allowed_trade_direction=AllowedTradeDirection.BUY_AND_SELL,
    )
    return EnergySystem(
        portfolio=AssetPortfolio([battery, flexible, FixedLoad(name="site")]),
        markets=market,
        timestep=HALF_HOUR,
        number_of_steps=len(STORAGE_LOAD),
        scenarios=Scenario(
            fixed_load_profiles={"site": STORAGE_LOAD},
            flexible_load_base_profiles={"process": FLEXIBLE_BASE},
            market_prices={"grid": STORAGE_PRICES},
        ),
    )


@pytest.mark.parametrize(
    ("system_factory", "expected_objective"),
    [
        (_unit_commitment_system, RECORDED_UNIT_COMMITMENT_OBJECTIVE),
        (_storage_and_market_system, RECORDED_STORAGE_MARKET_OBJECTIVE),
    ],
    ids=["unit_commitment", "storage_flexible_load_market_half_hourly"],
)
def test_feature_system_objective_is_unchanged(
    system_factory: Callable[[], EnergySystem],
    expected_objective: float,
) -> None:
    result = system_factory().optimize(solver_config=EXACT_MIP)
    _assert_optimal_with_objective(result, expected_objective, rel=1e-9)
