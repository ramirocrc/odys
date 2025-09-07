# Assets

Assets are the fundamental building blocks of energy systems in optimes. They represent energy generation, storage, and consumption components that can be optimized to meet system demands at minimum cost.

## Asset Types

### PowerGenerator

Represents electrical generators with configurable operational constraints:

- **Nominal Power**: Maximum generation capacity in MW
- **Variable Cost**: Operating cost per MWh generated
- **Ramp Rates**: Optional up/down ramping limits (MW/hour)
- **Minimum Up/Down Time**: Operational constraints for unit commitment
- **Startup/Shutdown Costs**: Fixed costs for changing operational state
- **Emission Factor**: CO2 emissions per MWh for environmental modeling

Example:
```python
from optimes.energy_system_models.assets.generator import PowerGenerator

generator = PowerGenerator(
    name="coal_plant",
    nominal_power=200.0,
    variable_cost=25.0,
    ramp_up=50.0,
    startup_cost=1000.0,
    emission_factor=820.0  # kg CO2/MWh
)
```

### Battery

Represents energy storage systems with comprehensive modeling capabilities:

- **Capacity**: Energy storage capacity in MWh
- **Max Power**: Maximum charge/discharge power in MW
- **Efficiency**: Separate charging and discharging efficiency values (0-1)
- **State of Charge**: Initial, final, minimum and maximum SOC constraints
- **Degradation Cost**: Optional cost per MWh cycled to model battery wear
- **Self-discharge**: Optional energy loss rate over time

Example:
```python
from optimes.energy_system_models.assets.storage import Battery

battery = Battery(
    name="lithium_battery",
    capacity=100.0,
    max_power=50.0,
    efficiency_charging=0.95,
    efficiency_discharging=0.95,
    soc_start=50.0,
    soc_end=50.0,
    soc_min=10.0,
    soc_max=90.0
)
```

## Asset Management

Assets are managed through the `AssetPortfolio` class, which provides:

- **Validation**: Ensures unique asset names and proper typing
- **Organization**: Groups assets by type for easy access
- **Filtering**: Methods to retrieve generators, batteries, or all assets

Example:
```python
from optimes.energy_system_models.assets.portfolio import AssetPortfolio

portfolio = AssetPortfolio()
portfolio.add_asset(generator)
portfolio.add_asset(battery)

# Access assets by type
generators = portfolio.generators
batteries = portfolio.batteries
all_assets = portfolio.assets
```

## Design Principles

- **Immutable**: All assets are frozen after creation to prevent accidental modification
- **Validated**: Pydantic models ensure data integrity and type safety
- **Extensible**: New asset types can be added by extending the `EnergyAsset` base class
- **Realistic**: Parameters reflect real-world operational constraints and physics
