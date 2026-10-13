"""Generate the data behind the docs landing page.

Usage:
    uv run --locked python tools/docs/generate_landing_data.py

Output:
    Writes docs/assets/landing/data.json (git-ignored build output), read by
    docs/assets/javascripts/home.js. Every number on the landing page comes from a
    real Odys run here: the hero snippets in tools/docs/landing/snippets/ are executed
    as written, so the code shown on the page is guaranteed to run.
"""

import difflib
import json
import runpy
from datetime import timedelta
from pathlib import Path

import numpy as np
import pandas as pd
from pydantic import ValidationError

from odys import (
    AssetPortfolio,
    EnergySystem,
    FixedLoad,
    Generator,
    LoadProfile,
    OptimalDispatchResults,
    Scenario,
)

TOOLS_DIR = Path(__file__).parent
REPOSITORY_ROOT = TOOLS_DIR.parent.parent
EXAMPLES_DIR = REPOSITORY_ROOT / "examples"
SNIPPETS_DIR = TOOLS_DIR / "landing" / "snippets"
OUTPUT_PATH = REPOSITORY_ROOT / "docs" / "assets" / "landing" / "data.json"

SHOWN_START = "# --8<-- [start:shown]"
SHOWN_END = "# --8<-- [end:shown]"
TABS = ("deterministic", "stochastic", "risk_aware")

# Examples and snippets are standalone scripts, not packages, so they are loaded by path.
_basic = runpy.run_path(str(EXAMPLES_DIR / "basic_dispatch.py"))
_battery = runpy.run_path(str(EXAMPLES_DIR / "battery_dispatch.py"))
_cvar = runpy.run_path(str(EXAMPLES_DIR / "cvar_market_risk.py"))
_ev_fleet = runpy.run_path(str(EXAMPLES_DIR / "ev_fleet_optimization.py"))
_flexible = runpy.run_path(str(EXAMPLES_DIR / "flexible_load_market.py"))
_arbitrage = runpy.run_path(str(EXAMPLES_DIR / "market_arbitrage.py"))
_prices = runpy.run_path(str(SNIPPETS_DIR / "prices.py"))
price_scenarios: list[list[float]] = _prices["price_scenarios"]


def _shown_lines(tab: str) -> list[str]:
    """Return the part of a snippet that the landing page displays."""
    lines = (SNIPPETS_DIR / f"{tab}.py").read_text().splitlines()
    return lines[lines.index(SHOWN_START) + 1 : lines.index(SHOWN_END)]


def _run_snippet(tab: str) -> OptimalDispatchResults:
    result = runpy.run_path(str(SNIPPETS_DIR / f"{tab}.py"))["result"]
    if not isinstance(result, OptimalDispatchResults):
        msg = f"Snippet {tab}.py must define `result` as OptimalDispatchResults"
        raise TypeError(msg)
    return result


def _hourly(series: pd.Series, *, level: str | None = None, key: str | None = None) -> pd.Series:
    """Sum a result series per hour, in numeric hour order.

    Result time labels are strings, so plain grouping would sort them as
    "0", "1", "10", "11", ...; this reorders them as integers.
    """
    if level is not None:
        series = series.xs(key, level=level)
    hourly = series.groupby(level="time", sort=False).sum()
    hourly.index = hourly.index.astype(int)
    return hourly.sort_index()


def _market_schedule(result: OptimalDispatchResults) -> list[float]:
    """Return the committed market position per hour in MW (sell positive).

    The hero markets are stage-fixed, so the schedule is identical in every
    scenario; the first one is taken.
    """
    net_volume = result.markets.to_dataframe()["net_volume"]
    if "scenario" not in net_volume.index.names:
        return _series(_hourly(net_volume))
    first_scenario = net_volume.index.get_level_values("scenario")[0]
    return _series(_hourly(net_volume, level="scenario", key=first_scenario))


def _profit_across_scenarios(schedule: list[float]) -> tuple[float, float]:
    """Return expected and worst-case profit of a schedule over all price scenarios."""
    profits = [float(p) for p in np.asarray(price_scenarios) @ np.asarray(schedule)]
    return round(sum(profits) / len(profits)), round(min(profits))


def _changed_lines(lines: list[str], reference: list[str]) -> list[int]:
    """Return indices of `lines` that are new or different compared to `reference`."""
    matcher = difflib.SequenceMatcher(a=reference, b=lines, autojunk=False)
    return [i for tag, _, _, j1, j2 in matcher.get_opcodes() if tag != "equal" for i in range(j1, j2)]


def _setup_fold(lines: list[str]) -> dict[str, int]:
    """Fold the asset definitions, up to the blank line before ``system = ...``."""
    end = next(i for i, line in enumerate(lines) if line.startswith("system ="))
    return {"start": 0, "end": end - 1}


def _scenarios_fold(lines: list[str]) -> dict[str, int]:
    """Fold the ``scenarios=[...]`` block, which risk_aware.py shares with stochastic.py."""
    start = next(i for i, line in enumerate(lines) if line.startswith("    scenarios=["))
    end = next(i for i in range(start, len(lines)) if lines[i] == "    ],")
    return {"start": start, "end": end + 1}


def _hero() -> dict[str, object]:
    shown = {tab: _shown_lines(tab) for tab in TABS}
    references = {"deterministic": shown["stochastic"], "stochastic": shown["deterministic"]}
    references["risk_aware"] = shown["stochastic"]
    tabs: dict[str, object] = {}
    for tab in TABS:
        schedule = _market_schedule(_run_snippet(tab))
        expected, worst = _profit_across_scenarios(schedule)
        folds = [{**_setup_fold(shown[tab]), "kind": "setup"}]
        if tab == "risk_aware":
            folds.append({**_scenarios_fold(shown[tab]), "kind": "scenarios"})
        tabs[tab] = {
            "code": shown[tab],
            "changed": _changed_lines(shown[tab], references[tab]),
            "folds": folds,
            "schedule": schedule,
            "expected_profit": expected,
            "worst_profit": worst,
        }
    deterministic_forecast = _prices["forecast"]
    return {"price_scenarios": price_scenarios, "forecast": deterministic_forecast, "tabs": tabs}


def _cvar_frontier() -> list[dict[str, float]]:
    """Expected and worst-case profit of the CVaR example, without and with the CVaR term."""
    points = []
    for weight, result in zip((0, 1), _cvar["run_cvar_market_risk"](), strict=True):
        volumes = result.markets.to_dataframe()["sell_volume"]
        scenario_prices: dict[str, dict[str, float]] = _cvar["SCENARIO_PRICES"]
        generation = float(result.generators.power.sum()) / len(scenario_prices)
        profits = []
        for scenario, prices in scenario_prices.items():
            sold = volumes.xs(scenario, level="scenario").groupby(level="market").sum()
            revenue = sum(price * float(sold[market]) for market, price in prices.items())
            profits.append((revenue - _cvar["CCGT_VARIABLE_COST"] * generation) * 24)
        points.append({"cvar_weight": weight, "expected": round(float(np.mean(profits))), "worst": round(min(profits))})
    return points


def _pandas_output() -> str:
    """The README quick example, whose printed result appears on the landing page."""
    generator = Generator(name="gen", nominal_power=100.0, variable_cost=50.0)
    load = FixedLoad(name="demand")
    energy_system = EnergySystem(
        portfolio=AssetPortfolio([generator, load]),
        scenarios=Scenario(profiles=(LoadProfile(load=load, values=[60, 90, 40, 70]),)),
        timestep=timedelta(hours=1),
        number_of_steps=4,
    )
    return str(energy_system.optimize().generators.power)


def _validation_error() -> str:
    try:
        Generator(name="gas", nominal_power=-50.0, variable_cost=40.0)
    except ValidationError as error:
        first_lines = str(error).splitlines()[:3]
        return "\n".join(line.split(" [type=")[0] for line in first_lines)
    msg = "Expected a ValidationError for a negative nominal power"
    raise AssertionError(msg)


def _series(values: object) -> list[float]:
    return [round(float(v), 2) + 0.0 for v in np.asarray(values, dtype=float)]


def _example_thumbnails() -> dict[str, dict[str, object]]:
    """Small real series for each example card: `lines` are drawn as paths, `bars` as columns."""
    basic = _basic["run_basic_dispatch"]().generators.power
    battery = _hourly(_battery["run_battery_dispatch"]().stationary_storages.net_power)
    arbitrage = _arbitrage["run_market_arbitrage"]()
    arbitrage_buy = _hourly(arbitrage.markets.to_dataframe()["buy_volume"])
    flexible_frame = _flexible["run_flexible_load_market"]().flexible_loads.to_dataframe()
    flexible_actual = _hourly(flexible_frame["actual_load"])
    flexible_baseline = flexible_actual - _hourly(flexible_frame["load_adjustment"])
    ev_charging = _hourly(_ev_fleet["run_ev_fleet_optimization"]().electric_vehicles.net_power)
    return {
        "basic_dispatch": {
            "lines": [
                {"values": _series(_hourly(basic, level="generator", key="solar_pv")), "tone": "accent"},
                {"values": _series(_hourly(basic, level="generator", key="ccgt")), "tone": "primary"},
            ],
        },
        "battery_dispatch": {
            "lines": [{"values": _series(_battery["SOLAR_PROFILE"]), "tone": "primary"}],
            "bars": _series(-battery),
        },
        "market_arbitrage": {
            "lines": [
                {"values": _series(_hourly(arbitrage.generators.power)), "tone": "primary"},
                {"values": _series(arbitrage_buy.abs()), "tone": "accent"},
            ],
        },
        "flexible_load_market": {
            "lines": [
                {"values": _series(flexible_baseline), "tone": "muted"},
                {"values": _series(flexible_actual), "tone": "accent"},
            ],
        },
        "ev_fleet_optimization": {
            "lines": [{"values": _series(_ev_fleet["MARKET_PRICES"]), "tone": "primary"}],
            "bars": _series(ev_charging),
        },
        "cvar_market_risk": {"ranges": _cvar_frontier()},
    }


def generate_landing_data() -> None:
    """Run every model behind the landing page and write its data file."""
    data = {
        "hero": _hero(),
        "cvar_frontier": _cvar_frontier(),
        "pandas_output": _pandas_output(),
        "validation_error": _validation_error(),
        "examples": _example_thumbnails(),
    }
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")))
    print(f"  ✓ {OUTPUT_PATH.relative_to(REPOSITORY_ROOT)}")


if __name__ == "__main__":
    print("Generating landing page data...")
    generate_landing_data()
    print("Done!")
