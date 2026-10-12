"""The landing page hero shows these snippets verbatim, so they must run and back up its claims."""

import runpy
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from odys import OptimalDispatchResults

SNIPPETS_DIR = Path(__file__).parents[2] / "docs" / "landing" / "snippets"
NUMBER_OF_SCENARIOS = 12


def _run(snippet: str) -> OptimalDispatchResults:
    result = runpy.run_path(str(SNIPPETS_DIR / f"{snippet}.py"))["result"]
    assert isinstance(result, OptimalDispatchResults)
    return result


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
    price_scenarios = runpy.run_path(str(SNIPPETS_DIR / "prices.py"))["price_scenarios"]
    return float((np.asarray(price_scenarios) @ schedule).mean())


@pytest.mark.parametrize("snippet", ["deterministic", "stochastic", "risk_aware"])
def test_snippet_solves_to_optimality(snippet: str) -> None:
    assert _run(snippet).termination_condition == "optimal"


@pytest.mark.parametrize("snippet", ["stochastic", "risk_aware"])
def test_snippet_commits_to_one_schedule_for_every_scenario(snippet: str) -> None:
    schedules = _schedules(_run(snippet))

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
