"""Generate interactive Plotly charts for example documentation.

Usage:
    uv run --locked python docs/generate_example_plots.py

Output:
    Writes standalone Plotly HTML files to docs/assets/examples/
    for embedding in zensical via <iframe>.
"""

import sys
from pathlib import Path

_project_root = str(Path(__file__).resolve().parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from examples.basic_dispatch import run_basic_dispatch  # pyrefly: ignore
from examples.battery_dispatch import run_battery_dispatch  # pyrefly: ignore
from examples.cvar_market_risk import run_cvar_market_risk  # pyrefly: ignore
from examples.ev_fleet_optimization import (  # pyrefly: ignore
    CHARGERS,
    EVS,
    MARKET_PRICES,
    run_ev_fleet_optimization,
)
from examples.flexible_load_market import run_flexible_load_market  # pyrefly: ignore
from examples.market_arbitrage import run_market_arbitrage  # pyrefly: ignore
from odys import Charger
from odys.optimization.model.sets import ModelDimension
from odys.results.optimization_results import OptimalDisptachResults

OUTPUT_DIR = Path(__file__).parent / "assets" / "examples"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

SOLAR_COLOR = "#2ECC71"
CCGT_COLOR = "#E67E22"
LOAD_COLOR = "#7F8C8D"
BATTERY_SOC_COLOR = "#3498DB"
BATTERY_DISCHARGE_COLOR = "#E74C3C"
BATTERY_CHARGE_COLOR = "#27AE60"
MARKET_BUY_COLOR = "#3498DB"
MARKET_PRICE_COLOR = "#E74C3C"
SDAC_COLOR = "#3498DB"
SIDC_COLOR = "#E67E22"
FLEXIBLE_LOAD_COLOR = "#3498DB"
VALUE_OF_CONSUMPTION_COLOR = "#E67E22"
EV_1_COLOR = "#3498DB"
EV_2_COLOR = "#E74C3C"
EV_3_COLOR = "#9B59B6"


def _save_figure(fig: go.Figure, name: str) -> None:
    path = OUTPUT_DIR / f"{name}.html"
    fig.update_layout(template=None)
    fig.write_html(path, include_plotlyjs="cdn")
    print(f"  \u2713 {path.name}")


def generate_basic_dispatch() -> None:
    """Stacked bar chart of generator dispatch with load overlay."""
    result = run_basic_dispatch()
    df = result.generators.to_dataframe()["power"].unstack("generator")
    steps = list(range(1, len(df) + 1))

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
            marker=dict(color=CCGT_COLOR),
        ),
    )

    solar_profile = [0, 0, 0, 0, 0, 0, 10, 30, 60, 90, 110, 120, 125, 120, 110, 90, 60, 30, 10, 0, 0, 0, 0, 0]

    fig.add_trace(
        go.Scatter(
            x=steps,
            y=solar_profile,
            mode="lines",
            name="Solar Capacity",
            line=dict(color=SOLAR_COLOR, width=2, dash="dash"),
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
        xaxis=dict(title="Time Step", range=[0.5, 24.5]),
        yaxis=dict(title="Power (MW)", range=[0, 150]),
        barmode="stack",
        hovermode="x unified",
        legend=dict(x=0.01, y=0.99),
        margin=dict(l=40, r=20, t=40, b=40),
    )

    _save_figure(fig, "basic_dispatch")


def generate_battery_dispatch() -> None:
    """Two-panel chart: generator dispatch with battery + battery SOC."""
    result = run_battery_dispatch()
    gen_df = result.generators.to_dataframe()["power"].unstack("generator")
    battery_df = result.standalone_storages.to_dataframe().droplevel("standalone_storage")
    steps = list(range(1, len(gen_df) + 1))

    fig = make_subplots(
        rows=2,
        cols=1,
        vertical_spacing=0.12,
        subplot_titles=("Dispatch", "Battery State of Charge"),
        row_heights=[0.7, 0.3],
    )

    # Split battery into discharge (positive) and charge (negative)
    battery_power = -battery_df["net_power"].values  # Invert so discharge is positive
    battery_discharge = [max(0, v) for v in battery_power]
    battery_charge = [min(0, v) for v in battery_power]

    # Calculate bases for stacking
    solar = gen_df["solar_pv"].values
    ccgt = gen_df["ccgt"].values
    solar_base = battery_discharge
    ccgt_base = [b + s for b, s in zip(battery_discharge, solar, strict=True)]

    fig.add_trace(
        go.Bar(
            x=steps,
            y=battery_discharge,
            base=0,
            name="Battery Discharge",
            marker=dict(color=BATTERY_SOC_COLOR),
            legendgroup="gen",
        ),
        row=1,
        col=1,
    )

    fig.add_trace(
        go.Bar(
            x=steps,
            y=solar,
            base=solar_base,
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
            base=ccgt_base,
            name="CCGT",
            marker=dict(color=CCGT_COLOR),
            legendgroup="gen",
        ),
        row=1,
        col=1,
    )

    fig.add_trace(
        go.Bar(
            x=steps,
            y=battery_charge,
            base=0,
            name="Battery Charge",
            marker=dict(color=BATTERY_SOC_COLOR),
            legendgroup="gen",
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
            legendgroup="gen",
        ),
        row=1,
        col=1,
    )

    soc = battery_df["soc"].values

    fig.add_trace(
        go.Scatter(
            x=steps,
            y=soc,
            mode="lines+markers",
            name="State of Charge (MWh)",
            line=dict(color=BATTERY_SOC_COLOR, width=2),
            marker=dict(size=6),
        ),
        row=2,
        col=1,
    )

    fig.update_layout(
        barmode="stack",
        hovermode="x unified",
        legend=dict(x=0.01, y=0.99),
        margin=dict(l=40, r=20, t=40, b=40),
    )

    fig.update_xaxes(title="Time Step", range=[0.5, 24.5], row=1, col=1)
    fig.update_xaxes(title="Time Step", range=[0.5, 24.5], row=2, col=1)
    fig.update_yaxes(title="Power (MW)", row=1, col=1, range=[-80, 200])
    fig.update_yaxes(title="Energy (MWh)", row=2, col=1, range=[0, 1])

    _save_figure(fig, "battery_dispatch")


def generate_market_arbitrage() -> None:
    """Two-panel chart: stacked dispatch bars + market prices."""
    result = run_market_arbitrage()
    gen_df = result.generators.to_dataframe()["power"].unstack("generator")
    buy_volume = result.markets.buy_volume.xs("market", level="market")
    steps = list(range(1, len(gen_df) + 1))

    market_prices = [80, 75, 70, 65, 60, 55, 50, 45, 40, 35, 30, 35, 40, 45, 50, 55, 60, 70, 80, 90, 85, 80, 75, 70]

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
            marker=dict(color=CCGT_COLOR),
        ),
        row=1,
        col=1,
    )

    fig.add_trace(
        go.Bar(
            x=steps,
            y=buy_volume.values,
            name="Market Purchases",
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
        barmode="stack",
        hovermode="x unified",
        legend=dict(x=0.5, y=1.02, xanchor="center", yanchor="bottom", orientation="h"),
        margin=dict(l=40, r=40, t=60, b=40),
    )

    fig.update_xaxes(title="Time Step", range=[0.5, 24.5], row=1, col=1)
    fig.update_xaxes(title="Time Step", range=[0.5, 24.5], row=2, col=1)
    fig.update_yaxes(title="Power (MW)", row=1, col=1)
    fig.update_yaxes(title="Price ($/MWh)", row=2, col=1)

    _save_figure(fig, "market_arbitrage")


def generate_flexible_load_market() -> None:
    """Two-panel chart: load consumption + market prices."""
    result = run_flexible_load_market()
    actual_load = result.flexible_loads.actual_load
    steps = list(range(1, len(actual_load) + 1))

    market_prices = [80, 75, 70, 65, 60, 55, 50, 45, 40, 35, 30, 35, 40, 45, 50, 55, 60, 70, 80, 90, 85, 80, 75, 70]

    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.12,
        subplot_titles=("Load Consumption", "Market Prices"),
        row_heights=[0.5, 0.5],
    )

    fig.add_trace(
        go.Scatter(
            x=steps,
            y=[60] * len(steps),
            mode="lines",
            name="Base Load (60 MW)",
            line=dict(color=LOAD_COLOR, width=2, dash="dash"),
        ),
        row=1,
        col=1,
    )

    fig.add_trace(
        go.Scatter(
            x=steps,
            y=actual_load.values,
            mode="lines+markers",
            name="Actual Consumption",
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

    fig.update_xaxes(title="Time Step", range=[0.5, 24.5], row=1, col=1)
    fig.update_xaxes(title="Time Step", range=[0.5, 24.5], row=2, col=1)
    fig.update_yaxes(title="Power (MW)", row=1, col=1, range=[0, 100])
    fig.update_yaxes(title="Price ($/MWh)", row=2, col=1)

    _save_figure(fig, "flexible_load_market")


def generate_cvar_market_risk() -> None:
    """Side-by-side grouped bar charts of market allocation for both runs."""
    result_profit, result_cvar = run_cvar_market_risk()

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
        sdac_profit = sell_profit.loc[(scenario, "sdac")]
        sidc_profit = sell_profit.loc[(scenario, "sidc")]
        sdac_cvar = sell_cvar.loc[(scenario, "sdac")]
        sidc_cvar = sell_cvar.loc[(scenario, "sidc")]

        fig.add_trace(
            go.Bar(
                x=[scenario],
                y=[sdac_profit],
                name="sdac",
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
                name="sidc",
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
                name="sdac",
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
                name="sidc",
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

    _save_figure(fig, "cvar_market_risk")


EV_COLORS = {"ev_1": EV_1_COLOR, "ev_2": EV_2_COLOR, "ev_3": EV_3_COLOR}
EV_V2G_COLOR = "#2980B9"
PRICE_STEP_COLOR = "#5D6D7E"
CUMULATIVE_PROFIT_COLOR = "#1E8449"
MARKER_OUTLINE_COLOR = "#2C3E50"
CHECK_OK_FILL = "rgba(46, 204, 113, 0.18)"
CHECK_FAIL_FILL = "rgba(231, 76, 60, 0.22)"
CHECK_OK_INK = "#1E8449"
CHECK_FAIL_INK = "#C0392B"
NEUTRAL_CELL_FILL = "rgba(0, 0, 0, 0)"
ACTIVE_POWER_TOLERANCE = 1e-6
ASSIGNMENT_THRESHOLD = 0.5
TRIP_POWER_TOLERANCE_KW = 1e-3
TRIP_COLOR = "#95A5A6"
CHARGING_COLOR = "#27AE60"
DISCHARGING_COLOR = "#E74C3C"

NUMBER_OF_HOURS = len(MARKET_PRICES)
HOUR_EDGES = list(range(NUMBER_OF_HOURS + 1))
HOUR_CENTERS = [t + 0.5 for t in range(NUMBER_OF_HOURS)]


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
        for trip in ev.trips:
            fig.add_vrect(
                x0=trip.start_time,
                x1=trip.end_time,
                fillcolor=EV_COLORS[ev.name],
                opacity=0.08,
                line_width=0,
                row=row,
                col=1,
            )


def _active_charger_segments(result: OptimalDisptachResults) -> list[tuple[str, str, int, int]]:
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


def _extract_ev_state_intervals(result: OptimalDisptachResults) -> list[tuple[str, str, int, int]]:
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

        intervals.extend((ev.name, "trip", trip.start_time, trip.end_time) for trip in ev.trips)

        is_charging = ev_power > ACTIVE_POWER_TOLERANCE
        is_discharging = ev_power < -ACTIVE_POWER_TOLERANCE

        for t in range(NUMBER_OF_HOURS):
            on_trip = any(trip.start_time <= t < trip.end_time for trip in ev.trips)
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


def generate_ev_fleet_setup() -> None:
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
    for ev in EVS:
        lane = lanes[ev.name]
        for i, trip in enumerate(ev.trips):
            fig.add_trace(
                go.Scatter(
                    x=[trip.start_time, trip.end_time],
                    y=[lane, lane],
                    mode="lines",
                    line=dict(color=TRIP_COLOR, width=16),
                    name="Trip (vehicle away)",
                    legendgroup="trip",
                    showlegend=i == 0,
                    text=f"{trip.name} (t{trip.start_time}-t{trip.end_time})",
                    hoverinfo="text",
                ),
                row=2,
                col=1,
            )
            fig.add_annotation(
                x=(trip.start_time + trip.end_time) / 2,
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

    _save_figure(fig, "ev_fleet_setup")


def generate_ev_fleet_dispatch_price() -> None:
    """Time-of-use price signal."""
    fig = go.Figure()
    fig.add_trace(_price_step_trace(show_legend=False))

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
        )

    fig.update_xaxes(range=[0, 24], dtick=3, title="Hour of day")
    fig.update_yaxes(title="Price ($/MWh)", rangemode="tozero")
    fig.update_layout(
        title=dict(text="Time-of-use price", x=0.5),
        hovermode="x unified",
        margin=dict(l=40, r=40, t=60, b=40),
    )

    _save_figure(fig, "ev_fleet_dispatch_price")


def generate_ev_fleet_dispatch_states(result: OptimalDisptachResults) -> None:
    """Vehicle states: trip, charging, discharging."""
    fig = go.Figure()

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
                showlegend=False,
                text=f"{_ev_display_name(ev_name)}: {state_names[state].lower()} (t{start}-t{end})",
                hoverinfo="text",
            ),
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
                showlegend=True,
            ),
        )

    fig.update_xaxes(range=[0, 24], dtick=3, title="Hour of day")
    fig.update_yaxes(
        tickvals=[2, 1, 0],
        ticktext=["EV 1", "EV 2", "EV 3"],
        range=[-0.6, 2.8],
    )
    fig.update_layout(
        title=dict(text="Vehicle states", x=0.5),
        hovermode="x unified",
        legend=dict(x=0.5, y=-0.2, xanchor="center", yanchor="top", orientation="h"),
        margin=dict(l=90, r=40, t=60, b=80),
    )

    _save_figure(fig, "ev_fleet_dispatch_states")


def generate_ev_fleet_dispatch_soc(result: OptimalDisptachResults) -> None:
    """State of charge for each EV."""
    fig = go.Figure()

    ev_dataset = result.electric_vehicles.to_dataset()
    for ev in EVS:
        soc_values = [ev.soc_start, *ev_dataset.sel(ev=ev.name).soc.values]
        fig.add_trace(
            go.Scatter(
                x=HOUR_EDGES,
                y=soc_values,
                mode="lines",
                name=ev.name,
                legendgroup=ev.name,
                line=dict(color=EV_COLORS[ev.name], width=2),
                hovertemplate="%{y:.2f}<extra>" + _ev_display_name(ev.name) + " SoC</extra>",
            ),
        )

    fig.update_xaxes(range=[0, 24], dtick=3, title="Hour of day")
    fig.update_yaxes(title="SoC", range=[0, 1.05], dtick=0.25)
    fig.update_layout(
        title=dict(text="State of charge", x=0.5),
        hovermode="x unified",
        legend=dict(x=0.5, y=-0.2, xanchor="center", yanchor="top", orientation="h"),
        margin=dict(l=40, r=40, t=60, b=80),
    )

    _save_figure(fig, "ev_fleet_dispatch_soc")


def generate_ev_fleet_dispatch_charger(result: OptimalDisptachResults) -> None:
    """Charger occupancy (powered hours only)."""
    fig = go.Figure()

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
                name=ev_name,
                legendgroup=ev_name,
                showlegend=ev_name not in shown_evs,
                text=f"{_ev_display_name(ev_name)} on {charger_name} (t{start}-t{end})",
                hoverinfo="text",
            ),
        )
        shown_evs.add(ev_name)

    fig.update_xaxes(range=[0, 24], dtick=3, title="Hour of day")
    fig.update_yaxes(
        tickvals=[1, 0],
        ticktext=[_charger_display_name(charger) for charger in CHARGERS],
        range=[-0.6, 1.6],
    )
    fig.update_layout(
        title=dict(text="Charger occupancy", x=0.5),
        hovermode="x unified",
        legend=dict(x=0.5, y=-0.2, xanchor="center", yanchor="top", orientation="h"),
        margin=dict(l=90, r=40, t=60, b=80),
    )

    _save_figure(fig, "ev_fleet_dispatch_charger")


def _constraint_check_rows(result: OptimalDisptachResults) -> list[tuple[str, str, str, bool]]:
    """Compute every trip, SoC, and charger constraint check from the solved result."""
    tolerance = 1e-6
    ev_dataset = result.electric_vehicles.to_dataset()
    assignment = result.chargers.to_dataset()["assignment"]
    rows: list[tuple[str, str, str, bool]] = []

    for ev in EVS:
        soc_values = ev_dataset.sel(ev=ev.name).soc.values
        for trip in ev.trips:
            actual = float(soc_values[trip.start_time - 1]) if trip.start_time > 0 else ev.soc_start
            rows.append((
                f"{_ev_display_name(ev.name)} SoC before {trip.name} (t{trip.start_time})",
                f"≥ {trip.min_soc_at_departure:.2f}",
                f"{actual:.3f}",
                actual >= trip.min_soc_at_departure - tolerance,
            ))

    for ev in EVS:
        if ev.soc_end is None:
            continue
        actual = float(ev_dataset.sel(ev=ev.name).soc.values[-1])
        rows.append((
            f"{_ev_display_name(ev.name)} end-of-day SoC",
            f"= {ev.soc_end:.2f}",
            f"{actual:.3f}",
            abs(actual - ev.soc_end) <= tolerance,
        ))

    worst_trip_power_kw = 0.0
    for ev in EVS:
        net_power = ev_dataset.sel(ev=ev.name).net_power.values
        for trip in ev.trips:
            trip_power = float(np.abs(net_power[trip.start_time : trip.end_time]).max()) * 1000
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
        most_evs = float(connected.sum(ModelDimension.EVs.value).max())
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


def generate_ev_fleet_verification(result: OptimalDisptachResults) -> None:
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
        print(f"WARNING: EV fleet verification check failed: {failed_check}", file=sys.stderr)

    fig = go.Figure(
        data=[
            go.Table(
                columnwidth=[0.46, 0.16, 0.2, 0.18],
                header=dict(
                    values=["<b>Check</b>", "<b>Requirement</b>", "<b>Result</b>", "<b>Status</b>"],
                    fill_color="#ECF0F1",
                    font=dict(color=MARKER_OUTLINE_COLOR, size=12),
                    align=["left", "center", "center", "center"],
                    height=30,
                ),
                cells=dict(
                    values=[checks, requirements, actuals, statuses],
                    fill_color=[NEUTRAL_CELL_FILL, NEUTRAL_CELL_FILL, NEUTRAL_CELL_FILL, status_fills],
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

    _save_figure(fig, "ev_fleet_verification")


def generate_ev_fleet_economics(result: OptimalDisptachResults) -> None:
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
            marker=dict(color=MARKET_BUY_COLOR, line=dict(color="#FFFFFF", width=1)),
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
            marker=dict(color=MARKET_PRICE_COLOR, line=dict(color="#FFFFFF", width=1)),
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

    _save_figure(fig, "ev_fleet_economics")


def generate_ev_fleet_optimization() -> None:
    """Solve the EV fleet example once and generate all four figures."""
    result = run_ev_fleet_optimization()
    generate_ev_fleet_setup()
    generate_ev_fleet_dispatch_price()
    generate_ev_fleet_dispatch_states(result)
    generate_ev_fleet_dispatch_soc(result)
    generate_ev_fleet_dispatch_charger(result)
    generate_ev_fleet_verification(result)
    generate_ev_fleet_economics(result)


if __name__ == "__main__":
    print("Generating example plots...")
    generate_basic_dispatch()
    generate_battery_dispatch()
    generate_flexible_load_market()
    generate_market_arbitrage()
    generate_cvar_market_risk()
    generate_ev_fleet_optimization()
    print("Done!")
