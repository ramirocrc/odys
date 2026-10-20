"""docs/assets/javascripts/home.js draws the landing page figure from this data, so its shape must hold."""

import importlib.util
import runpy
from pathlib import Path
from types import ModuleType

import pytest
from pydantic import BaseModel, ConfigDict

ROOT = Path(__file__).parents[2]
SNIPPET = ROOT / "tools" / "docs" / "landing" / "snippets" / "stochastic.py"
NUMBER_OF_SCENARIOS = 12
HOURS = 24
SCHEDULE_PRECISION = 0.01


class Hero(BaseModel):
    """What home.js reads: hourly prices per scenario (€/MWh) and the committed schedule (MW, sell positive)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    price_scenarios: list[list[float]]
    schedule: list[float]


class LandingData(BaseModel):
    """The whole data file."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    hero: Hero


def _load_generator() -> ModuleType:
    path = ROOT / "tools" / "docs" / "generate_landing_data.py"
    spec = importlib.util.spec_from_file_location("generate_landing_data", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def hero() -> Hero:
    """The generator's output, validated against the shape home.js reads (extra keys are rejected)."""
    return LandingData.model_validate(_load_generator().landing_data()).hero


def _hours_by_mean_price(hero: Hero) -> list[int]:
    """Hours from the cheapest to the dearest, by the price averaged over the scenarios."""
    mean_prices = [sum(prices) / len(prices) for prices in zip(*hero.price_scenarios, strict=True)]
    return sorted(range(len(mean_prices)), key=mean_prices.__getitem__)


def test_landing_data_has_one_hourly_price_series_per_scenario(hero: Hero) -> None:
    assert len(hero.price_scenarios) == NUMBER_OF_SCENARIOS
    assert all(len(prices) == HOURS for prices in hero.price_scenarios)


def test_landing_data_prices_are_the_snippets(hero: Hero) -> None:
    assert hero.price_scenarios == runpy.run_path(str(SNIPPET))["price_scenarios"]


def test_landing_data_schedule_has_one_position_per_hour(hero: Hero) -> None:
    assert len(hero.schedule) == HOURS


def test_landing_data_schedule_sells_in_the_dearest_hour(hero: Hero) -> None:
    assert hero.schedule[_hours_by_mean_price(hero)[-1]] > SCHEDULE_PRECISION


def test_landing_data_schedule_buys_in_the_cheapest_hour(hero: Hero) -> None:
    assert hero.schedule[_hours_by_mean_price(hero)[0]] < -SCHEDULE_PRECISION
