---
icon: lucide/target
---

# Objective

When you call `energy_system.optimize()`, Odys maximizes an objective built from two terms: the expected profit across scenarios and, optionally, a risk term (CVaR) that protects against bad outcomes.

## Basic usage

By default, Odys maximizes expected profit. Configure the objective with `Objective`, `ProfitTerm`, and `CVaRTerm`:

```python
from odys import CVaRTerm, Objective, ProfitTerm

objective = Objective(
    terms=(
        ProfitTerm(weight=1.0),
        CVaRTerm(weight=0.5, confidence_level=0.95),
    ),
)

energy_system = EnergySystem(..., objective=objective)
```

## Fields

`Objective`:

| Field   | Type                 | Required | Default            | Description                                  |
| ------- | -------------------- | -------- | ------------------ | -------------------------------------------- |
| `terms` | `tuple` of terms     | No       | `(ProfitTerm(weight=1.0),)` | The terms of the objective                   |

An `Objective` holds a tuple of terms: a `ProfitTerm` is required, a `CVaRTerm` is optional, and each type appears at most once (otherwise building it raises an `OdysValidationError`). `Objective()` is the default, `Objective(terms=(ProfitTerm(weight=1.0),))`, which maximizes expected profit. Read a term back with `objective.term_of(CVaRTerm)`.

| Term         | Field              | Description                                                      |
| ------------ | ------------------ | ---------------------------------------------------------------- |
| `ProfitTerm` | `weight`           | Weight $w_{\text{profit}}$ of the expected profit                |
| `CVaRTerm`   | `weight`           | Weight $w_{\text{risk}}$ of the CVaR                             |
| `CVaRTerm`   | `confidence_level` | Confidence level $\alpha$; the CVaR averages the worst $1-\alpha$ of outcomes |

## Profit

The profit of a scenario adds up the market revenue and every asset's costs and values. Each asset page explains its own contribution; the sum is shown [below](#math-profit).

## Risk (CVaR)

The risk term penalizes low-profit scenarios through the conditional value at risk (CVaR): the expected profit in the worst $1-\alpha$ share of scenarios. Without a `CVaRTerm`, the model is risk-neutral. Use CVaR when you want to protect against bad outcomes, not just maximize expected profit.

See the [CVaR Market Risk example](../../examples/cvar_market_risk.md) for a worked scenario.

## Mathematical formulation

See [Mathematical notation](../mathematical_notation.md) for every symbol.

### Objective

$$
\max\; w_{\text{profit}} \sum_s \pi_s \Pi_s
+ w_{\text{risk}} \left(
\eta - \frac{1}{1-\alpha} \sum_s \pi_s \xi_s
\right)
$$

Without a `CVaRTerm`, $w_{\text{risk}} = 0$ and the CVaR variables are not created.

### Profit {#math-profit}

$\Pi_s$ is the sum of every asset and market contribution:

$$
\begin{aligned}
\Pi_s =
& \sum_{t,m} \lambda_{m,t,s} \, \Delta t \left(v^{sell}_{m,t,s} - v^{buy}_{m,t,s}\right) \\
& - \sum_{t,g}\left(c_g \, \Delta t \, p_{g,t,s} + C^{start}_g y^{start}_{g,t,s} + C^{shutdown}_g y^{shutdown}_{g,t,s}\right) \\
& + \sum_{t,l} v_l \, \Delta t \, \Delta d_{l,t,s} \\
& - \sum_{t,b} c^{deg}_b \, \Delta t \left(p^{ch}_{b,t,s} + p^{dis}_{b,t,s}\right)
\end{aligned}
$$

| Term | Defined on |
| ---- | ---------- |
| Market revenue | [EnergyMarket](../markets/energy_market.md#math-objective) |
| Generation cost | [Generator](../assets/generator.md#objective-contribution) |
| Value of flexible consumption | [FlexibleLoad](../assets/flexible_load.md#math-objective) |
| Degradation cost ($b$ over stationary storages and EVs) | [Battery](../assets/battery.md#math-objective) |

Prices and costs are per MWh, while volumes and powers are in MW, so every energy term is multiplied by the timestep length $\Delta t$ in hours. Startup and shutdown costs are charged per event, so they are not scaled.

### CVaR

| Symbol | Domain | Meaning |
| ------ | ------ | ------- |
| $\eta$ | $\mathbb{R}$ | Value at risk |
| $\xi_s$ | $\ge 0$ | Shortfall of scenario $s$ below $\eta$ |

$$
\xi_s \ge \eta - \Pi_s
$$

## Next steps

See [Stochastic optimization](stochastic.md) to optimize across several scenarios, or [Results](results.md) to read what the optimizer decided.
