from datetime import timedelta

import linopy
import pytest
import xarray as xr

from odys.domain.conditions import StorageFinalState, StorageInitialState
from odys.domain.entities.battery import Battery
from odys.domain.entities.battery_storage import BatteryStorage
from odys.domain.entities.fixed_load import FixedLoad
from odys.domain.entities.flexible_load import FlexibleLoad
from odys.domain.entities.generator import Generator
from odys.domain.entities.portfolio import AssetPortfolio
from odys.domain.exceptions import OdysNoResultsError, OdysSolverError
from odys.domain.profiles import FlexibleLoadProfile, LoadProfile
from odys.domain.scenario import Scenario
from odys.energy_system import EnergySystem
from odys.parameters.dimensions import ModelDimension
from odys.results.dispatch import Dispatch
from odys.results.optimization_results import OptimalDispatchResults
from odys.solvers.outcome import SolveOutcome, SolveStatus
from odys.solvers.solver import solve
from odys.solvers.solver_config import SolverConfig


@pytest.fixture
def energy_system_sample() -> EnergySystem:
    generator_1 = Generator(
        name="generator_1",
        nominal_power=100.0,
        variable_cost=20.0,
    )
    generator_2 = Generator(
        name="generator_2",
        nominal_power=150.0,
        variable_cost=25.0,
    )
    battery_1 = BatteryStorage(
        name="battery_1",
        battery=Battery(
            max_charge_power=200.0,
            max_discharge_power=200.0,
            capacity=100.0,
            efficiency_charging=1,
            efficiency_discharging=1,
        ),
    )
    load_1 = FixedLoad(name="load_1")
    portfolio = AssetPortfolio([generator_1, generator_2, battery_1, load_1])

    demand_profile = [50, 75, 100, 125, 150]
    return EnergySystem(
        portfolio=portfolio,
        number_of_steps=len(demand_profile),
        timestep=timedelta(minutes=30),
        scenarios=Scenario(profiles=(LoadProfile(load=load_1, values=demand_profile),)),
        initial_conditions=(StorageInitialState(storage=battery_1, soc=1.0),),
        final_conditions=(StorageFinalState(storage=battery_1, soc=0.5),),
    )


def test_solving_and_termination_condition(energy_system_sample: EnergySystem) -> None:
    result = energy_system_sample.optimize()
    assert result.solver_status is SolveStatus.OK
    assert result.termination_condition == "optimal"


def _never_build_dispatches(_solution: xr.Dataset) -> tuple[Dispatch, ...]:
    msg = "dispatches must not be built without a solution"
    raise AssertionError(msg)


@pytest.fixture
def results_without_solution() -> OptimalDispatchResults:
    outcome = SolveOutcome(
        status=SolveStatus.WARNING,
        termination_condition="infeasible",
        objective_value=None,
        solution=xr.Dataset(),
    )
    return OptimalDispatchResults(outcome, _never_build_dispatches)


def test_results_without_solution_report_the_status(results_without_solution: OptimalDispatchResults) -> None:
    assert results_without_solution.solver_status is SolveStatus.WARNING
    assert results_without_solution.termination_condition == "infeasible"


def test_objective_value_without_solution_raises(results_without_solution: OptimalDispatchResults) -> None:
    with pytest.raises(OdysSolverError, match="No solution available"):
        _ = results_without_solution.objective_value


def test_dataset_without_solution_raises(results_without_solution: OptimalDispatchResults) -> None:
    with pytest.raises(OdysSolverError, match="No solution available"):
        results_without_solution.to_dataset()


def test_dispatch_without_solution_raises(results_without_solution: OptimalDispatchResults) -> None:
    with pytest.raises(OdysSolverError, match="No solution available"):
        _ = results_without_solution.generators


@pytest.mark.parametrize(
    ("status", "termination_condition"),
    [(SolveStatus.WARNING, "infeasible"), (SolveStatus.OK, "time_limit")],
    ids=["infeasible", "time-limit-without-incumbent"],
)
def test_optimize_without_solution_reports_the_status_and_raises_on_access(
    energy_system_sample: EnergySystem,
    monkeypatch: pytest.MonkeyPatch,
    status: SolveStatus,
    termination_condition: str,
) -> None:
    """A solve that ends without a solution (simulated; see the mocking exception in tests/CLAUDE.md)."""

    def stop_without_solution(*_args: object, **_kwargs: object) -> tuple[str, str]:
        return status.value, termination_condition

    monkeypatch.setattr(linopy.Model, "solve", stop_without_solution)

    result = energy_system_sample.optimize()

    assert result.solver_status is status
    assert result.termination_condition == termination_condition
    with pytest.raises(OdysSolverError, match="No solution available"):
        _ = result.generators


@pytest.mark.parametrize(
    ("accessor", "label"),
    [
        ("markets", "market"),
        ("electric_vehicles", "electric vehicle"),
        ("chargers", "charger"),
        ("flexible_loads", "flexible load"),
    ],
    ids=["markets", "electric-vehicles", "chargers", "flexible-loads"],
)
def test_dispatch_of_an_absent_entity_type_raises(
    energy_system_sample: EnergySystem,
    accessor: str,
    label: str,
) -> None:
    result = energy_system_sample.optimize()

    with pytest.raises(OdysNoResultsError, match=f"This model does not contain {label} results"):
        getattr(result, accessor)


FLEXIBLE_LOWER_BOUND = [15.0, 15.0, 15.0]
FLEXIBLE_UPPER_BOUND = [25.0, 25.0, 25.0]
FLEXIBLE_DEMAND = [30.0, 40.0, 50.0]
LOW_FLEXIBLE_LOWER_BOUND = [5.0, 5.0, 5.0]
LOW_FLEXIBLE_UPPER_BOUND = [15.0, 15.0, 15.0]
HIGH_SCENARIO_PROBABILITY = 0.6
LOW_SCENARIO_PROBABILITY = 0.4


@pytest.fixture
def single_scenario_flexible_results() -> OptimalDispatchResults:
    load = FixedLoad(name="load")
    flexible_load = FlexibleLoad(name="flex", value_of_consumption=40.0)
    system = EnergySystem(
        portfolio=AssetPortfolio(
            [Generator(name="gen", nominal_power=100.0, variable_cost=20.0), load, flexible_load],
        ),
        timestep=timedelta(hours=1),
        number_of_steps=len(FLEXIBLE_DEMAND),
        scenarios=Scenario(
            profiles=(
                LoadProfile(load=load, values=FLEXIBLE_DEMAND),
                FlexibleLoadProfile(
                    load=flexible_load,
                    lower_bound=FLEXIBLE_LOWER_BOUND,
                    upper_bound=FLEXIBLE_UPPER_BOUND,
                ),
            ),
        ),
    )
    return system.optimize()


def test_single_scenario_results_have_no_scenario_dimension(
    single_scenario_flexible_results: OptimalDispatchResults,
) -> None:
    assert "scenario" not in single_scenario_flexible_results.to_dataset().dims
    assert "scenario" not in single_scenario_flexible_results.generators.to_dataset().dims
    assert "scenario" not in single_scenario_flexible_results.flexible_loads.to_dataset().dims


def test_single_scenario_flexible_consumption_is_the_upper_bound_when_supply_is_cheaper(
    single_scenario_flexible_results: OptimalDispatchResults,
) -> None:
    flexible_loads = single_scenario_flexible_results.flexible_loads["flex"]

    assert list(flexible_loads.consumption) == pytest.approx(FLEXIBLE_UPPER_BOUND)


def _two_scenario_flexible_system() -> EnergySystem:
    load = FixedLoad(name="load")
    flexible_load = FlexibleLoad(name="flex", value_of_consumption=40.0)
    return EnergySystem(
        portfolio=AssetPortfolio(
            [Generator(name="gen", nominal_power=100.0, variable_cost=20.0), load, flexible_load],
        ),
        timestep=timedelta(hours=1),
        number_of_steps=len(FLEXIBLE_DEMAND),
        scenarios=[
            Scenario(
                name="high",
                probability=HIGH_SCENARIO_PROBABILITY,
                profiles=(
                    LoadProfile(load=load, values=FLEXIBLE_DEMAND),
                    FlexibleLoadProfile(
                        load=flexible_load,
                        lower_bound=FLEXIBLE_LOWER_BOUND,
                        upper_bound=FLEXIBLE_UPPER_BOUND,
                    ),
                ),
            ),
            Scenario(
                name="low",
                probability=LOW_SCENARIO_PROBABILITY,
                profiles=(
                    LoadProfile(load=load, values=FLEXIBLE_DEMAND),
                    FlexibleLoadProfile(
                        load=flexible_load,
                        lower_bound=LOW_FLEXIBLE_LOWER_BOUND,
                        upper_bound=LOW_FLEXIBLE_UPPER_BOUND,
                    ),
                ),
            ),
        ],
    )


def test_multi_scenario_results_keep_the_scenario_dimension() -> None:
    results = _two_scenario_flexible_system().optimize()

    assert ModelDimension.Scenarios in results.to_dataset().dims
    assert ModelDimension.Scenarios in results.flexible_loads.to_dataset().dims


@pytest.mark.parametrize(
    ("scenario", "upper_bound"),
    [("high", FLEXIBLE_UPPER_BOUND), ("low", LOW_FLEXIBLE_UPPER_BOUND)],
    ids=["high", "low"],
)
def test_multi_scenario_flexible_consumption_follows_each_scenarios_upper_bound(
    scenario: str,
    upper_bound: list[float],
) -> None:
    results = _two_scenario_flexible_system().optimize()

    consumption = results.flexible_loads["flex"].to_dataset()["consumption"].sel({ModelDimension.Scenarios: scenario})

    assert list(consumption.to_numpy()) == pytest.approx(upper_bound)


def test_results_with_a_solution_build_the_dispatches_once_from_the_full_solution() -> None:
    problem = _two_scenario_flexible_system().build_problem()
    outcome = solve(problem.model, SolverConfig())
    received: list[xr.Dataset] = []

    def record_dispatches(solution: xr.Dataset) -> tuple[Dispatch, ...]:
        received.append(solution)
        return problem.dispatches(solution)

    OptimalDispatchResults(outcome, record_dispatches)

    assert len(received) == 1
    assert ModelDimension.Scenarios in received[0].dims
