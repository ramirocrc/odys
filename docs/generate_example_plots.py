"""Generate interactive Plotly charts for example documentation.

Usage:
    uv run --locked python docs/generate_example_plots.py

Output:
    Writes Plotly JSON files to docs/assets/examples/
    for embedding in mkdocs via mkdocs-plotly-plugin.
"""

import sys
from pathlib import Path

_project_root = str(Path(__file__).resolve().parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

import plotly.graph_objects as go
from plotly.subplots import make_subplots

from examples.basic_dispatch import run_basic_dispatch  # pyrefly: ignore
from examples.battery_dispatch import run_battery_dispatch  # pyrefly: ignore
from examples.cvar_market_risk import run_cvar_market_risk  # pyrefly: ignore
from examples.market_arbitrage import run_market_arbitrage  # pyrefly: ignore

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


def _save_figure(fig: go.Figure, name: str) -> None:
    path = OUTPUT_DIR / f"{name}.json"
    fig.update_layout(template=None)
    path.write_text(fig.to_json())
    print(f"  \u2713 {path.name}")


def generate_basic_dispatch() -> None:
    """Stacked area chart of generator dispatch with load overlay."""
    result = run_basic_dispatch()
    df = result.generators.to_dataframe()["power"].unstack("generator")
    steps = list(range(1, len(df) + 1))

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=steps,
            y=df["solar_pv"],
            mode="lines",
            fill="tozeroy",
            name="Solar PV",
            line=dict(color=SOLAR_COLOR, width=1),
            stackgroup="generation",
        ),
    )

    fig.add_trace(
        go.Scatter(
            x=steps,
            y=df["ccgt"],
            mode="lines",
            fill="tonexty",
            name="CCGT",
            line=dict(color=CCGT_COLOR, width=1),
            stackgroup="generation",
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
        xaxis=dict(title="Time Step"),
        yaxis=dict(title="Power (MW)", range=[0, 180]),
        hovermode="x unified",
        legend=dict(x=0.01, y=0.99),
        margin=dict(l=40, r=20, t=40, b=40),
    )

    _save_figure(fig, "basic_dispatch")


def generate_battery_dispatch() -> None:
    """Two-panel chart: generator dispatch + battery SOC and power."""
    result = run_battery_dispatch()
    gen_df = result.generators.to_dataframe()["power"].unstack("generator")
    battery_df = result.storages.to_dataframe().droplevel("storage")
    steps = list(range(1, len(gen_df) + 1))

    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.12,
        subplot_titles=("Generator Dispatch", "Battery State"),
    )

    fig.add_trace(
        go.Scatter(
            x=steps,
            y=gen_df["solar_pv"],
            mode="lines",
            fill="tozeroy",
            name="Solar PV",
            line=dict(color=SOLAR_COLOR, width=1),
            stackgroup="gen",
            legendgroup="gen",
        ),
        row=1,
        col=1,
    )

    fig.add_trace(
        go.Scatter(
            x=steps,
            y=gen_df["ccgt"],
            mode="lines",
            fill="tonexty",
            name="CCGT",
            line=dict(color=CCGT_COLOR, width=1),
            stackgroup="gen",
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
    net_power = battery_df["net_power"].values

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

    bar_colors = [BATTERY_DISCHARGE_COLOR if v > 0 else BATTERY_CHARGE_COLOR for v in net_power]
    fig.add_trace(
        go.Bar(
            x=steps,
            y=net_power,
            name="Net Power (discharge +)",
            marker=dict(color=bar_colors),
            opacity=0.7,
        ),
        row=2,
        col=1,
    )

    fig.update_layout(
        hovermode="x unified",
        legend=dict(x=0.01, y=0.99),
        margin=dict(l=40, r=20, t=40, b=40),
    )

    fig.update_xaxes(title="Time Step", row=2, col=1)
    fig.update_yaxes(title="Power (MW)", row=1, col=1, range=[0, 180])
    fig.update_yaxes(title="Energy (MWh)", row=2, col=1)

    _save_figure(fig, "battery_dispatch")


def generate_market_arbitrage() -> None:
    """Dual-axis chart: generation vs market purchases with price overlay."""
    result = run_market_arbitrage()
    gen_df = result.generators.to_dataframe()["power"].unstack("generator")
    buy_volume = result.markets.buy_volume.xs("market", level="market")
    steps = list(range(1, len(gen_df) + 1))

    market_prices = [80, 70, 40, 30, 30, 80, 90, 60, 40]

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=steps,
            y=gen_df["ccgt"],
            name="CCGT Generation",
            marker=dict(color=CCGT_COLOR),
            opacity=0.8,
            yaxis="y",
        ),
    )

    fig.add_trace(
        go.Bar(
            x=steps,
            y=buy_volume.values,
            name="Market Purchases",
            marker=dict(color=MARKET_BUY_COLOR),
            opacity=0.8,
            yaxis="y",
        ),
    )

    fig.add_trace(
        go.Scatter(
            x=steps,
            y=market_prices,
            mode="lines+markers",
            name="Market Price ($/MWh)",
            line=dict(color=MARKET_PRICE_COLOR, width=2),
            marker=dict(size=8),
            yaxis="y2",
        ),
    )

    fig.add_trace(
        go.Scatter(
            x=steps,
            y=[50] * len(steps),
            mode="lines",
            name="CCGT Cost (50 $/MWh)",
            line=dict(color=MARKET_PRICE_COLOR, width=1, dash="dot"),
            yaxis="y2",
        ),
    )

    fig.update_layout(
        title=dict(text="Market Arbitrage Dispatch", x=0.5),
        xaxis=dict(title="Time Step"),
        yaxis=dict(title="Power (MW)", side="left"),
        yaxis2=dict(
            title="Price ($/MWh)",
            side="right",
            overlaying="y",
            rangemode="tozero",
        ),
        barmode="group",
        hovermode="x unified",
        legend=dict(x=0.01, y=0.99),
        margin=dict(l=40, r=40, t=40, b=40),
    )

    _save_figure(fig, "market_arbitrage")


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
        barmode="group",
        hovermode="x unified",
        legend=dict(x=0.5, y=-0.15, orientation="h"),
        margin=dict(l=40, r=20, t=40, b=60),
    )

    fig.update_xaxes(title="Scenario", row=1, col=1)
    fig.update_xaxes(title="Scenario", row=1, col=2)
    fig.update_yaxes(title="Volume (MW)", row=1, col=1, rangemode="tozero")

    _save_figure(fig, "cvar_market_risk")


if __name__ == "__main__":
    print("Generating example plots...")
    generate_basic_dispatch()
    generate_battery_dispatch()
    generate_market_arbitrage()
    generate_cvar_market_risk()
    print("Done!")
