---
icon: fontawesome/solid/shield
---

# CVaR Market Risk

## Problem Description

This example asks a more realistic market question: how should the optimizer allocate limited generation capacity across markets when prices are uncertain?

Imagine we are right before the day-ahead market. We have a single gas turbine with 100 MW of available capacity, and we need to decide how much of that capacity to sell in the day-ahead market, `sdac`.

Because this decision has to be made now, we set `stage_fixed=True` for `sdac`. That means the committed volume must be the same across all scenarios.

We consider three equally likely scenarios. Both market prices vary across scenarios: `sdac` has modest price uncertainty (190, 200, 210 $/MWh), while `sidc` has much wider price swings (500, 200, 15 $/MWh). This creates two markets with different risk profiles.

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

- `high`: the intraday market is very attractive (500 $/MWh), so keeping capacity
  for `sidc` pays off.
- `mid`: both markets are similarly priced around 200 $/MWh.
- `low`: the intraday market collapses (15 $/MWh), so holding back capacity for
  `sidc` becomes a bad bet.

That spread is what creates the risk tradeoff. `sdac` has modest price variation
(190-210 $/MWh), while `sidc` swings dramatically (15-500 $/MWh).

```python
scenarios = [
    StochasticScenario(
        name="high",
        probability=1 / 3,
        available_capacity_profiles={"ccgt": [100]},
        market_prices={"sdac": [190], "sidc": [500]},
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
        market_prices={"sdac": [210], "sidc": [15]},
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
                sidc       -0.0
```

This makes sense: the optimizer sends all 100 MW to `sidc` when the price is
high or moderate, and it stays out of that market when the price falls below
the turbine's variable cost.

Expected profit confirms that choice:

- `sdac`: `(190 - 20) × 100 = 17,000` in `high`, `(200 - 20) × 100 = 18,000`
  in `mid`, `(210 - 20) × 100 = 19,000` in `low`, so the expected profit is
  `(17,000 + 18,000 + 19,000) / 3 = 18,000`
- `sidc`: `(500 - 20) × 100 = 48,000` in `high`, `(200 - 20) × 100 = 18,000`
  in `mid`, and `0` in `low`, so the expected profit is
  `(48,000 + 18,000 + 0) / 3 = 22,000`

So `sidc` really does have the higher expected profit, which is why the
profit-only model chooses it.

With CVaR added:

```text
scenario  time  market
high      0     sdac       94.736842
                sidc        5.263158
mid       0     sdac       94.736842
                sidc        5.263158
low       0     sdac        0.000000
                sidc        0.000000
```

This is the key change: once downside risk is penalized, the optimizer commits
most capacity (~95 MW) to `sdac` across all scenarios, with a small position
in `sidc` to capture upside in favorable scenarios.

The math backs this up. The CVaR term penalizes downside exposure:

- `sdac`: expected profit is `18,000`. Its scenario profits are `17,000`,
  `18,000`, and `19,000`, so the 60th-percentile VaR is `18,000`. The only
  shortfall is in the high scenario: `18,000 - 17,000 = 1,000`, and the
  average shortfall is `1,000 / 3 ≈ 333`. With confidence level `0.6`, the
  multiplier is `1 / (1 - 0.6) = 2.5`, so the CVaR term is
  `18,000 - 2.5 × 333 ≈ 17,167`
- `sidc`: expected profit is `22,000`. Its scenario profits are `0`, `18,000`,
  and `48,000`, so the 60th-percentile VaR is `18,000`. The only shortfall is
  in the low scenario: `18,000 - 0 = 18,000`, and the average shortfall is
  `18,000 / 3 = 6,000`. With confidence level `0.6`, the multiplier is
  `1 / (1 - 0.6) = 2.5`, so the CVaR term is
  `18,000 - 2.5 × 6,000 = 3,000`

So even though `sidc` has the better expected profit, `sdac` has much lower
downside risk, which is why the CVaR-penalized objective heavily favors it.

The important comparison is this:

- with profit only, the optimizer prefers `sidc`
- with profit plus CVaR, the optimizer heavily prefers `sdac`

The first result makes sense because `sidc` has the highest upside. The second
result makes sense because CVaR makes the low-price case matter, and that makes
the lower-variance `sdac` commitment more attractive.

## Discussion

This is the most advanced example in the set because it combines uncertainty, market participation, and risk aversion.

The useful intuition here is that expected value and risk are not the same thing. A decision that looks best on average can still be unattractive once you account for the bad tail outcomes. CVaR gives the optimizer a way to say, “I care about avoiding the painful scenarios, not just chasing the average.”

In this example, both markets have uncertainty, but with very different profiles. `sdac` has modest price variation while `sidc` has dramatic swings. The profit-only objective goes all-in on the higher-variance market, while the CVaR-penalized objective heavily favors the lower-variance option. This is the core value of risk-aware optimization: it lets the model balance upside potential against downside exposure.
