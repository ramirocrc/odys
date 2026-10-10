"""Tests that every formulation builds its own dispatch from a solved model."""

from datetime import timedelta

import pandas as pd
import pytest
import xarray as xr

from odys import (
    AssetPortfolio,
    Battery,
    Charger,
    ElectricVehicle,
    EnergyMarket,
    EnergySystem,
    FixedLoad,
    FlexibleLoad,
    Generator,
    LoadProfile,
    PriceProfile,
    Scenario,
    StationaryStorage,
)
from odys.optimization.formulations.charging import ChargingFormulation
from odys.optimization.formulations.electric_vehicle import ElectricVehicleFormulation
from odys.optimization.formulations.energy_market import EnergyMarketFormulation
from odys.optimization.formulations.flexible_load import FlexibleLoadFormulation
from odys.optimization.model.model_builder import build_model
from odys.optimization.problem import OptimizationProblem
from odys.results.dispatch import (
    ChargerDispatch,
    Dispatch,
    ElectricVehicleDispatch,
    FlexibleLoadDispatch,
    GeneratorDispatch,
    MarketDispatch,
    StationaryStorageDispatch,
)
from odys.solvers.solver import solve
from odys.solvers.solver_config import SolverConfig

DEMAND = [40.0, 60.0, 50.0]
FLEXIBLE_BASE = [10.0, 10.0, 10.0]
PRICES = [30.0, 80.0, 50.0]

EV_CAPACITY = 50.0
EV_SOC_START = 0.5
EV_SOC_END = 0.7
EV_DEGRADATION_COST = 100.0
EXPECTED_EV_CHARGED_ENERGY = (EV_SOC_END - EV_SOC_START) * EV_CAPACITY
FLEXIBLE_ADJUSTMENT_LIMIT = 5.0
EXPECTED_FLEXIBLE_ACTUAL_LOAD = [15.0, 5.0, 5.0]

FIXED_LOAD = FixedLoad(name="load")
FLEXIBLE_LOAD = FlexibleLoad(
    name="flex",
    max_increase=FLEXIBLE_ADJUSTMENT_LIMIT,
    max_decrease=FLEXIBLE_ADJUSTMENT_LIMIT,
    value_of_consumption=40.0,
)
MARKET = EnergyMarket(name="grid", max_trading_volume_per_step=100.0)

EXPECTED_SERIES: dict[type[Dispatch], tuple[str, ...]] = {
    GeneratorDispatch: ("power", "status", "startup", "shutdown"),
    StationaryStorageDispatch: ("net_power", "soc", "charge_mode"),
    ElectricVehicleDispatch: ("net_power", "soc", "charge_mode"),
    ChargerDispatch: ("assignment", "power"),
    MarketDispatch: ("sell_volume", "buy_volume", "net_volume"),
    FlexibleLoadDispatch: ("load_adjustment", "actual_load"),
}


@pytest.fixture(scope="module")
def solved_problem() -> tuple[OptimizationProblem, xr.Dataset]:
    portfolio = AssetPortfolio(
        [
            Generator(name="gen", nominal_power=100.0, variable_cost=20.0),
            StationaryStorage(
                name="storage",
                battery=Battery(capacity=20.0, max_charge_power=10.0, max_discharge_power=10.0, soc_start=0.5),
            ),
            ElectricVehicle(
                name="ev",
                battery=Battery(
                    capacity=EV_CAPACITY,
                    max_charge_power=11.0,
                    max_discharge_power=11.0,
                    soc_start=EV_SOC_START,
                    soc_end=EV_SOC_END,
                    degradation_cost=EV_DEGRADATION_COST,
                ),
                trips=(),
            ),
            Charger(name="charger", max_power=11.0),
            FIXED_LOAD,
            FLEXIBLE_LOAD,
        ],
    )
    system = EnergySystem(
        portfolio=portfolio,
        timestep=timedelta(hours=1),
        number_of_steps=len(DEMAND),
        markets=MARKET,
        scenarios=Scenario(
            profiles=(
                LoadProfile(load=FIXED_LOAD, values=DEMAND),
                LoadProfile(load=FLEXIBLE_LOAD, values=FLEXIBLE_BASE),
                PriceProfile(market=MARKET, values=PRICES),
            ),
        ),
    )
    problem = system.build_problem()
    outcome = solve(build_model(problem), SolverConfig())
    assert outcome.has_solution
    return problem, outcome.solution


def _dispatch_of(dispatches: tuple[Dispatch, ...], kind: type[Dispatch]) -> Dispatch:
    return next(dispatch for dispatch in dispatches if isinstance(dispatch, kind))


def test_problem_dispatches_has_one_dispatch_per_entity_type_and_none_for_fixed_loads(
    solved_problem: tuple[OptimizationProblem, xr.Dataset],
) -> None:
    problem, solution = solved_problem

    dispatches = problem.dispatches(solution)

    assert sorted(type(dispatch).__name__ for dispatch in dispatches) == sorted(
        kind.__name__ for kind in EXPECTED_SERIES
    )


@pytest.mark.parametrize("kind", list(EXPECTED_SERIES), ids=lambda kind: kind.__name__)
def test_dispatch_series_are_complete_pandas_series(
    solved_problem: tuple[OptimizationProblem, xr.Dataset],
    kind: type[Dispatch],
) -> None:
    problem, solution = solved_problem
    dispatch = _dispatch_of(problem.dispatches(solution), kind)

    assert set(dispatch.to_dataset().data_vars) == set(EXPECTED_SERIES[kind])
    for name in EXPECTED_SERIES[kind]:
        series = getattr(dispatch, name)
        assert isinstance(series, pd.Series)
        assert series.name == name
        assert not series.isna().any()


def test_charger_power_is_assignment_times_vehicle_charging_power(
    solved_problem: tuple[OptimizationProblem, xr.Dataset],
) -> None:
    problem, solution = solved_problem
    chargers = problem.formulation_of(ChargingFormulation)
    assert chargers is not None
    dispatch = chargers.dispatch(solution)

    expected = (solution[ChargingFormulation.assignment_name] * solution[ElectricVehicleFormulation.power_in_name]).sum(
        ElectricVehicleFormulation.dimension,
    )
    xr.testing.assert_allclose(dispatch.to_dataset()["power"], expected)


def test_charger_power_delivers_the_energy_the_vehicle_must_gain(
    solved_problem: tuple[OptimizationProblem, xr.Dataset],
) -> None:
    """Degradation above any arbitrage margin, so the vehicle charges only what its end SOC requires."""
    problem, solution = solved_problem
    chargers = problem.formulation_of(ChargingFormulation)
    assert chargers is not None

    charged_energy = float(chargers.dispatch(solution).to_dataset()["power"].sum())

    assert charged_energy == pytest.approx(EXPECTED_EV_CHARGED_ENERGY)


def test_flexible_load_actual_load_is_base_plus_adjustment(
    solved_problem: tuple[OptimizationProblem, xr.Dataset],
) -> None:
    problem, solution = solved_problem
    flexible_loads = problem.formulation_of(FlexibleLoadFormulation)
    assert flexible_loads is not None
    dispatch = flexible_loads.dispatch(solution)

    actual_load = dispatch.to_dataset()["actual_load"].squeeze()

    assert list(actual_load.to_numpy()) == pytest.approx(EXPECTED_FLEXIBLE_ACTUAL_LOAD)


def test_market_net_volume_is_sell_minus_buy(solved_problem: tuple[OptimizationProblem, xr.Dataset]) -> None:
    problem, solution = solved_problem
    markets = problem.formulation_of(EnergyMarketFormulation)
    assert markets is not None
    dispatch = markets.dispatch(solution)

    expected = solution[EnergyMarketFormulation.sell_volume_name] - solution[EnergyMarketFormulation.buy_volume_name]
    xr.testing.assert_allclose(dispatch.to_dataset()["net_volume"], expected)
