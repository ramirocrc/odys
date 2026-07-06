"""Risk-aware market allocation with CVaR.

This example shows how Odys can trade off expected profit against downside
risk. The same generation can look attractive in expectation but still be a bad
choice once uncertain market prices are taken into account.

## Assets

- **ccgt**: 100 MW gas turbine, variable cost of 20 $/MWh, fully available
  across all scenarios.

## Markets

- **sdac**: Sell-only market with non-anticipative decisions (stage_fixed=True).
  Prices vary slightly by scenario: 190, 200, 210 $/MWh.
- **sidc**: Sell-only market with uncertain prices (stage_fixed=False).
  Prices vary by scenario: 500 (high), 200 (mid), 15 (low) $/MWh.

## Problem

We simulate a single 24-hour timestep with three equally likely scenarios.
The optimizer allocates the ccgt's 100 MW generation between two markets,
both with uncertain prices but different risk profiles.

Two optimizations are run:
1. **Expected profit only**: Maximize expected profit without CVaR penalty.
2. **With CVaR penalty (weight = 1)**: Penalize risk (downside exposure).

## Scenario Data

| Scenario | Probability | sdac Price | sidc Price | sdac Profit | sidc Profit |
|----------|-------------|------------|------------|-------------|-------------|
| high     | 1/3         | 190 $/MWh  | 500 $/MWh  | 17,000      | 48,000      |
| mid      | 1/3         | 200 $/MWh  | 200 $/MWh  | 18,000      | 18,000      |
| low      | 1/3         | 210 $/MWh  | 15 $/MWh   | 19,000      | -500        |

(Profit = (price - 20) * 100 MW)

## Expected Profit Analysis

**sdac (uncertain, but non-anticipative):**
- E[profit] = (17,000 + 18,000 + 19,000) / 3 = 18,000

**sidc (uncertain):**
- Allocating to sidc, the optimizer avoids the low scenario (price 15 < 20)
- High: 100 MW at 500 → 48,000
- Mid: 100 MW at 200 → 18,000
- Low: 0 MW produced → 0
- **E[profit] = (48,000 + 18,000 + 0) / 3 = 22,000**
- **sidc has 4,000 higher expected profit than sdac**

## CVaR Analysis (confidence_level = 0.6)

The objective uses: CVaR_expr = VaR - 2.5 x E[shortfall]
(with 2.5 = 1 / (1 - 0.6))

**For sdac:** Profits: [17,000, 18,000, 19,000]
- VaR (60th percentile) = 18,000
- Shortfalls: z_low = 18,000 - 17,000 = 1,000, z_mid = 0, z_high = 0
- E[shortfall] = (1,000 + 0 + 0) / 3 ≈ 333
- CVaR_expr = 18,000 - 2.5 x 333 ≈ **17,167**

**For sidc:** Profits: [0, 18,000, 48,000]
- VaR (60th percentile) = 18,000
- Shortfalls: z_low = 18,000 - 0 = 18,000, z_mid = 0, z_high = 0
- E[shortfall] = (18,000 + 0 + 0) / 3 = 6,000
- CVaR_expr = 18,000 - 2.5 x 6,000 = **3,000**

## Objective Function

Objective = profit_weight x E[profit] + cvar_weight x CVaR_expr

### Run 1: Expected Profit Only (no CVaR)

| Market | E[Profit] | Objective Value |
|--------|-----------|-----------------|
| sdac   | 18,000    | 18,000          |
| sidc   | 22,000    | 22,000          |

**Result:** sidc wins (22,000 > 18,000)
- sidc has 4,000 higher expected profit than sdac
- Optimizer sells 100 MW to sidc in high/mid scenarios, 0 MW in low

### Run 2: With CVaR Penalty (weight = 1)

The optimizer now finds an optimal mix rather than a pure allocation, since both
markets have uncertainty:

- **sdac**: ~94.7 MW in all scenarios (non-anticipative)
- **sidc**: ~5.3 MW in high/mid scenarios, 0 MW in low

**Result:** sdac dominates the allocation (~95% vs ~5%)
- The CVaR penalty strongly favors the lower-variance market
- A small sidc position captures upside in favorable scenarios
- Lower variance becomes more valuable than higher (but riskier) expected profit

## Critical CVaR Weight

There exists a critical CVaR weight above which the optimizer shifts from
primarily sidc to primarily sdac. Below this threshold, the higher expected
profit of sidc dominates; above it, the lower downside risk of sdac wins.

- **No CVaR (w = 0)**: Optimizer chooses **sidc** (higher expected profit)
- **Low CVaR weight**: Optimizer still prefers **sidc** (expected profit dominates)
- **High CVaR weight**: Optimizer shifts to **sdac** (downside risk dominates)

## Key Insight

This example is really about the shape of the decision, not just the final
profit number. A purely expected-value objective prefers the riskier market,
but once downside risk is penalized, the lower-variance market becomes more
attractive. That is the core value of CVaR: it makes the optimizer care about
bad outcomes, not only the average one.
"""

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
from odys.results.optimization_results import OptimalDisptachResults
from odys.utils.logging import get_logger, setup_rich_logging

setup_rich_logging()
logger = get_logger(__name__)


def run_cvar_market_risk() -> tuple[OptimalDisptachResults, OptimalDisptachResults]:
    """Run the CVaR market risk example and return both optimization results."""
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

    energy_system_max_expected_profit = EnergySystem(
        portfolio=portfolio,
        markets=[sdac, sidc],
        scenarios=scenarios,
        number_of_steps=1,
        timestep=timedelta(hours=24),
        objective=Objective(
            profit=ProfitTerm(weight=1),
        ),
    )
    result_max_expected_profit = energy_system_max_expected_profit.optimize()

    energy_system_penalized_cvar = EnergySystem(
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
    result_penalized_cvar = energy_system_penalized_cvar.optimize()

    return result_max_expected_profit, result_penalized_cvar


if __name__ == "__main__":
    result_max_expected_profit, result_penalized_cvar = run_cvar_market_risk()
    logger.info("optimal solution for max expected profit")
    logger.info(result_max_expected_profit.markets.sell_volume)

    logger.info("optimal solution penalizing cvar")
    logger.info(result_penalized_cvar.markets.sell_volume)
