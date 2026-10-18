---
icon: lucide/clock
---

# Time and units

odys plans over a horizon of equal steps, and it doesn't convert units: every value you give it is read in the units on this page. Getting these right is what makes the costs, the energy and the ramps come out as you expect.

## The horizon

The horizon is set by two parameters of the `EnergySystem`:

- `timestep`, a `timedelta` above zero: the length of every step, such as `timedelta(hours=1)` or `timedelta(minutes=15)`.
- `number_of_steps`, an integer of at least 1: how many steps the horizon has.

A day-ahead plan in quarter-hours is `timestep=timedelta(minutes=15)` with `number_of_steps=96`. All steps have the same length.

The horizon has no start date. Time labels count steps from the start of the run: `"0"`, `"1"`, `"2"` and so on, in the results too. Every time you give odys, such as a trip's departure, is measured from that start. To show results against clock time, see [Results](../solving/results.md#clock-time).

## Units

| Quantity                  | Unit           | Examples                                                        |
| ------------------------- | -------------- | --------------------------------------------------------------- |
| Power                     | MW             | `nominal_power`, `max_charge_power`, load and capacity profiles |
| Energy                    | MWh            | `capacity`, `energy_consumption`                                |
| Prices and variable costs | currency / MWh | `variable_cost`, `value_of_consumption`, `PriceProfile`         |
| Per-event costs           | currency       | `startup_cost`, `shutdown_cost`                                 |
| State of charge           | fraction (0-1) | `soc`, `soc_min`, `soc_max`                                     |

Profiles and decisions are powers, held for the whole step. The energy of a step is that power times the step length: 60 MW over a 15-minute step is 15 MWh. Prices and costs are per MWh, so odys multiplies them by the energy, and the currency is whatever your prices are in.

For a small asset, convert to MW yourself: a 22 kW charger is `0.022`.

## How each field reads time

Most fields are a power, an energy or a price. A few depend on the step length, and they don't all read it the same way:

| Field | Read as | With 15-minute steps |
| ----- | ------- | -------------------- |
| [`ramp_up`, `ramp_down`](../assets/generator.md#ramp-limits) | MW per step | 40 MW is 40 MW per quarter-hour, 160 MW per hour |
| [`self_discharge_rate`](../assets/battery.md#self-discharge) | Fraction per hour | 0.004 loses 0.1 % of the charge per step |
| [`variable_cost`](../assets/generator.md), [`value_of_consumption`](../assets/flexible_load.md#value-of-consumption), [`degradation_cost`](../assets/battery.md#degradation-cost), prices | Currency per MWh | 50 per MWh at 60 MW is 750 per step |
| [`startup_cost`, `shutdown_cost`](../assets/generator.md#startup-and-shutdown-cost) | Currency per event | Charged once per start, whatever the step length |
| [`min_up_time`, `min_down_time`](../assets/generator.md#minimum-up-and-down-time), [`time_in_state`](../assets/generator.md#initial-and-final-state) | `timedelta` | `timedelta(hours=1)` is 4 steps |
| [Trip `start_time`, `end_time`](../assets/electric_vehicle.md#trips) | `timedelta` from the start of the run | `timedelta(hours=7)` is the start of step 28 |

Every `timedelta` has to be a whole number of steps: `timedelta(minutes=50)` with 15-minute steps raises an `OdysValidationError` when you create the `EnergySystem`.

When you change the step length, check the per-step fields: a ramp limit written for hourly steps allows four times as much per hour with 15-minute steps.

## Horizon and problem size

The model grows with the number of steps times the number of scenarios. Generators, batteries, markets and chargers each add binary decisions at every step, which is what makes long, fine-grained horizons slow to solve. The [Mathematical Formulation](../../formulation/index.md#problem-class-and-size) lists which assets add binaries.

## Next steps

Next, see how [Profiles](profiles.md) give each asset and market its time series, one value per step.
