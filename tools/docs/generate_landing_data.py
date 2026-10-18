"""Generate the data behind the docs landing page.

Usage:
    uv run --locked python tools/docs/generate_landing_data.py

Output:
    Writes docs/assets/landing/data.json (git-ignored build output), read by
    docs/assets/javascripts/home.js. Every number in the landing page hero comes from
    a real Odys run here: the hero snippets in tools/docs/landing/snippets/ are executed
    as written, so the code shown on the page is guaranteed to run.
"""

import difflib
import json
import runpy
from pathlib import Path

import numpy as np
import pandas as pd

from odys import OptimalDispatchResults

TOOLS_DIR = Path(__file__).parent
REPOSITORY_ROOT = TOOLS_DIR.parent.parent
SNIPPETS_DIR = TOOLS_DIR / "landing" / "snippets"
OUTPUT_PATH = REPOSITORY_ROOT / "docs" / "assets" / "landing" / "data.json"

SHOWN_START = "# --8<-- [start:shown]"
SHOWN_END = "# --8<-- [end:shown]"
TABS = ("deterministic", "stochastic")

# Snippets are standalone scripts, not packages, so they are loaded by path.
_snippets = {tab: runpy.run_path(str(SNIPPETS_DIR / f"{tab}.py")) for tab in TABS}
price_scenarios: list[list[float]] = _snippets["stochastic"]["price_scenarios"]


def _shown_lines(tab: str) -> list[str]:
    """Return the part of a snippet that the landing page displays."""
    lines = (SNIPPETS_DIR / f"{tab}.py").read_text().splitlines()
    return lines[lines.index(SHOWN_START) + 1 : lines.index(SHOWN_END)]


def _snippet_result(tab: str) -> OptimalDispatchResults:
    result = _snippets[tab]["result"]
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


def _changed_lines(lines: list[str], reference: list[str]) -> list[int]:
    """Return indices of `lines` that are new or different compared to `reference`."""
    matcher = difflib.SequenceMatcher(a=reference, b=lines, autojunk=False)
    return [i for tag, _, _, j1, j2 in matcher.get_opcodes() if tag != "equal" for i in range(j1, j2)]


def _setup_fold(lines: list[str]) -> dict[str, int]:
    """Fold the asset definitions, up to the blank line before the first commented block."""
    end = next(i for i, line in enumerate(lines) if line.startswith("# "))
    return {"start": 0, "end": end - 1}


def _data_fold(lines: list[str], name: str) -> dict[str, int]:
    """Fold the literal price data assigned to `name`, which spans one line or ends at a lone ``]``."""
    start = next(i for i, line in enumerate(lines) if line.startswith(f"{name} = ["))
    end = start if lines[start].endswith("]") else lines.index("]", start)
    return {"start": start, "end": end + 1}


def _hero() -> dict[str, object]:
    shown = {tab: _shown_lines(tab) for tab in TABS}
    references = {"deterministic": shown["stochastic"], "stochastic": shown["deterministic"]}
    price_data = {"deterministic": "forecast", "stochastic": "price_scenarios"}
    tabs: dict[str, object] = {}
    for tab in TABS:
        schedule = _market_schedule(_snippet_result(tab))
        folds = [
            {**_setup_fold(shown[tab]), "kind": "setup"},
            {**_data_fold(shown[tab], price_data[tab]), "kind": price_data[tab]},
        ]
        tabs[tab] = {
            "code": shown[tab],
            "changed": _changed_lines(shown[tab], references[tab]),
            "folds": folds,
            "schedule": schedule,
        }
    deterministic_forecast = _snippets["deterministic"]["forecast"]
    return {"price_scenarios": price_scenarios, "forecast": deterministic_forecast, "tabs": tabs}


def _series(values: object) -> list[float]:
    return [round(float(v), 2) + 0.0 for v in np.asarray(values, dtype=float)]


def generate_landing_data() -> None:
    """Run every model behind the landing page and write its data file."""
    data = {
        "hero": _hero(),
    }
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")))
    print(f"  ✓ {OUTPUT_PATH.relative_to(REPOSITORY_ROOT)}")


if __name__ == "__main__":
    print("Generating landing page data...")
    generate_landing_data()
    print("Done!")
