---
icon: fontawesome/solid/shield
---

# CVaR Market Risk

## Problem Description

This example asks a more realistic market question: how should the optimizer allocate limited generation capacity across markets when prices are uncertain?

Imagine we are right before the day-ahead market. We have a single gas turbine with 100 MW of available capacity, and we need to decide how much of that capacity to sell in the day-ahead market, `sdac`.

Because this decision has to be made now, we set `stage_fixed=True` for `sdac`. That means the committed volume must be the same across all scenarios.

We consider three equally likely scenarios. Both market prices vary across scenarios: `sdac` has modest price uncertainty (190, 200, 210 $/MWh), while `sidc` has wider price swings (280, 200, 140 $/MWh). This creates two markets with different risk profiles.

The example is built as a single 24-hour timestep because the main decision is one commitment: how much capacity should go to `sdac` before the uncertainty is resolved?

![CVaR decision timeline](/assets/examples/cvar_timeline.svg)

**Source**: [`examples/cvar_market_risk.py`](https://github.com/ramirocrc/odys/blob/main/examples/cvar_market_risk.py)

## Walkthrough

### 1. Define the generator and markets

The generator produces the energy, and the two markets represent different ways of selling it.

```python
from datetime import timedelta

from odys import (
    AssetPortfolio,
    CVaRTerm,
    EnergyMarket,
    EnergySystem,
    Generator,
    Objective,
    ProfitTerm,
    StochasticScenario,
    TradeDirection,
)

ccgt = Generator(name="ccgt", nominal_power=100.0, variable_cost=20.0)
portfolio = AssetPortfolio(assets=[ccgt])

sdac = EnergyMarket(
    name="sdac",
    max_trading_volume_per_step=150,
    stage_fixed=True,
    trade_direction=TradeDirection.SELL_ONLY,
)
sidc = EnergyMarket(
    name="sidc",
    stage_fixed=False,
    max_trading_volume_per_step=100,
    trade_direction=TradeDirection.SELL_ONLY,
)
```

The difference between the markets is the whole point. `sdac` is the market we must commit to now, so it is stage-fixed. `sidc` is the flexible market, so its volume can adapt after the scenario is known.

### 2. Create the scenarios

The three scenarios represent three possible price outcomes:

- `high`: the intraday market is attractive (280 $/MWh), so keeping capacity
  for `sidc` pays off.
- `mid`: both markets are similarly priced around 200 $/MWh.
- `low`: the intraday market is less attractive (140 $/MWh), but still profitable.

That spread is what creates the risk tradeoff. `sdac` has modest price variation
(190-210 $/MWh), while `sidc` swings more widely (140-280 $/MWh).

```python
scenarios = [
    StochasticScenario(
        name="high",
        probability=1 / 3,
        available_capacity_profiles={"ccgt": [100]},
        market_prices={"sdac": [190], "sidc": [280]},
    ),
    StochasticScenario(
        name="mid",
        probability=1 / 3,
        available_capacity_profiles={"ccgt": [100]},
        market_prices={"sdac": [200], "sidc": [200]},
    ),
    StochasticScenario(
        name="low",
        probability=1 / 3,
        available_capacity_profiles={"ccgt": [100]},
        market_prices={"sdac": [210], "sidc": [140]},
    ),
]
```

These scenarios are what introduce risk. Both markets have uncertainty, but
`sidc` has much higher variance, which is where the risk tradeoff comes from.

### 3. Compare profit only with profit plus CVaR

We first solve the model with profit only. This gives us the baseline: what the
optimizer would do if it cared only about average return.

```python
energy_system = EnergySystem(
    portfolio=portfolio,
    markets=[sdac, sidc],
    scenarios=scenarios,
    number_of_steps=1,
    timestep=timedelta(hours=24),
    objective=Objective(profit=ProfitTerm(weight=1)),
)

result_profit = energy_system.optimize()
```

This version should prefer `sidc`, because the high-price scenario pulls up the
average return enough to outweigh the weaker outcomes.

Now we add CVaR. This keeps the same market setup, but changes the objective so
the downside matters too.

```python
energy_system = EnergySystem(
    portfolio=portfolio,
    markets=[sdac, sidc],
    scenarios=scenarios,
    number_of_steps=1,
    timestep=timedelta(hours=24),
    objective=Objective(
        profit=ProfitTerm(weight=1),
        cvar=CVaRTerm(weight=1, confidence_level=0.6),
    ),
)

result_cvar = energy_system.optimize()
```

This is the key modeling move. Profit alone rewards the best average outcome, but CVaR puts weight on the lower tail and makes bad outcomes more expensive.

## Results

The chart below compares the optimal allocation across scenarios for both the
profit-only and CVaR-penalized runs. With profit alone, the optimizer sends
capacity to the riskier sidc market. Adding CVaR shifts most capacity to sdac,
with a small position in sidc to capture upside.

<iframe src="/assets/examples/cvar_market_risk.html" style="width:100%; height:500px; border:none;" loading="lazy"></iframe>

Profit-only result:

```text
scenario  time  market
high      0     sdac        0.0
                sidc      100.0
mid       0     sdac       -0.0
                sidc      100.0
low       0     sdac       -0.0
                sidc      100.0
```

This makes sense: the optimizer sends all 100 MW to `sidc` because it has slightly higher expected profit (18,667 vs 18,000).

Expected profit confirms that choice:

- `sdac`: `(190 - 20) × 100 = 17,000` in `high`, `(200 - 20) × 100 = 18,000`
  in `mid`, `(210 - 20) × 100 = 19,000` in `low`, so the expected profit is
  `(17,000 + 18,000 + 19,000) / 3 = 18,000`
- `sidc`: `(280 - 20) × 100 = 26,000` in `high`, `(200 - 20) × 100 = 18,000`
  in `mid`, `(140 - 20) × 100 = 12,000` in `low`, so the expected profit is
  `(26,000 + 18,000 + 12,000) / 3 = 18,667`

So `sidc` has the higher expected profit, which is why the profit-only model chooses it.

With CVaR added:

```text
scenario  time  market
high      0     sdac       87.5
                sidc       12.5
mid       0     sdac       87.5
                sidc       12.5
low       0     sdac       87.5
                sidc       12.5
```

This is the key change: once downside risk is penalized, the optimizer commits most capacity (~87.5 MW) to `sdac` across all scenarios, with a meaningful position (~12.5 MW) in `sidc` to capture upside in favorable scenarios.

The math backs this up. For the optimal mix (87.5 MW sdac + 12.5 MW sidc):

- **Scenario profits**: `high` = 18,125, `mid` = 18,000, `low` = 18,125
- **Expected profit**: (18,125 + 18,000 + 18,125) / 3 = 18,083
- **VaR (60th percentile)**: 18,125 (the optimizer pushes η to the maximum profit)
- **Shortfalls**: `high` = 0, `mid` = 125, `low` = 0
- **E[shortfall]**: (0 + 125 + 0) / 3 ≈ 41.67
- **CVaR**: 18,125 - 2.5 × 41.67 ≈ 18,021
- **Objective**: 18,083 + 18,021 = 36,104

Compare this to pure strategies:

- **100% sdac**: E[profit] = 18,000, CVaR ≈ 17,167, Objective ≈ 35,167
- **100% sidc**: E[profit] = 18,667, CVaR = 13,000, Objective ≈ 31,667

The mixed strategy (87.5/12.5) achieves a higher objective (36,104) than either pure strategy, demonstrating how CVaR creates value through diversification.

The important comparison is this:

- with profit only, the optimizer prefers `sidc` (100% allocation)
- with profit plus CVaR, the optimizer prefers `sdac` (~87.5% allocation)

The first result makes sense because `sidc` has the higher expected profit. The second result makes sense because CVaR makes the low-price case matter, and that makes the lower-variance `sdac` commitment more attractive. The more balanced allocation (87.5/12.5 instead of 95/5) reflects that `sidc` is still profitable in all scenarios, just with more variance.

## Discussion

This is the most advanced example in the set because it combines uncertainty, market participation, and risk aversion.

The useful intuition here is that expected value and risk are not the same thing. A decision that looks best on average can still be unattractive once you account for the bad tail outcomes. CVaR gives the optimizer a way to say, "I care about avoiding the painful scenarios, not just chasing the average."

In this example, both markets have uncertainty, but with very different profiles. `sdac` has modest price variation while `sidc` has wider swings. The profit-only objective goes all-in on the higher-variance market, while the CVaR-penalized objective favors the lower-variance option but still maintains a meaningful position in the riskier market. This is the core value of risk-aware optimization: it lets the model balance upside potential against downside exposure, resulting in more diversified allocations rather than extreme bets.
