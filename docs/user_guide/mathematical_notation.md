---
icon: lucide/sigma
---

# Mathematical notation

Let's collect the mathematical symbols used across the User Guide. The notation is aligned with the current optimization model implementation.

## Indices and sets

| Symbol | Meaning |
| ------ | ------- |
| $t$ | Timestep |
| $T$ | Final timestep |
| $\tau$ | Rolling-window timestep index |
| $s$ | Scenario |
| $s_0$ | First scenario |
| $g$ | Generator |
| $b$ | Storage asset |
| $l$ | Load |
| $m$ | Market |

## Objective and risk

| Symbol | Meaning |
| ------ | ------- |
| $\Pi_s$ | Per-scenario profit |
| $\pi_s$ | Scenario probability |
| $w_{\text{profit}}$ | Expected-profit weight |
| $w_{\text{risk}}$ | CVaR weight |
| $\eta$ | Value-at-risk threshold |
| $\xi_s$ | CVaR shortfall in scenario $s$ |
| $\alpha$ | CVaR confidence level |
| $\lambda_{m,t,s}$ | Market price |

## Generator symbols

| Symbol | Meaning |
| ------ | ------- |
| $p_{g,t,s}$ | Generator output |
| $u_{g,t,s}$ | Generator on/off status |
| $y^{start}_{g,t,s}$ | Startup indicator |
| $y^{shutdown}_{g,t,s}$ | Shutdown indicator |
| $P^{\max}_g$ | Generator nominal power |
| $P^{\min}_g$ | Generator minimum power when on |
| $R^{up}_g$ | Ramp-up limit |
| $R^{down}_g$ | Ramp-down limit |
| $U_g$ | Minimum up time |
| $\epsilon_g$ | Small numerical lower bound used when the generator is on |
| $A_{g,t,s}$ | Available-capacity profile |
| $c_g$ | Generator variable cost |
| $C^{start}_g$ | Generator startup cost |

## Storage symbols

| Symbol | Meaning |
| ------ | ------- |
| $p^{ch}_{b,t,s}$ | Charging power |
| $p^{dis}_{b,t,s}$ | Discharging power |
| $p^{net}_{b,t,s}$ | Net storage power |
| $SOC_{b,t,s}$ | State of charge |
| $SOC^{start}_b$ | Initial state of charge |
| $SOC^{end}_b$ | Final state of charge |
| $SOC^{min}_b$ | Minimum state of charge |
| $SOC^{max}_b$ | Maximum state of charge |
| $E_b$ | Storage energy capacity |
| $\eta^{ch}_b$ | Charging efficiency |
| $\eta^{dis}_b$ | Discharging efficiency |
| $\eta^{rt}_b$ | Round-trip efficiency |
| $z_{b,t,s}$ | Binary charging mode |
| $\Delta t$ | Timestep length in hours |

## Market symbols

| Symbol | Meaning |
| ------ | ------- |
| $v^{buy}_{m,t,s}$ | Bought volume |
| $v^{sell}_{m,t,s}$ | Sold volume |
| $V^{\max}_m$ | Market trading-volume limit |
| $z_{m,t,s}$ | Binary market trade mode |
| $x_{m,t,s}$ | Generic stage-fixed market variable |

## Load and balance symbols

| Symbol | Meaning |
| ------ | ------- |
| $d_{l,t,s}$ | Load demand |

The power-balance equation uses generation, storage discharge, and market buys on the supply side, and load, storage charge, and market sells on the demand side.

## Sign conventions

- $p^{net}_{b,t,s} = p^{ch}_{b,t,s} - p^{dis}_{b,t,s}$
- Positive storage `net_power` means charging.
- Negative storage `net_power` means discharging.
- Market sell volume contributes positively to profit.
- Market buy volume contributes negatively to profit.

## Next steps

Learn about [Multi-stage Optimization](multi_stage.md), a planned extension to the current two-stage stochastic framework.
