# Minimal Example

This page demonstrates a minimal example of using the optimes library for energy system optimization. The example creates a simple energy system with generators and batteries, then optimizes the system operation to meet demand at minimum cost.

## Step-by-Step Example

### 1. Import Required Modules

Start by importing the necessary components for energy system optimization:

```python
from datetime import timedelta

from optimes.energy_system import EnergySystem
from optimes.energy_system_models.assets.generator import PowerGenerator
from optimes.energy_system_models.assets.portfolio import AssetPortfolio
from optimes.energy_system_models.assets.storage import Battery
```

### 2. Create Power Generators

Create two power generators with different characteristics:

- **Generator 1**: 100 MW capacity with 20 cost units per MW
- **Generator 2**: 150 MW capacity with 25 cost units per MW

```python
generator_1 = PowerGenerator(
    name="gen1",
    nominal_power=100.0,
    variable_cost=20.0,
)
generator_2 = PowerGenerator(
    name="gen2",
    nominal_power=150.0,
    variable_cost=25.0,
)
```

### 3. Create Battery Storage

Configure a battery storage system with the following specifications:

- Maximum power: 200 MW
- Capacity: 100 MWh
- Perfect efficiency (100% for both charging and discharging)
- Initial state of charge: 100%
- Terminal state of charge: 50%

```python
battery_1 = Battery(
    name="battery1",
    max_power=200.0,
    capacity=100.0,
    efficiency_charging=1.0,
    efficiency_discharging=1.0,
    soc_start=100.0,
    soc_end=50.0,
)
```

### 4. Build Asset Portfolio

Add all assets to an `AssetPortfolio` object, which manages the collection of energy system components:

```python
portfolio = AssetPortfolio()
portfolio.add_asset(generator_1)
portfolio.add_asset(generator_2)
portfolio.add_asset(battery_1)
```

### 5. Define Energy System

Define the complete energy system with the asset portfolio, demand profile, and time step:

- The asset portfolio containing all assets
- A demand profile: [50, 75, 100, 125, 150] MW for 5 time periods
- Time step: 30 minutes

```python
energy_system = EnergySystem(
    portfolio=portfolio,
    demand_profile=[50, 75, 100, 125, 150],
    timestep=timedelta(minutes=30),
    power_unit="MW",
)
```

### 6. Run Optimization

Use the `EnergySystem.optimize()` method to find the optimal operation schedule that minimizes total cost while meeting demand:

```python
result = energy_system.optimize()
```

### 7. Access Results

Convert the optimization results to a pandas DataFrame for analysis:

```python
results_df = result.to_dataframe()
```

### 8. Example Results

The optimization produces the following results showing the optimal dispatch schedule:

|      | var_generator_power | var_generator_power | var_battery_charge | var_battery_discharge | var_battery_soc | var_battery_charge_mode |
| ---- | ------------------- | ------------------- | ------------------ | --------------------- | --------------- | ----------------------- |
| unit | gen1                | gen2                | battery1           | battery1              | battery1        | battery1                |
| time |                     |                     |                    |                       |                 |                         |
| 0    | 50.0                | 0.0                 | 0.0                | 0.0                   | 100.0           | 0.0                     |
| 1    | 75.0                | 0.0                 | 0.0                | 0.0                   | 100.0           | 0.0                     |
| 2    | 100.0               | 0.0                 | 0.0                | 0.0                   | 100.0           | 0.0                     |
| 3    | 100.0               | 0.0                 | 0.0                | 25.0                  | 75.0            | 0.0                     |
| 4    | 100.0               | 25.0                | 0.0                | 25.0                  | 50.0            | 0.0                     |

**Results Interpretation:**

- **Time periods 0-2**: Only the cheaper generator (gen1) is used to meet demand, with the battery remaining fully charged
- **Time period 3**: Gen1 reaches its maximum capacity (100 MW), and the battery discharges 25 MW to meet the 125 MW demand
- **Time period 4**: Both generators are used (gen1 at 100 MW, gen2 at 25 MW) plus battery discharge (25 MW) to meet the 150 MW demand
- **Battery operation**: The battery discharges in the final periods to reach the required terminal state of charge (50%)

This optimal solution minimizes total cost by prioritizing the cheaper generator and using battery storage strategically.

## Next Steps

After running this example, you can:

- Analyze the optimization results to understand the optimal dispatch
- Modify asset parameters to explore different scenarios
- Add more complex constraints or objectives
- Scale up to larger systems with more assets and time periods
