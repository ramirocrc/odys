---
icon: fontawesome/solid/charging-station
---

# Charger

A `Charger` is charging infrastructure for [ElectricVehicle](electric_vehicle.md) assets. Chargers do not participate in the power balance themselves. They track which EV is connected and enforce power limits on that connection.

## Basic usage

```python
from odys import Charger

charger_dc = Charger(name="charger_dc", max_power=0.050)  # 50 kW
charger_ac = Charger(name="charger_ac", max_power=0.022)  # 22 kW
```

Add chargers to the same portfolio as the EVs:

```python
from odys import AssetPortfolio

portfolio = AssetPortfolio([ev_1, ev_2, charger_dc, charger_ac])
```

## Fields

| Field        | Type    | Required | Default | Description                                             |
| ------------ | ------- | -------- | ------- | ------------------------------------------------------- |
| `name`       | `str`   | Yes      | -       | Unique identifier for the charger                       |
| `max_power`  | `float` | Yes      | -       | Maximum charge/discharge power through the charger (MW) |
| `efficiency` | `float` | No       | `1.0`   | Charger efficiency (0-1). Not yet used by the model     |

## Assignment rules

The optimizer decides charger-to-EV assignment at each timestep with these rules:

1. Each charger serves at most one EV at a time
2. Each EV connects to at most one charger at a time
3. An EV cannot be assigned to a charger while driving
4. Without a charger assigned, an EV cannot charge or discharge (including V2G)

That means charger capacity is a hard bottleneck. With 2 chargers and 3 EVs, the optimizer must decide who charges when based on trip deadlines and price signals.

See the [formulation](#math-assignment).

## Results

After optimization, access charger results through `result.chargers`:

```python
result = energy_system.optimize()

result.chargers.assignment  # binary assignment of EV to charger over time
result.chargers.power  # charging power delivered through each charger
```

## Mathematical formulation

See [Mathematical notation](../mathematical_notation.md) for every symbol.

### Variables

| Symbol | Result attribute | Domain | Meaning |
| ------ | ---------------- | ------ | ------- |
| $a_{c,e,t,s}$ | `assignment` | $\{0,1\}$ | 1 when vehicle $e$ is connected to charger $c$ |
| $\sum_e a_{c,e,t,s} \, p^{ch}_{e,t,s}$ | `power` | - | Charging power delivered through charger $c$ (reported, not a model variable) |

### Constraints

#### Assignment {#math-assignment}

$$
\sum_e a_{c,e,t,s} \le 1, \qquad
\sum_c a_{c,e,t,s} \le 1, \qquad
a_{c,e,t,s} \le 1 - \omega_{e,t}
$$

#### Power limit {#math-power-limit}

$$
p^{ch}_{e,t,s} + p^{dis}_{e,t,s} \le \sum_c P^{\max}_c \, a_{c,e,t,s}
$$

With no charger assigned, the right-hand side is 0, so the vehicle can neither charge nor discharge.

### Objective contribution

None.

### Power balance contribution

None: the vehicles connected to the chargers carry the power. See [ElectricVehicle](electric_vehicle.md#power-balance-contribution).

## Next steps

See the [EV Fleet example](../../examples/ev_fleet_optimization.md) for V2G arbitrage and charger competition, or [AssetPortfolio](../concepts/asset_portfolio.md) to combine chargers with the rest of your assets.
