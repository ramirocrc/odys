"""Generate the data behind the docs landing page.

Usage:
    uv run --locked python tools/docs/generate_landing_data.py

Output:
    Writes docs/assets/landing/data.json (git-ignored build output), read by
    docs/assets/javascripts/home.js. Every number in the landing page figure comes from
    a real Odys run here: the stochastic hero snippet in tools/docs/landing/snippets/ is
    executed as written.
"""

import json
import runpy
from pathlib import Path

import numpy as np

from odys import OptimalDispatchResults

TOOLS_DIR = Path(__file__).parent
REPOSITORY_ROOT = TOOLS_DIR.parent.parent
SNIPPET_PATH = TOOLS_DIR / "landing" / "snippets" / "stochastic.py"
OUTPUT_PATH = REPOSITORY_ROOT / "docs" / "assets" / "landing" / "data.json"


def _market_schedule(result: OptimalDispatchResults) -> list[float]:
    """Return the committed market position per hour in MW (sell positive).

    The market is stage-fixed, so the schedule is identical in every scenario; the first
    one is taken. Result time labels are strings, so plain sorting would order them as
    "0", "1", "10", "11", ...; this orders them as integers.
    """
    net_volume = result.markets.to_dataframe()["net_volume"]
    first_scenario = net_volume.index.get_level_values("scenario")[0]
    hourly = net_volume.xs(first_scenario, level="scenario").groupby(level="time", sort=False).sum()
    hourly.index = hourly.index.astype(int)
    return _series(hourly.sort_index())


def _series(values: object) -> list[float]:
    """Round to cents for the JSON file; adding 0.0 turns -0.0 into 0.0."""
    return [round(float(v), 2) + 0.0 for v in np.asarray(values, dtype=float)]


def _hero() -> dict[str, object]:
    """Run the snippet, a standalone script loaded by path, and return the figure's data."""
    snippet = runpy.run_path(str(SNIPPET_PATH))
    result = snippet["result"]
    if not isinstance(result, OptimalDispatchResults):
        msg = f"Snippet {SNIPPET_PATH.name} must define `result` as OptimalDispatchResults"
        raise TypeError(msg)
    return {"price_scenarios": snippet["price_scenarios"], "schedule": _market_schedule(result)}


def landing_data() -> dict[str, object]:
    """Run the model behind the landing page and return the data home.js reads."""
    return {"hero": _hero()}


def generate_landing_data() -> None:
    """Run the model behind the landing page and write its data file."""
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(landing_data(), ensure_ascii=False, separators=(",", ":")))
    print(f"  ✓ {OUTPUT_PATH.relative_to(REPOSITORY_ROOT)}")


if __name__ == "__main__":
    print("Generating landing page data...")
    generate_landing_data()
    print("Done!")
