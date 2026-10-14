---
icon: lucide/sigma
---

# Mathematical notation

This page collects the mathematical symbols used across the User Guide. Each asset and market page writes its own formulation with these symbols.

The subscripts say what a symbol belongs to: $z_{b,t,s}$ is a battery's charging mode and $z_{m,t,s}$ a market's trade mode, and $D_g$ is a generator's minimum down time while $D^{\min}_l$ and $D^{\max}_l$ are a load's bounds.

## Indices and sets

| Symbol | Meaning |
| ------ | ------- |
| $t$ | Timestep |
| $T$ | Final timestep |
| $\tau$ | Timestep inside a minimum up or down time window (summation index) |
| $s$ | Scenario |
| $s_0$ | First scenario |
| $g$ | Generator |
| $b$ | Battery-backed asset (stationary storage or electric vehicle) |
| $e$ | Electric vehicle |
| $c$ | Charger |
| $k$ | EV trip |
| $l$ | Load |
| $m$ | Market |

## Objective and risk

| Symbol | Meaning |
| ------ | ------- |
| $\Pi_s$ | Per-scenario profit |
| $\pi_s$ | Scenario probability |
| $w_{\text{profit}}$ | Expected-profit weight |
| $w_{\text{risk}}$ | CVaR weight |
| $\zeta$ | Value-at-risk threshold |
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
| $U_g$ | Minimum up time, in steps |
| $D_g$ | Minimum down time, in steps |
| $p^0_g$ | Output just before the first step (initial state) |
| $u^0_g$ | Status just before the first step, 1 if $p^0_g > 0$ |
| $T^0_g$ | Steps already spent in the initial status |
| $H^{up}_{g,t}$, $H^{down}_{g,t}$ | Steps on (off) before the first step that fall in the minimum up (down) time window ending at $t$ |
| $p^{end}_g$ | Output at the last step (final state) |
| $\epsilon_g$ | Small numerical lower bound used when the generator is on |
| $A_{g,t,s}$ | Available-capacity profile |
| $c_g$ | Generator variable cost |
| $C^{start}_g$ | Generator startup cost |
| $C^{shutdown}_g$ | Generator shutdown cost |

## Storage symbols

| Symbol | Meaning |
| ------ | ------- |
| $p^{ch}_{b,t,s}$ | Charging power |
| $p^{dis}_{b,t,s}$ | Discharging power |
| $p^{net}_{b,t,s}$ | Net storage power |
| $SOC_{b,t,s}$ | State of charge (fraction of capacity) |
| $SOC^{start}_b$ | Initial state of charge (initial state) |
| $SOC^{end}_b$ | Final state of charge (final state) |
| $SOC^{min}_b$ | Minimum state of charge |
| $SOC^{max}_b$ | Maximum state of charge |
| $E_b$ | Storage energy capacity |
| $P^{ch,\max}_b$ | Maximum charging power |
| $P^{dis,\max}_b$ | Maximum discharging power |
| $\eta^{ch}_b$ | Charging efficiency |
| $\eta^{dis}_b$ | Discharging efficiency |
| $\eta^{rt}_b$ | Round-trip efficiency |
| $\delta_b$ | Self-discharge rate per hour |
| $z_{b,t,s}$ | Binary charging mode |
| $\Delta t$ | Timestep length in hours |
| $c^{deg}_b$ | Storage degradation cost |

## Electric vehicle and charger symbols

| Symbol | Meaning |
| ------ | ------- |
| $p^{ch}_{e,t,s}$ | EV charging power |
| $p^{dis}_{e,t,s}$ | EV discharging power |
| $p^{net}_{e,t,s}$ | EV net power |
| $SOC_{e,t,s}$ | EV state of charge |
| $a_{c,e,t,s}$ | Binary charger-to-EV assignment |
| $P^{\max}_c$ | Charger maximum power |
| $\Delta SOC^{trip}_{e,t}$ | Trip energy drop as a fraction of capacity |
| $\omega_{e,t}$ | 1 while the EV is driving |
| $SOC^{dep}_{e,t}$ | Minimum SoC at departure, at the trip's start step |
| $E^{trip}_k$ | Energy consumed by trip $k$ |
| $t^{start}_k$, $t^{end}_k$ | Start and end step of trip $k$: its `start_time` and `end_time` divided by $\Delta t$ |

Electric vehicles reuse the [Battery](assets/battery.md#mathematical-formulation) symbols with $b = e$.

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
| $d^{\text{fixed}}_{l,t,s}$ | Fixed load demand |
| $d^{\text{base}}_{l,t,s}$ | Flexible load base demand |
| $\Delta d_{l,t,s}$ | Flexible load adjustment (positive = increase, negative = decrease) |
| $\Delta d^{\max+}_l$ | Maximum increase above base profile |
| $\Delta d^{\max-}_l$ | Maximum decrease below base profile |
| $D^{\min}_l$ | Absolute minimum consumption (`min_load`) |
| $D^{\max}_l$ | Absolute maximum consumption (`max_load`) |
| $d_{l,t,s}$ | Actual flexible load consumption, $d^{\text{base}}_{l,t,s} + \Delta d_{l,t,s}$ |
| $v_l$ | Value of consumption (economic value per MWh) |

See [Power balance](concepts/power_balance.md) and [FlexibleLoad](assets/flexible_load.md#mathematical-formulation) for how these symbols are used.

## Sign conventions

- $p^{net}_{b,t,s} = p^{ch}_{b,t,s} - p^{dis}_{b,t,s}$
- Positive storage/EV `net_power` means charging.
- Negative storage/EV `net_power` means discharging.
- Market sell volume contributes positively to profit.
- Market buy volume contributes negatively to profit.

## Next steps

See the [Examples](../examples/index.md) for end-to-end worked problems.
