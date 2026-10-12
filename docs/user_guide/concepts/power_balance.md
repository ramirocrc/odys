---
icon: lucide/scale
---

# Power balance

Odys models your system as a single bus. At every timestep and in every scenario, the power flowing in must equal the power flowing out. This is the constraint that ties all assets and markets together: a load can only be served if some generator, battery, or market supplies it.

## Supply and demand

| Supply side | Demand side |
| ----------- | ----------- |
| [Generator](../assets/generator.md) output | [FixedLoad](../assets/fixed_load.md) demand |
| [Battery](../assets/battery.md) discharge (stationary storage and EV V2G) | [FlexibleLoad](../assets/flexible_load.md) demand (base + adjustment) |
| [EnergyMarket](../markets/energy_market.md) purchases | Battery charging (stationary storage and EVs) |
| | EnergyMarket sales |

[Chargers](../assets/charger.md) are not in the balance: the vehicles connected to them are.

There is no network: power flows freely between all assets. Without markets, the portfolio has to cover its own demand, and creating the `EnergySystem` checks that enough supply exists (see [EnergySystem validation](energy_system.md#validation)).

## Mathematical formulation

See [Mathematical notation](../mathematical_notation.md) for every symbol.

### Constraints

$$
\begin{aligned}
& \sum_g p_{g,t,s}
+ \sum_b p^{dis}_{b,t,s}
+ \sum_m v^{buy}_{m,t,s} \\
& =
\sum_l d^{\text{fixed}}_{l,t,s}
+ \sum_l \left( d^{\text{base}}_{l,t,s} + \Delta d_{l,t,s} \right)
+ \sum_b p^{ch}_{b,t,s}
+ \sum_m v^{sell}_{m,t,s}
\qquad \forall t, s
\end{aligned}
$$

Here $b$ ranges over stationary storages and electric vehicles.

## Next steps

Each asset page ends with its power balance contribution. Start with [Generator](../assets/generator.md#power-balance-contribution).
