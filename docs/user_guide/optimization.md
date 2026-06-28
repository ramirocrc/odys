---
icon: lucide/arrow-up-down
---

# Optimization

Let's look at what happens when you call `energy_system.optimize()` -- the objective function, the constraints, and how to read the results.

See [Mathematical notation](mathematical_notation.md) for the full list of symbols used below.

## Objective function

Odys uses the full objective below:

$$
\max\; w_{\text{profit}} \sum_s \pi_s \Pi_s
+ w_{\text{risk}} \left(
\eta - \frac{1}{1-\alpha} \sum_s \pi_s \xi_s
\right)
$$

Where:

- $\Pi_s$ is the profit in scenario $s$
- $\pi_s$ is the probability of scenario $s$
- $\eta$ is the VaR threshold
- $\xi_s$ is the shortfall for scenario $s$
- $\alpha$ is the CVaR confidence level

The profit term is:

$$
\Pi_s = \sum_{t,m} \lambda_{m,t,s}\left(v^{sell}_{m,t,s} - v^{buy}_{m,t,s}\right)
- \sum_{t,g}\left(c_g p_{g,t,s} + C^{start}_g y^{start}_{g,t,s}\right)
$$

The current implementation includes market revenue/cost when market prices are provided, generator variable cost, and generator startup cost.

The risk term penalizes low-profit scenarios through CVaR. By default, that term is ignored, so the model behaves as risk-neutral. Use CVaR when you want to protect against bad outcomes, not just maximize expected profit.

$$
w_{\text{profit}} = 1, \qquad w_{\text{risk}} = 0
$$

If you enable CVaR, the shortfall variables satisfy:

$$
\xi_s \ge \eta - \Pi_s
$$

## Constraints

The optimizer respects these constraints:

### Power balance

At every timestep, supply must equal demand:

$$
\sum_g p_{g,t,s} + \sum_b p^{dis}_{b,t,s} + \sum_m v^{buy}_{m,t,s}
= \sum_l d_{l,t,s} + \sum_b p^{ch}_{b,t,s} + \sum_m v^{sell}_{m,t,s}
$$

This is the fundamental constraint: total supply must match total demand. Notice how it balances generation, storage discharge, and market buys on the supply side against load, storage charge, and market sells on the demand side.

### Generator constraints

For each generator:

$$
0 \le p_{g,t,s}, \qquad u_{g,t,s}, y^{start}_{g,t,s}, y^{shutdown}_{g,t,s} \in \{0,1\}
$$

$$
p_{g,t,s} - P^{\max}_g u_{g,t,s} \le 0
$$

$$
p_{g,t,s} \ge \epsilon_g u_{g,t,s}
$$

$$
p_{g,t,s} \ge P^{\min}_g u_{g,t,s}
$$

$$
p_{g,t,s} - p_{g,t-1,s} \le R^{up}_g
$$

$$
p_{g,t-1,s} - p_{g,t,s} \le R^{down}_g
$$

Startup and shutdown indicators satisfy:

$$
y^{start}_{g,t,s} \ge u_{g,t,s} - u_{g,t-1,s}
$$

$$
y^{start}_{g,t,s} \le u_{g,t,s}, \qquad y^{start}_{g,t,s} + u_{g,t-1,s} \le 1
$$

$$
y^{shutdown}_{g,t,s} \ge u_{g,t-1,s} - u_{g,t,s}
$$

$$
y^{shutdown}_{g,t,s} \le u_{g,t-1,s}, \qquad y^{shutdown}_{g,t,s} + u_{g,t,s} \le 1
$$

The current minimum-up-time implementation uses the shutdown indicator:

$$
\sum_{\tau=t-U_g+1}^{t} u_{g,\tau,s} \ge U_g y^{shutdown}_{g,t+1,s}
$$

If scenario available-capacity profiles are provided, generator power is also capped by them:

$$
p_{g,t,s} \le A_{g,t,s}
$$

### Storage constraints

For each storage asset:

$$
0 \le p^{ch}_{b,t,s}, \qquad 0 \le p^{dis}_{b,t,s}, \qquad 0 \le SOC_{b,t,s}, \qquad z_{b,t,s} \in \{0,1\}
$$

$$
p^{ch}_{b,t,s} \le z_{b,t,s} P^{\max}_b
$$

$$
p^{dis}_{b,t,s} + z_{b,t,s} P^{\max}_b \le P^{\max}_b
$$

$$
SOC_{b,t,s} = SOC_{b,t-1,s}
+ \eta^{ch}_b \frac{\Delta t}{E_b} p^{ch}_{b,t,s}
- \frac{\Delta t}{\eta^{dis}_b E_b} p^{dis}_{b,t,s}
$$

for $t > 0$. At the first timestep, the implementation applies:

$$
SOC_{b,0,s} = SOC^{start}_b
+ \eta^{ch}_b \frac{\Delta t}{E_b} p^{ch}_{b,0,s}
- \frac{\Delta t}{\eta^{dis}_b E_b} p^{dis}_{b,0,s}
$$

$$
SOC^{min}_b \le SOC_{b,t,s} \le SOC^{max}_b
$$

$$
SOC_{b,t,s} \le 1, \qquad SOC_{b,T,s} = SOC^{end}_b
$$

The reported net power variable is defined as:

$$
p^{net}_{b,t,s} = p^{ch}_{b,t,s} - p^{dis}_{b,t,s}
$$

### Market constraints

For each market:

$$
0 \le v^{sell}_{m,t,s} \le V^{\max}_m, \qquad 0 \le v^{buy}_{m,t,s} \le V^{\max}_m, \qquad z_{m,t,s} \in \{0,1\}
$$

Buy and sell are mutually exclusive through the binary trade-mode variable $z_{m,t,s}$:

$$
v^{sell}_{m,t,s} \le z_{m,t,s} V^{\max}_m
$$

$$
v^{buy}_{m,t,s} + z_{m,t,s} V^{\max}_m \le V^{\max}_m
$$

If a market is buy-only or sell-only, the unused direction is fixed to zero.

For `stage_fixed` markets:

$$
x_{m,t,s} = x_{m,t,s_0} \quad \forall s
$$

where $x$ is each market variable: buy volume, sell volume, and trade mode.

## Reading results

The `optimize()` call returns an `OptimizationResults` object:

```python
result = energy_system.optimize()
```

### Solver status

```python
result.solver_status  # "ok" if the solver found a solution
result.termination_condition  # "optimal" if it's the best possible solution
```

### Asset-specific results

Each asset type has its own results container:

```python
# Generators
result.generators.power  # MW dispatched per timestep
result.generators.status  # on/off (1/0)
result.generators.startup  # startup events
result.generators.shutdown  # shutdown events

# Storages
result.storages.net_power  # positive = charging, negative = discharging
result.storages.state_of_charge  # SOC at each timestep

# Markets
result.markets.sell_volume  # MW sold per market per timestep
result.markets.buy_volume  # MW bought per market per timestep
```

All of these are `pandas.DataFrame` objects, so you can use the full pandas API to slice, filter, and plot.

### Combined DataFrame

For a single view of everything:

```python
df = result.to_dataframe()
```

This gives you a multi-indexed DataFrame with all variables, units, and timesteps. For deterministic scenarios, the scenario index level is dropped automatically.

!!! tip

    If you're working in a notebook, `result.to_dataframe` is usually the quickest way to see what the optimizer did. You can export it with `.to_csv()` or plot it directly.

## Next steps

Want to switch solvers or tune solver options? See [Solvers](solvers.md) to configure the optimization backend.
