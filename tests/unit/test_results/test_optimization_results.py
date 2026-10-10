from datetime import timedelta

import linopy
import pytest
import xarray as xr

from odys.domain.entities.battery import Battery
from odys.domain.entities.fixed_load import FixedLoad
from odys.domain.entities.generator import Generator
from odys.domain.entities.portfolio import AssetPortfolio
from odys.domain.entities.stationary_storage import StationaryStorage
from odys.domain.exceptions import OdysSolverError
from odys.domain.profiles import LoadProfile
from odys.domain.scenario import Scenario
from odys.energy_system import EnergySystem
from odys.results.optimization_results import OptimalDispatchResults
from odys.solvers.outcome import SolveOutcome, SolveStatus


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
    battery_1 = StationaryStorage(
        name="battery_1",
        battery=Battery(
            max_charge_power=200.0,
            max_discharge_power=200.0,
            capacity=100.0,
            efficiency_charging=1,
            efficiency_discharging=1,
            soc_start=1.0,
            soc_end=0.5,
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
    )


def test_solving_and_termination_condition(energy_system_sample: EnergySystem) -> None:
    result = energy_system_sample.optimize()
    assert result.solver_status is SolveStatus.OK
    assert result.termination_condition == "optimal"


@pytest.fixture
def results_without_solution(energy_system_sample: EnergySystem) -> OptimalDispatchResults:
    outcome = SolveOutcome(
        status=SolveStatus.WARNING,
        termination_condition="infeasible",
        objective_value=None,
        solution=xr.Dataset(),
    )
    return OptimalDispatchResults(outcome, energy_system_sample.build_problem())


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
)
def test_optimize_without_solution_reports_the_status_and_raises_on_access(
    energy_system_sample: EnergySystem,
    monkeypatch: pytest.MonkeyPatch,
    status: SolveStatus,
    termination_condition: str,
) -> None:
    def stop_without_solution(*_args: object, **_kwargs: object) -> tuple[str, str]:
        return status.value, termination_condition

    monkeypatch.setattr(linopy.Model, "solve", stop_without_solution)

    result = energy_system_sample.optimize()

    assert result.solver_status is status
    assert result.termination_condition == termination_condition
    with pytest.raises(OdysSolverError, match="No solution available"):
        _ = result.generators
