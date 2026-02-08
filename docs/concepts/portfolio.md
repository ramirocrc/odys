# Portfolio Management

The `AssetPortfolio` class provides comprehensive management of energy system assets, acting as a container and organizer for generators, batteries, and other energy components.

## Core Functionality

### Asset Addition and Validation

The portfolio ensures that all assets meet the following requirements:

- **Unique Names**: Each asset must have a unique identifier
- **Type Safety**: Only valid `EnergyAsset` instances can be added
- **Immutable Storage**: Assets cannot be modified after addition

```python
from odys.energy_system_models.assets.portfolio import AssetPortfolio
from odys.energy_system_models.assets.generator import PowerGenerator

portfolio = AssetPortfolio()

# Add assets with validation
generator = PowerGenerator(name="gen1", nominal_power=100.0, variable_cost=20.0)
portfolio.add_asset(generator)

# Attempting to add duplicate names raises ValueError
# portfolio.add_asset(generator)  # Would raise ValueError
```

### Asset Retrieval

The portfolio provides multiple ways to access assets:

```python
# Get specific asset by name
specific_generator = portfolio.get_asset("gen1")

# Get all assets of a specific type
all_generators = portfolio.generators
all_batteries = portfolio.batteries

# Get all assets as a read-only mapping
all_assets = portfolio.assets  # Returns MappingProxyType
```

## Organization by Asset Type

### Generators Access
```python
generators = portfolio.generators  # Returns tuple[PowerGenerator, ...]

# Iterate over all generators
for generator in portfolio.generators:
    print(f"{generator.name}: {generator.nominal_power} MW")
```

### Batteries Access
```python
batteries = portfolio.batteries  # Returns tuple[Battery, ...]

# Calculate total storage capacity
total_capacity = sum(battery.capacity for battery in portfolio.batteries)
```

## Design Patterns

### Read-Only Interface
The portfolio provides read-only access to prevent accidental modification:

```python
assets_view = portfolio.assets  # MappingProxyType - immutable view
generators_tuple = portfolio.generators  # Tuple - immutable sequence
```

### Type-Safe Filtering
The internal `_get_assets_by_type()` method ensures type safety when filtering assets:

```python
# This ensures only PowerGenerator instances are returned
generators = portfolio._get_assets_by_type(PowerGenerator)
```

## Error Handling

The portfolio provides clear error messages for common issues:

### Duplicate Asset Names
```python
portfolio.add_asset(PowerGenerator(name="gen1", nominal_power=100.0, variable_cost=20.0))
# portfolio.add_asset(PowerGenerator(name="gen1", nominal_power=200.0, variable_cost=25.0))
# Raises: ValueError: Asset with name 'gen1' already exists.
```

### Invalid Asset Types
```python
# portfolio.add_asset("not_an_asset")
# Raises: TypeError: Expected an instance of EnergyAsset, got <class 'str'>.
```

### Missing Assets
```python
# portfolio.get_asset("nonexistent")
# Raises: KeyError: Asset with name 'nonexistent' does not exist.
```

## Advanced Usage

### Portfolio Composition
```python
def create_sample_portfolio() -> AssetPortfolio:
    """Create a diversified energy portfolio."""
    portfolio = AssetPortfolio()

    # Add multiple generators
    portfolio.add_asset(PowerGenerator(
        name="coal_plant",
        nominal_power=400.0,
        variable_cost=25.0
    ))

    portfolio.add_asset(PowerGenerator(
        name="gas_turbine",
        nominal_power=200.0,
        variable_cost=35.0,
        ramp_up=100.0
    ))

    # Add storage
    portfolio.add_asset(Battery(
        name="grid_battery",
        capacity=500.0,
        max_power=100.0,
        efficiency_charging=0.95,
        efficiency_discharging=0.95,
        soc_start=250.0
    ))

    return portfolio
```

### Portfolio Analysis
```python
def analyze_portfolio(portfolio: AssetPortfolio) -> dict:
    """Analyze portfolio characteristics."""
    return {
        "total_generation_capacity": sum(g.nominal_power for g in portfolio.generators),
        "total_storage_capacity": sum(b.capacity for b in portfolio.batteries),
        "total_storage_power": sum(b.max_power for b in portfolio.batteries),
        "asset_count": len(portfolio.assets),
        "generator_count": len(portfolio.generators),
        "battery_count": len(portfolio.batteries)
    }
```

## Integration with Energy Systems

The portfolio integrates seamlessly with the `EnergySystem` class:

```python
from odys.energy_system import EnergySystem
from datetime import timedelta

# Create and populate portfolio
portfolio = create_sample_portfolio()

# Use in energy system
energy_system = EnergySystem(
    portfolio=portfolio,
    demand_profile=[300, 350, 400, 380, 320],
    timestep=timedelta(hours=1),
    power_unit="MW"
)
```

This design ensures that energy systems have access to well-organized, validated asset collections while maintaining data integrity and type safety.
