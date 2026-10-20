"""The landing page figure is drawn from stochastic.py; these tests check that it backs up the page's claims.

deterministic.py is the point-forecast baseline the stochastic schedule must beat.
"""

import runpy
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from odys import OptimalDispatchResults

SNIPPETS_DIR = Path(__file__).parents[2] / "tools" / "docs" / "landing" / "snippets"
NUMBER_OF_SCENARIOS = 12


def _namespace(snippet: str) -> dict[str, object]:
    return runpy.run_path(str(SNIPPETS_DIR / f"{snippet}.py"))


def _run(snippet: str) -> OptimalDispatchResults:
    result = _namespace(snippet)["result"]
    assert isinstance(result, OptimalDispatchResults)
    return result


def _prices(snippet: str, name: str) -> np.ndarray:
    return np.asarray(_namespace(snippet)[name], dtype=float)


def _schedules(result: OptimalDispatchResults) -> pd.DataFrame:
    """Market net volume per scenario (rows) and hour (columns, numeric order)."""
    net_volume = result.markets.to_dataframe()["net_volume"]
    if "scenario" not in net_volume.index.names:
        net_volume = pd.concat({"forecast": net_volume}, names=["scenario"])
    schedules = (
        net_volume
        .droplevel("market")
        .reset_index()
        .pivot_table(
            index="scenario",
            columns="time",
            values="net_volume",
        )
    )
    return schedules.reindex(columns=sorted(schedules.columns, key=int))


def _expected_profit(schedule: np.ndarray) -> float:
    return float((_prices("stochastic", "price_scenarios") @ schedule).mean())


@pytest.mark.parametrize("snippet", ["deterministic", "stochastic"])
def test_snippet_solves_to_optimality(snippet: str) -> None:
    assert _run(snippet).termination_condition == "optimal"


def test_stochastic_snippet_commits_to_one_schedule_for_every_scenario() -> None:
    schedules = _schedules(_run("stochastic"))

    assert len(schedules) == NUMBER_OF_SCENARIOS
    np.testing.assert_allclose(
        schedules.to_numpy(),
        np.tile(schedules.iloc[0], (NUMBER_OF_SCENARIOS, 1)),
        atol=1e-6,
    )


def test_stochastic_schedule_beats_the_point_forecast_in_expectation() -> None:
    deterministic = _schedules(_run("deterministic")).iloc[0].to_numpy()
    stochastic = _schedules(_run("stochastic")).iloc[0].to_numpy()

    assert not np.allclose(deterministic, stochastic)
    assert _expected_profit(stochastic) > _expected_profit(deterministic)


def test_deterministic_forecast_is_one_of_the_price_scenarios() -> None:
    forecast = _prices("deterministic", "forecast")

    assert any(np.array_equal(forecast, scenario) for scenario in _prices("stochastic", "price_scenarios"))
