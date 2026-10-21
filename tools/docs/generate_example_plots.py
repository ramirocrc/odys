"""Generate interactive Plotly charts for example documentation.

Usage:
    uv run --locked python tools/docs/generate_example_plots.py

Output:
    Writes standalone Plotly HTML files to docs/assets/plots/ (git-ignored build output)
    for embedding in zensical via <iframe>.
"""

import json
import re
import sys
from datetime import timedelta
from pathlib import Path
from typing import NamedTuple

_project_root = str(Path(__file__).resolve().parent.parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

import numpy as np
import plotly.graph_objects as go
from plotly.offline import get_plotlyjs_version
from plotly.subplots import make_subplots

from examples.day_ahead_or_intraday import run_day_ahead_or_intraday  # pyrefly: ignore
from examples.demand_response import run_demand_response  # pyrefly: ignore
from examples.depot_charging import (  # pyrefly: ignore
    CHARGERS,
    EV_FINAL_STATES,
    EV_INITIAL_STATES,
    EVS,
    MARKET_PRICES,
    run_depot_charging,
)
from examples.make_or_buy import run_make_or_buy  # pyrefly: ignore
from examples.merit_order_dispatch import run_merit_order_dispatch  # pyrefly: ignore
from examples.solar_storage import LOAD_PROFILE, run_solar_storage  # pyrefly: ignore
from odys import Charger, OptimalDispatchResults, Trip
from odys.optimization.formulations.electric_vehicle import ElectricVehicleFormulation

OUTPUT_DIR = Path(__file__).resolve().parent.parent.parent / "docs" / "assets" / "plots"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Chart colours and font come from the brand tokens, the single source of truth for Odys styling.
# Figures are built with the light colours; _save_figure derives the dark figure from them, and
# each chart page follows the colour scheme of the docs page that embeds it.
_BRAND = json.loads((Path(__file__).parent / "brand" / "tokens.json").read_text())
_CHART = _BRAND["chart"]
BRAND_FONT = f"{_BRAND['font']['sans']['family']}, {_BRAND['font']['sans']['fallback']}"
TRANSPARENT = "rgba(0, 0, 0, 0)"
_HEX_OR_RGBA = re.compile(r"#[0-9a-f]{6}\b|rgba\((\d+), (\d+), (\d+), ([\d.]+)\)", re.IGNORECASE)


def _chart_color(role: str, scheme: str = "light") -> str:
    """Resolve a chart role ("solar", "price", ...) to its brand colour in one colour scheme."""
    return _CHART["roles"][role][scheme]


def _chrome_color(name: str, scheme: str = "light") -> str:
    """Resolve a non-data chart colour ("text", "grid", ...) in one colour scheme."""
    return _CHART["chrome"][name][scheme]


def with_alpha(hex_color: str, alpha: float) -> str:
    """Turn a hex colour into an rgba() colour with the given alpha."""
    red, green, blue = _rgb(hex_color)
    return f"rgba({red}, {green}, {blue}, {alpha})"


def _rgb(hex_color: str) -> tuple[int, int, int]:
    red, green, blue = (int(hex_color[i : i + 2], 16) for i in (1, 3, 5))
    return red, green, blue


def _dark_colors() -> dict[str, str]:
    """Map every light chart colour (roles and chrome) to its dark counterpart."""
    pairs = [*_CHART["roles"].values(), *_CHART["chrome"].values()]
    return {pair["light"]: pair["dark"] for pair in pairs}


def to_dark(figure_json: str) -> str:
    """Swap every light brand colour in a serialised figure for its dark counterpart.

    Hex colours are swapped directly; rgba() colours built with with_alpha keep their alpha.
    """
    dark = _dark_colors()
    dark_by_rgb = {_rgb(light): dark_color for light, dark_color in dark.items()}

    def swap(match: re.Match[str]) -> str:
        if match.group(1) is None:
            return dark.get(match.group(0).lower(), match.group(0))
        rgb = (int(match.group(1)), int(match.group(2)), int(match.group(3)))
        if rgb not in dark_by_rgb:
            return match.group(0)
        return with_alpha(dark_by_rgb[rgb], float(match.group(4)))

    return _HEX_OR_RGBA.sub(swap, figure_json)


SOLAR_COLOR = _chart_color("solar")
SOLAR_LINE_COLOR = _chart_color("solar_line")
THERMAL_COLOR = _chart_color("thermal")
LOAD_COLOR = _chart_color("load")
BATTERY_SOC_COLOR = _chart_color("battery_soc")
BATTERY_DISCHARGE_COLOR = _chart_color("discharge")
BATTERY_CHARGE_COLOR = _chart_color("charge")
MARKET_BUY_COLOR = _chart_color("market_buy")
MARKET_PRICE_COLOR = _chart_color("price")
SDAC_COLOR = _chart_color("sdac")
SIDC_COLOR = _chart_color("sidc")
FLEXIBLE_LOAD_COLOR = _chart_color("flexible_load")
VALUE_OF_CONSUMPTION_COLOR = _chart_color("value_of_consumption")
EV_1_COLOR = _chart_color("ev_1")
EV_2_COLOR = _chart_color("ev_2")
EV_3_COLOR = _chart_color("ev_3")
BACKGROUND_COLOR = _chrome_color("background")
GRID_COLOR = _chrome_color("grid")

# Runs inside each chart page. The page is embedded in a same-origin iframe, so it reads the
# docs page's colour scheme and re-renders when the reader switches it. Opened on its own, the
# chart follows the operating system's preference.
_THEME_SCRIPT = """
const figures = {"light": %(light)s, "dark": %(dark)s};
const chart = document.getElementById("chart");
const media = window.matchMedia("(prefers-color-scheme: dark)");
let host = null;
try {
  if (window.parent !== window) host = window.parent.document.body;
} catch (error) {}
let current = null;
function scheme() {
  const docsScheme = host && host.dataset.mdColorScheme;
  if (docsScheme) return docsScheme === "slate" ? "dark" : "light";
  return media.matches ? "dark" : "light";
}
function render() {
  const next = scheme();
  if (next === current) return;
  current = next;
  Plotly.react(chart, figures[next].data, figures[next].layout, {responsive: true});
}
render();
if (host) new MutationObserver(render).observe(host, {attributes: true, attributeFilter: ["data-md-color-scheme"]});
media.addEventListener("change", render);
"""

_CHART_PAGE = """<!doctype html>
<html>
<head>
<meta charset="utf-8">
<meta name="color-scheme" content="light dark">
<style>html, body { margin: 0; height: 100%%; background: transparent; } #chart { height: 100%%; }</style>
<script src="https://cdn.plot.ly/plotly-%(version)s.min.js"></script>
</head>
<body>
<div id="chart"></div>
<script>%(script)s</script>
</body>
</html>
"""


def _apply_chart_theme(fig: go.Figure) -> None:
    """Give a figure the brand font and the light chrome on a transparent background."""
    text, muted, axis = (_chrome_color(name) for name in ("text", "muted", "axis"))
    fig.update_layout(
        template=None,
        font={"family": BRAND_FONT, "color": text},
        paper_bgcolor=TRANSPARENT,
        plot_bgcolor=TRANSPARENT,
        legend_bgcolor=TRANSPARENT,
        hoverlabel={"bgcolor": BACKGROUND_COLOR, "bordercolor": axis, "font": {"color": text}},
    )
    axes = {"gridcolor": GRID_COLOR, "zerolinecolor": axis, "linecolor": axis, "tickfont": {"color": muted}}
    fig.update_xaxes(**axes)
    fig.update_yaxes(**axes)


def _save_figure(fig: go.Figure, name: str) -> None:
    path = OUTPUT_DIR / f"{name}.html"
    _apply_chart_theme(fig)
    light = fig.to_json().replace("</", "<\\/")
    script = _THEME_SCRIPT % {"light": light, "dark": to_dark(light)}
    path.write_text(_CHART_PAGE % {"version": get_plotlyjs_version(), "script": script})
    print(f"  \u2713 {path.name}")


def generate_merit_order_dispatch() -> None:
    """Stacked bar chart of generator dispatch with load overlay."""
    result = run_merit_order_dispatch()
    df = result.generators.to_dataframe()["power"].unstack("generator")
    steps = list(range(len(df)))

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=steps,
            y=df["solar_pv"],
            name="Solar PV",
            marker=dict(color=SOLAR_COLOR),
        ),
    )

    fig.add_trace(
        go.Bar(
            x=steps,
            y=df["ccgt"],
            name="CCGT",
            marker=dict(color=THERMAL_COLOR),
        ),
    )

    solar_profile = [0, 0, 0, 0, 0, 0, 10, 30, 60, 90, 110, 120, 125, 120, 110, 90, 60, 30, 10, 0, 0, 0, 0, 0]

    fig.add_trace(
        go.Scatter(
            x=steps,
            y=solar_profile,
            mode="lines",
            name="Solar Capacity",
            line=dict(color=SOLAR_LINE_COLOR, width=2, dash="dash"),
        ),
    )

    fig.add_trace(
        go.Scatter(
            x=steps,
            y=[70] * len(steps),
            mode="lines",
            name="Load (70 MW)",
            line=dict(color=LOAD_COLOR, width=2, dash="dash"),
        ),
    )

    fig.update_layout(
        title=dict(text="Generator Dispatch", x=0.5),
        xaxis=dict(title="Time Step", range=[-0.5, 23.5]),
        yaxis=dict(title="Power (MW)", range=[0, 150]),
        barmode="stack",
        hovermode="x unified",
        legend=dict(x=0.01, y=0.99),
        margin=dict(l=40, r=20, t=40, b=40),
    )

    _save_figure(fig, "merit_order_dispatch")


def generate_solar_storage() -> None:
    """Two-panel chart: generator dispatch with battery + battery SOC."""
    result = run_solar_storage()
    gen_df = result.generators.to_dataframe()["power"].unstack("generator")
    battery_df = result.battery_storages.to_dataframe().droplevel("battery_storage")
    steps = list(range(len(gen_df)))

    fig = make_subplots(
        rows=2,
        cols=1,
        vertical_spacing=0.12,
        subplot_titles=("Dispatch", "Battery State of Charge"),
        row_heights=[0.7, 0.3],
    )

    # Split battery into discharge (positive) and charge (negative)
    battery_power = -battery_df["net_power"].to_numpy()  # Invert so discharge is positive
    battery_discharge = np.maximum(battery_power, 0)
    battery_charge = np.minimum(battery_power, 0)

    solar = gen_df["solar_pv"].to_numpy()
    ccgt = gen_df["ccgt"].to_numpy()
    np.testing.assert_allclose(solar + ccgt + battery_power, LOAD_PROFILE, atol=1e-6)

    fig.add_trace(
        go.Bar(
            x=steps,
            y=battery_discharge,
            name="Battery Discharge",
            marker=dict(color=BATTERY_DISCHARGE_COLOR),
            legendgroup="gen",
        ),
        row=1,
        col=1,
    )

    fig.add_trace(
        go.Bar(
            x=steps,
            y=solar,
            name="Solar PV",
            marker=dict(color=SOLAR_COLOR),
            legendgroup="gen",
        ),
        row=1,
        col=1,
    )

    fig.add_trace(
        go.Bar(
            x=steps,
            y=ccgt,
            name="CCGT",
            marker=dict(color=THERMAL_COLOR),
            legendgroup="gen",
        ),
        row=1,
        col=1,
    )

    fig.add_trace(
        go.Bar(
            x=steps,
            y=battery_charge,
            name="Battery Charge",
            marker=dict(color=BATTERY_CHARGE_COLOR),
            legendgroup="gen",
        ),
        row=1,
        col=1,
    )

    fig.add_trace(
        go.Scatter(
            x=steps,
            y=LOAD_PROFILE,
            mode="lines",
            name="Load",
            line=dict(color=LOAD_COLOR, width=2, dash="dash"),
            legendgroup="gen",
        ),
        row=1,
        col=1,
    )

    soc_percent = battery_df["soc"].to_numpy() * 100

    fig.add_trace(
        go.Scatter(
            x=steps,
            y=soc_percent,
            mode="lines+markers",
            name="State of Charge (%)",
            line=dict(color=BATTERY_SOC_COLOR, width=2),
            marker=dict(size=6),
        ),
        row=2,
        col=1,
    )

    fig.update_layout(
        barmode="relative",
        hovermode="x unified",
        legend=dict(x=0.01, y=0.99),
        margin=dict(l=40, r=20, t=40, b=40),
    )

    fig.update_xaxes(title="Time Step", range=[-0.5, 23.5], row=1, col=1)
    fig.update_xaxes(title="Time Step", range=[-0.5, 23.5], row=2, col=1)
    fig.update_yaxes(title="Power (MW)", row=1, col=1, range=[-80, 200])
    fig.update_yaxes(title="State of Charge (%)", row=2, col=1, range=[0, 100])

    _save_figure(fig, "solar_storage")


def generate_make_or_buy() -> None:
    """Two-panel chart: stacked dispatch bars + market prices."""
    result = run_make_or_buy()
    gen_df = result.generators.to_dataframe()["power"].unstack("generator")
    bought = -result.markets.net_volume.xs("market", level="market")
    steps = list(range(len(gen_df)))

    market_prices = [80, 75, 70, 65, 60, 55, 52, 45, 40, 35, 30, 35, 40, 45, 52, 55, 60, 70, 80, 90, 85, 80, 75, 70]

    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.12,
        subplot_titles=("Dispatch", "Market Prices"),
        row_heights=[0.7, 0.3],
    )

    fig.add_trace(
        go.Bar(
            x=steps,
            y=gen_df["ccgt"],
            name="CCGT Generation",
            marker=dict(color=THERMAL_COLOR),
        ),
        row=1,
        col=1,
    )

    fig.add_trace(
        go.Bar(
            x=steps,
            y=bought.values,
            name="Market (bought +, sold -)",
            marker=dict(color=MARKET_BUY_COLOR),
        ),
        row=1,
        col=1,
    )

    fig.add_trace(
        go.Scatter(
            x=steps,
            y=[70] * len(steps),
            mode="lines",
            name="Load (70 MW)",
            line=dict(color=LOAD_COLOR, width=2, dash="dash"),
        ),
        row=1,
        col=1,
    )

    fig.add_trace(
        go.Scatter(
            x=steps,
            y=market_prices,
            mode="lines+markers",
            name="Market Price ($/MWh)",
            line=dict(color=MARKET_PRICE_COLOR, width=2),
            marker=dict(size=8),
        ),
        row=2,
        col=1,
    )

    fig.add_trace(
        go.Scatter(
            x=steps,
            y=[50] * len(steps),
            mode="lines",
            name="CCGT Cost (50 $/MWh)",
            line=dict(color=MARKET_PRICE_COLOR, width=1, dash="dot"),
        ),
        row=2,
        col=1,
    )

    fig.update_layout(
        barmode="relative",
        hovermode="x unified",
        legend=dict(x=0.5, y=1.02, xanchor="center", yanchor="bottom", orientation="h"),
        margin=dict(l=40, r=40, t=60, b=40),
    )

    fig.update_xaxes(title="Time Step", range=[-0.5, 23.5], row=1, col=1)
    fig.update_xaxes(title="Time Step", range=[-0.5, 23.5], row=2, col=1)
    fig.update_yaxes(title="Power (MW)", row=1, col=1)
    fig.update_yaxes(title="Price ($/MWh)", row=2, col=1)

    _save_figure(fig, "make_or_buy")


def generate_demand_response() -> None:
    """Two-panel chart: load consumption + market prices."""
    result = run_demand_response()
    consumption = result.flexible_loads.consumption
    steps = list(range(len(consumption)))

    market_prices = [80, 75, 72, 65, 60, 55, 50, 45, 40, 35, 30, 35, 40, 45, 50, 55, 60, 72, 80, 90, 85, 80, 75, 72]

    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.12,
        subplot_titles=("Load Consumption", "Market Prices"),
        row_heights=[0.5, 0.5],
    )

    for bound_name, bound in (("Lower Bound (40 MW)", 40), ("Upper Bound (100 MW)", 100)):
        fig.add_trace(
            go.Scatter(
                x=steps,
                y=[bound] * len(steps),
                mode="lines",
                name=bound_name,
                line=dict(color=LOAD_COLOR, width=2, dash="dash"),
            ),
            row=1,
            col=1,
        )

    fig.add_trace(
        go.Scatter(
            x=steps,
            y=consumption.values,
            mode="lines+markers",
            name="Consumption",
            line=dict(color=FLEXIBLE_LOAD_COLOR, width=2),
            marker=dict(size=6),
        ),
        row=1,
        col=1,
    )

    fig.add_trace(
        go.Scatter(
            x=steps,
            y=market_prices,
            mode="lines+markers",
            name="Market Price ($/MWh)",
            line=dict(color=MARKET_PRICE_COLOR, width=2),
            marker=dict(size=8),
        ),
        row=2,
        col=1,
    )

    fig.add_trace(
        go.Scatter(
            x=steps,
            y=[70] * len(steps),
            mode="lines",
            name="Value of Consumption (70 $/MWh)",
            line=dict(color=VALUE_OF_CONSUMPTION_COLOR, width=2, dash="dash"),
        ),
        row=2,
        col=1,
    )

    fig.update_layout(
        hovermode="x unified",
        legend=dict(x=0.5, y=1.02, xanchor="center", yanchor="bottom", orientation="h"),
        margin=dict(l=40, r=40, t=60, b=40),
    )

    fig.update_xaxes(title="Time Step", range=[-0.5, 23.5], row=1, col=1)
    fig.update_xaxes(title="Time Step", range=[-0.5, 23.5], row=2, col=1)
    fig.update_yaxes(title="Power (MW)", row=1, col=1, range=[0, 110])
    fig.update_yaxes(title="Price ($/MWh)", row=2, col=1)

    _save_figure(fig, "demand_response")


def generate_day_ahead_or_intraday() -> None:
    """Side-by-side grouped bar charts of market allocation for both runs."""
    result_profit, result_cvar = run_day_ahead_or_intraday()

    sell_profit = result_profit.markets.sell_volume.droplevel("time")
    sell_cvar = result_cvar.markets.sell_volume.droplevel("time")

    scenarios = ["high", "mid", "low"]

    fig = make_subplots(
        rows=1,
        cols=2,
        shared_yaxes=True,
        subplot_titles=("Profit Only", "Profit + CVaR (weight=1)"),
    )

    for i, scenario in enumerate(scenarios):
        sdac_profit = sell_profit.loc[(scenario, "day_ahead")]
        sidc_profit = sell_profit.loc[(scenario, "intraday")]
        sdac_cvar = sell_cvar.loc[(scenario, "day_ahead")]
        sidc_cvar = sell_cvar.loc[(scenario, "intraday")]

        fig.add_trace(
            go.Bar(
                x=[scenario],
                y=[sdac_profit],
                name="Day-ahead",
                marker=dict(color=SDAC_COLOR),
                legendgroup="sdac",
                showlegend=(i == 0),
            ),
            row=1,
            col=1,
        )

        fig.add_trace(
            go.Bar(
                x=[scenario],
                y=[sidc_profit],
                name="Intraday",
                marker=dict(color=SIDC_COLOR),
                legendgroup="sidc",
                showlegend=(i == 0),
            ),
            row=1,
            col=1,
        )

        fig.add_trace(
            go.Bar(
                x=[scenario],
                y=[sdac_cvar],
                name="Day-ahead",
                marker=dict(color=SDAC_COLOR),
                legendgroup="sdac",
                showlegend=False,
            ),
            row=1,
            col=2,
        )

        fig.add_trace(
            go.Bar(
                x=[scenario],
                y=[sidc_cvar],
                name="Intraday",
                marker=dict(color=SIDC_COLOR),
                legendgroup="sidc",
                showlegend=False,
            ),
            row=1,
            col=2,
        )

    fig.update_layout(
        barmode="stack",
        hovermode="x unified",
        legend=dict(x=0.5, y=-0.15, orientation="h"),
        margin=dict(l=40, r=20, t=40, b=60),
    )

    fig.update_xaxes(title="Scenario", row=1, col=1)
    fig.update_xaxes(title="Scenario", row=1, col=2)
    fig.update_yaxes(title="Volume (MW)", row=1, col=1, rangemode="tozero")

    _save_figure(fig, "day_ahead_or_intraday")


EV_COLORS = {"ev_1": EV_1_COLOR, "ev_2": EV_2_COLOR, "ev_3": EV_3_COLOR}
SOC_START = {state.vehicle.name: state.soc for state in EV_INITIAL_STATES}
SOC_END = {state.vehicle.name: state.soc for state in EV_FINAL_STATES}
PRICE_STEP_COLOR = _chart_color("price_step")
MARKER_OUTLINE_COLOR = _chart_color("marker_outline")
TABLE_HEADER_FILL = _chart_color("table_header")
CHECK_OK_INK = _chart_color("check_ok")
CHECK_FAIL_INK = _chart_color("check_fail")
CHECK_OK_FILL = with_alpha(CHECK_OK_INK, 0.18)
CHECK_FAIL_FILL = with_alpha(CHECK_FAIL_INK, 0.22)
NEUTRAL_CELL_FILL = TRANSPARENT
ACTIVE_POWER_TOLERANCE = 1e-6
ASSIGNMENT_THRESHOLD = 0.5
TRIP_POWER_TOLERANCE_KW = 1e-3
TRIP_COLOR = _chart_color("trip")
CHARGING_COLOR = _chart_color("charge")
DISCHARGING_COLOR = _chart_color("discharge")

NUMBER_OF_HOURS = len(MARKET_PRICES)
HOUR_EDGES = list(range(NUMBER_OF_HOURS + 1))
HOUR_CENTERS = [t + 0.5 for t in range(NUMBER_OF_HOURS)]


ONE_HOUR = timedelta(hours=1)
MIDDAY_PRICE = 10.0


class TripHours(NamedTuple):
    """The first hour of a trip and the hour the vehicle is back, as step indices of the hourly example."""

    start: int
    end: int


def _trip_hours(trip: Trip) -> TripHours:
    return TripHours(start=trip.start_time // ONE_HOUR, end=trip.end_time // ONE_HOUR)


def _ev_display_name(ev_name: str) -> str:
    return ev_name.replace("ev_", "EV ")


def _charger_display_name(charger: Charger) -> str:
    kind = charger.name.removeprefix("charger_").upper()
    return f"{kind} ({charger.max_power * 1000:.0f} kW)"


def _mw_to_kw(values_mw: np.ndarray) -> list[float]:
    return [float(v) * 1000 for v in values_mw]


def _price_step_trace(*, show_legend: bool) -> go.Scatter:
    return go.Scatter(
        x=HOUR_EDGES,
        y=[*MARKET_PRICES, MARKET_PRICES[-1]],
        mode="lines",
        name="Price",
        line=dict(color=PRICE_STEP_COLOR, width=2, shape="hv"),
        showlegend=show_legend,
        hovertemplate="%{y:.0f} $/MWh<extra>Price</extra>",
    )


def _add_price_row(fig: go.Figure, row: int, *, annotate: bool = False, show_legend: bool = False) -> None:
    fig.add_trace(_price_step_trace(show_legend=show_legend), row=row, col=1)
    if annotate:
        annotations = [
            (3.0, 5.0, "5 $/MWh overnight"),
            (9.0, 80.0, "80 $/MWh morning peak"),
            (12.5, 10.0, "10 $/MWh midday"),
            (19.0, 100.0, "100 $/MWh evening peak"),
        ]
        for x, y, text in annotations:
            fig.add_annotation(
                x=x,
                y=y,
                yshift=12,
                text=text,
                showarrow=False,
                font=dict(size=10, color=PRICE_STEP_COLOR),
                row=row,
                col=1,
            )


def _add_trip_vrects(fig: go.Figure, row: int) -> None:
    for ev in EVS:
        for hours in map(_trip_hours, ev.trips):
            fig.add_vrect(
                x0=hours.start,
                x1=hours.end,
                fillcolor=EV_COLORS[ev.name],
                opacity=0.08,
                line_width=0,
                row=row,
                col=1,
            )


def _active_charger_segments(result: OptimalDispatchResults) -> list[tuple[str, str, int, int]]:
    """Return (charger, ev, start, end) hours where an EV is both assigned and exchanging power.

    The assignment variable is degenerate while an EV draws no power, so raw
    assignments overstate occupancy; only powered hours count as occupancy here.
    """
    assignment = result.chargers.to_dataset()["assignment"]
    net_power = result.electric_vehicles.to_dataset()["net_power"]
    segments: list[tuple[str, str, int, int]] = []
    for charger in CHARGERS:
        for ev in EVS:
            connected = assignment.sel(charger=charger.name, ev=ev.name).values > ASSIGNMENT_THRESHOLD
            powered = np.abs(net_power.sel(ev=ev.name).values) > ACTIVE_POWER_TOLERANCE
            active = [bool(c and p) for c, p in zip(connected, powered, strict=True)]
            start: int | None = None
            for t, flag in enumerate([*active, False]):
                if flag and start is None:
                    start = t
                elif not flag and start is not None:
                    segments.append((charger.name, ev.name, start, t))
                    start = None
    return segments


def _extract_ev_state_intervals(result: OptimalDispatchResults) -> list[tuple[str, str, int, int]]:
    """Return (ev_name, state, start, end) tuples for trip, charging, and discharging intervals.

    States are mutually exclusive per timestep:
    - "trip": vehicle is on a trip (unavailable)
    - "charging": vehicle is charging (net_power > 0)
    - "discharging": vehicle is discharging (net_power < 0, V2G only)
    """
    net_power = result.electric_vehicles.to_dataset()["net_power"]
    intervals: list[tuple[str, str, int, int]] = []

    for ev in EVS:
        ev_power = net_power.sel(ev=ev.name).values

        trip_hours = [_trip_hours(trip) for trip in ev.trips]
        intervals.extend((ev.name, "trip", hours.start, hours.end) for hours in trip_hours)

        is_charging = ev_power > ACTIVE_POWER_TOLERANCE
        is_discharging = ev_power < -ACTIVE_POWER_TOLERANCE

        for t in range(NUMBER_OF_HOURS):
            on_trip = any(hours.start <= t < hours.end for hours in trip_hours)
            if on_trip:
                continue

            if is_charging[t]:
                intervals.append((ev.name, "charging", t, t + 1))
            elif is_discharging[t]:
                intervals.append((ev.name, "discharging", t, t + 1))

    merged: list[tuple[str, str, int, int]] = []
    for ev_name, state, start, end in intervals:
        if merged and merged[-1][0] == ev_name and merged[-1][1] == state and merged[-1][3] == start:
            merged[-1] = (ev_name, state, merged[-1][2], end)
        else:
            merged.append((ev_name, state, start, end))

    return merged


def generate_depot_charging_setup() -> None:
    """Price signal and trip obligations the optimizer faces, before any decision is shown."""
    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        row_heights=[0.55, 0.45],
        vertical_spacing=0.12,
        subplot_titles=("Time-of-use price", "Trip obligations (vehicle away from the depot)"),
    )

    _add_price_row(fig, row=1, annotate=True)

    lanes = {"ev_1": 2, "ev_2": 1, "ev_3": 0}
    first_trip = True
    for ev in EVS:
        lane = lanes[ev.name]
        for trip in ev.trips:
            hours = _trip_hours(trip)
            fig.add_trace(
                go.Scatter(
                    x=[hours.start, hours.end],
                    y=[lane, lane],
                    mode="lines",
                    line=dict(color=TRIP_COLOR, width=16),
                    name="Trip (vehicle away)",
                    legendgroup="trip",
                    showlegend=first_trip,
                    text=f"{trip.name} (t{hours.start}-t{hours.end})",
                    hoverinfo="text",
                ),
                row=2,
                col=1,
            )
            first_trip = False
            fig.add_annotation(
                x=(hours.start + hours.end) / 2,
                y=lane + 0.38,
                text=trip.name,
                showarrow=False,
                font=dict(size=10, color=TRIP_COLOR),
                row=2,
                col=1,
            )

    fig.update_xaxes(range=[0, 24], dtick=3)
    fig.update_xaxes(title="Hour of day", row=2, col=1)
    fig.update_yaxes(title="Price ($/MWh)", rangemode="tozero", row=1, col=1)
    fig.update_yaxes(
        tickvals=[2, 1, 0],
        ticktext=["EV 1", "EV 2", "EV 3"],
        range=[-0.6, 2.8],
        row=2,
        col=1,
    )
    fig.update_layout(
        title=dict(text="What the Optimizer Faces", x=0.5),
        hovermode="x unified",
        legend=dict(x=0.5, y=-0.22, xanchor="center", yanchor="top", orientation="h"),
        margin=dict(l=40, r=40, t=60, b=90),
    )

    _save_figure(fig, "depot_charging_setup")


def generate_depot_charging_dispatch_combined(result: OptimalDispatchResults) -> None:
    """Combined dispatch figure: price, vehicle states, SoC, and charger occupancy with aligned x-axes."""
    fig = make_subplots(
        rows=4,
        cols=1,
        shared_xaxes=True,
        row_heights=[0.22, 0.26, 0.26, 0.26],
        vertical_spacing=0.08,
        subplot_titles=(
            "Time-of-use price",
            "Vehicle states",
            "State of charge",
            "Charger occupancy",
        ),
    )

    _add_price_row(fig, row=1, annotate=True)

    lanes = {"ev_1": 2, "ev_2": 1, "ev_3": 0}
    state_intervals = _extract_ev_state_intervals(result)
    state_colors = {"trip": TRIP_COLOR, "charging": CHARGING_COLOR, "discharging": DISCHARGING_COLOR}
    state_names = {"trip": "Trip (vehicle away)", "charging": "Charging", "discharging": "Discharging (V2G)"}

    for ev_name, state, start, end in state_intervals:
        lane = lanes[ev_name]
        color = state_colors[state]
        fig.add_trace(
            go.Scatter(
                x=[start, end],
                y=[lane, lane],
                mode="lines",
                line=dict(color=color, width=16),
                name=state_names[state],
                legendgroup=state,
                legend="legend",
                showlegend=False,
                text=f"{_ev_display_name(ev_name)}: {state_names[state].lower()} (t{start}-t{end})",
                hoverinfo="text",
            ),
            row=2,
            col=1,
        )

    for state in ["trip", "charging", "discharging"]:
        fig.add_trace(
            go.Scatter(
                x=[None],
                y=[None],
                mode="lines",
                line=dict(color=state_colors[state], width=16),
                name=state_names[state],
                legendgroup=state,
                legend="legend",
                showlegend=True,
            ),
            row=2,
            col=1,
        )

    ev_dataset = result.electric_vehicles.to_dataset()
    for ev in EVS:
        soc_values = [SOC_START[ev.name], *ev_dataset.sel(ev=ev.name).soc.values]
        fig.add_trace(
            go.Scatter(
                x=HOUR_EDGES,
                y=soc_values,
                mode="lines",
                name=_ev_display_name(ev.name),
                legendgroup=ev.name,
                legend="legend2",
                line=dict(color=EV_COLORS[ev.name], width=2),
                hovertemplate="%{y:.2f}<extra>" + _ev_display_name(ev.name) + " SoC</extra>",
            ),
            row=3,
            col=1,
        )

    charger_lanes = {"charger_dc": 1, "charger_ac": 0}
    shown_evs: set[str] = set()
    for charger_name, ev_name, start, end in _active_charger_segments(result):
        lane = charger_lanes[charger_name]
        fig.add_trace(
            go.Scatter(
                x=[start + 0.04, end - 0.04],
                y=[lane, lane],
                mode="lines",
                line=dict(color=EV_COLORS[ev_name], width=16),
                name=_ev_display_name(ev_name),
                legendgroup=f"charger_{ev_name}",
                legend="legend3",
                showlegend=ev_name not in shown_evs,
                text=f"{_ev_display_name(ev_name)} on {charger_name} (t{start}-t{end})",
                hoverinfo="text",
            ),
            row=4,
            col=1,
        )
        shown_evs.add(ev_name)

    for row in range(1, 5):
        fig.update_xaxes(range=[0, 24], dtick=3, row=row, col=1)

    fig.update_yaxes(title="Price ($/MWh)", rangemode="tozero", row=1, col=1)
    fig.update_yaxes(
        tickvals=[2, 1, 0],
        ticktext=["EV 1", "EV 2", "EV 3"],
        range=[-0.6, 2.8],
        row=2,
        col=1,
    )
    fig.update_yaxes(title="SoC", range=[0, 1.05], dtick=0.25, row=3, col=1)
    fig.update_yaxes(
        tickvals=[1, 0],
        ticktext=[_charger_display_name(charger) for charger in CHARGERS],
        range=[-0.6, 1.6],
        row=4,
        col=1,
    )

    fig.update_xaxes(title="Hour of day", row=4, col=1)

    fig.update_layout(
        title=dict(text="Optimal Dispatch", x=0.5),
        hovermode="x unified",
        legend=dict(
            x=0.5,
            y=0.56,
            xanchor="center",
            yanchor="top",
            orientation="h",
            title="",
        ),
        legend2=dict(
            x=0.5,
            y=0.26,
            xanchor="center",
            yanchor="top",
            orientation="h",
            title="",
        ),
        legend3=dict(
            x=0.5,
            y=-0.06,
            xanchor="center",
            yanchor="top",
            orientation="h",
            title="",
        ),
        margin=dict(l=90, r=40, t=60, b=100),
    )

    _save_figure(fig, "depot_charging_dispatch_combined")


def _constraint_check_rows(result: OptimalDispatchResults) -> list[tuple[str, str, str, bool]]:
    """Compute every trip, SoC, and charger constraint check from the solved result."""
    tolerance = 1e-6
    ev_dataset = result.electric_vehicles.to_dataset()
    assignment = result.chargers.to_dataset()["assignment"]
    rows: list[tuple[str, str, str, bool]] = []

    for ev in EVS:
        soc_values = ev_dataset.sel(ev=ev.name).soc.values
        for trip in ev.trips:
            start = _trip_hours(trip).start
            actual = float(soc_values[start - 1]) if start > 0 else SOC_START[ev.name]
            rows.append((
                f"{_ev_display_name(ev.name)} SoC before {trip.name} (t{start})",
                f"≥ {trip.min_soc_at_departure:.2f}",
                f"{actual:.3f}",
                actual >= trip.min_soc_at_departure - tolerance,
            ))

    for ev in EVS:
        if ev.name not in SOC_END:
            continue
        actual = float(ev_dataset.sel(ev=ev.name).soc.values[-1])
        rows.append((
            f"{_ev_display_name(ev.name)} end-of-day SoC",
            f"= {SOC_END[ev.name]:.2f}",
            f"{actual:.3f}",
            abs(actual - SOC_END[ev.name]) <= tolerance,
        ))

    worst_trip_power_kw = 0.0
    for ev in EVS:
        net_power = ev_dataset.sel(ev=ev.name).net_power.values
        for hours in map(_trip_hours, ev.trips):
            trip_power = float(np.abs(net_power[hours.start : hours.end]).max()) * 1000
            worst_trip_power_kw = max(worst_trip_power_kw, trip_power)
    rows.append((
        "Largest |EV power| during any trip",
        "= 0 kW",
        f"{worst_trip_power_kw:.4f} kW",
        worst_trip_power_kw <= TRIP_POWER_TOLERANCE_KW,
    ))

    net_power_kw_by_ev = {ev.name: np.abs(ev_dataset.sel(ev=ev.name).net_power.values) * 1000 for ev in EVS}
    for charger in CHARGERS:
        connected = assignment.sel(charger=charger.name)
        most_evs = float(connected.sum(ElectricVehicleFormulation.dimension).max())
        rows.append((
            f"Most EVs on {_charger_display_name(charger)} in any hour",
            "≤ 1",
            f"{most_evs:.0f}",
            most_evs <= 1 + tolerance,
        ))
        loading_kw = sum(connected.sel(ev=ev.name).values * net_power_kw_by_ev[ev.name] for ev in EVS)
        worst_loading_kw = float(np.max(loading_kw))
        limit_kw = charger.max_power * 1000
        rows.append((
            f"{_charger_display_name(charger)} worst-hour loading",
            f"≤ {limit_kw:.0f} kW",
            f"{worst_loading_kw:.1f} kW",
            worst_loading_kw <= limit_kw + tolerance,
        ))

    return rows


def generate_depot_charging_verification(result: OptimalDispatchResults) -> None:
    """Constraint verification table computed from the solved result, not asserted by hand."""
    rows = _constraint_check_rows(result)
    checks = [row[0] for row in rows]
    requirements = [row[1] for row in rows]
    actuals = [row[2] for row in rows]
    statuses = ["PASS" if row[3] else "FAIL" for row in rows]
    status_fills = [CHECK_OK_FILL if row[3] else CHECK_FAIL_FILL for row in rows]
    status_inks = [CHECK_OK_INK if row[3] else CHECK_FAIL_INK for row in rows]

    failures = [row[0] for row in rows if not row[3]]
    for failed_check in failures:
        print(f"WARNING: depot charging verification check failed: {failed_check}", file=sys.stderr)

    fig = go.Figure(
        data=[
            go.Table(
                columnwidth=[0.46, 0.16, 0.2, 0.18],
                header=dict(
                    values=["<b>Check</b>", "<b>Requirement</b>", "<b>Result</b>", "<b>Status</b>"],
                    fill_color=TABLE_HEADER_FILL,
                    line=dict(color=GRID_COLOR),
                    font=dict(color=MARKER_OUTLINE_COLOR, size=12),
                    align=["left", "center", "center", "center"],
                    height=30,
                ),
                cells=dict(
                    values=[checks, requirements, actuals, statuses],
                    fill_color=[NEUTRAL_CELL_FILL, NEUTRAL_CELL_FILL, NEUTRAL_CELL_FILL, status_fills],
                    line=dict(color=GRID_COLOR),
                    font=dict(
                        size=12,
                        color=[MARKER_OUTLINE_COLOR, MARKER_OUTLINE_COLOR, MARKER_OUTLINE_COLOR, status_inks],
                    ),
                    align=["left", "center", "center", "center"],
                    height=26,
                ),
            ),
        ],
    )

    fig.update_layout(
        title=dict(text="Constraint Verification (computed from the solved result)", x=0.5),
        margin=dict(l=20, r=20, t=50, b=20),
    )

    _save_figure(fig, "depot_charging_verification")


def generate_depot_charging_economics(result: OptimalDispatchResults) -> None:
    """Market flows showing grid purchases and V2G sales."""
    buy_mwh = np.asarray(result.markets.buy_volume.xs("grid_market", level="market").values, dtype=float)
    sell_mwh = np.asarray(result.markets.sell_volume.xs("grid_market", level="market").values, dtype=float)

    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        row_heights=[0.4, 0.6],
        vertical_spacing=0.08,
        subplot_titles=(
            "Price ($/MWh)",
            "Grid purchases and V2G sales (kW)",
        ),
    )

    _add_price_row(fig, row=1)

    fig.add_trace(
        go.Bar(
            x=HOUR_CENTERS,
            y=_mw_to_kw(buy_mwh),
            width=0.88,
            name="Buy from grid",
            marker=dict(color=MARKET_BUY_COLOR, line=dict(color=BACKGROUND_COLOR, width=1)),
            hovertemplate="%{y:.1f} kW<extra>Buy</extra>",
        ),
        row=2,
        col=1,
    )
    fig.add_trace(
        go.Bar(
            x=HOUR_CENTERS,
            y=[-v for v in _mw_to_kw(sell_mwh)],
            width=0.88,
            name="Sell to grid (V2G)",
            marker=dict(color=MARKET_PRICE_COLOR, line=dict(color=BACKGROUND_COLOR, width=1)),
            hovertemplate="%{y:.1f} kW<extra>Sell</extra>",
        ),
        row=2,
        col=1,
    )

    fig.update_xaxes(range=[0, 24], dtick=3)
    fig.update_xaxes(title="Hour of day", row=2, col=1)
    fig.update_yaxes(title="Price", rangemode="tozero", row=1, col=1)
    fig.update_yaxes(title="Power (kW)", row=2, col=1)
    fig.update_layout(
        title=dict(text="Buy Low, Sell High", x=0.5),
        barmode="relative",
        hovermode="x unified",
        legend=dict(x=0.5, y=-0.15, xanchor="center", yanchor="top", orientation="h"),
        margin=dict(l=40, r=40, t=60, b=90),
    )

    _save_figure(fig, "depot_charging_economics")


def _check_depot_charging_claims(result: OptimalDispatchResults) -> None:
    """Fail the docs build if the solve no longer matches what depot_charging.md says.

    Only claims that hold in every optimal solution are checked. Hours with the same price
    are interchangeable, so which of them the solver uses is not checked.
    """
    ev_dataset = result.electric_vehicles.to_dataset()
    prices = np.array(MARKET_PRICES)

    end_soc = {ev.name: float(ev_dataset.sel(ev=ev.name).soc.values[-1]) for ev in EVS}
    np.testing.assert_allclose(list(end_soc.values()), [0.3, 0.6, 0.5], atol=1e-6, err_msg=str(end_soc))

    net_power = ev_dataset.net_power.transpose(ElectricVehicleFormulation.dimension, ...).values
    discharging = (net_power < -ACTIVE_POWER_TOLERANCE).sum(axis=0)
    evening_peak = prices == prices.max()
    np.testing.assert_array_equal(
        discharging[evening_peak],
        len(CHARGERS),
        err_msg="every charger should be discharging a van at each evening peak step",
    )

    charging = (net_power > ACTIVE_POWER_TOLERANCE).any(axis=0)
    np.testing.assert_array_equal(
        np.flatnonzero(charging & (prices > MIDDAY_PRICE)),
        [],
        err_msg="the vans should charge only at the overnight and midday prices",
    )


def generate_depot_charging() -> None:
    """Solve the depot charging example once and generate all figures."""
    result = run_depot_charging()
    _check_depot_charging_claims(result)
    generate_depot_charging_setup()
    generate_depot_charging_dispatch_combined(result)
    generate_depot_charging_verification(result)
    generate_depot_charging_economics(result)


if __name__ == "__main__":
    print("Generating example plots...")
    generate_merit_order_dispatch()
    generate_solar_storage()
    generate_demand_response()
    generate_make_or_buy()
    generate_day_ahead_or_intraday()
    generate_depot_charging()
    print("Done!")
