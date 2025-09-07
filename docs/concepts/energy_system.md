# Energy System

The `EnergySystem` class is the main orchestrator for energy system modeling and optimization. It combines asset portfolios, demand profiles, and operational constraints to create optimizable energy system models.

## Core Components

### System Configuration

An energy system requires the following components:

- **Asset Portfolio**: Collection of generators, batteries, and other energy assets
- **Demand Profile**: Time series of power demand that must be met
- **Time Step**: Duration of each optimization period
- **Power Unit**: Units for power quantities (W, kW, or MW)
- **Available Capacity Profiles**: Optional time-varying capacity limits for generators

### Example Setup

```python
from datetime import timedelta
from optimes.energy_system import EnergySystem
from optimes.energy_system_models.assets.portfolio import AssetPortfolio

energy_system = EnergySystem(
    portfolio=portfolio,
    demand_profile=[100, 120, 150, 130, 110],  # MW for each time period
    timestep=timedelta(hours=1),
    power_unit="MW",
    available_capacity_profiles={
        "wind_farm": [80, 90, 60, 40, 70]  # Variable wind availability
    }
)
```

## Optimization Process

The energy system optimization follows these steps:

1. **Validation**: The system validates all inputs and creates a `ValidatedEnergySystem`
2. **Model Building**: An algebraic optimization model is constructed using the validated parameters
3. **Solving**: The model is solved using the HiGHS optimization solver
4. **Results**: Optimization results are returned with detailed dispatch schedules and costs

### Running Optimization

```python
# Optimize the system
results = energy_system.optimize()

# Access results
total_cost = results.objective_value
dispatch_schedule = results.to_dataframe()
```

## Mathematical Model

The energy system is formulated as a linear programming problem that:

- **Minimizes**: Total system cost (generation + storage + startup costs)
- **Subject to**:
  - Power balance constraints (supply = demand at each time period)
  - Generator capacity and operational limits
  - Battery energy balance and power constraints
  - Ramp rate limitations
  - Minimum up/down time requirements

## Key Features

### Flexible Time Modeling
- Support for arbitrary time steps (minutes, hours, etc.)
- Multi-period optimization with intertemporal constraints
- Time-varying resource availability

### Comprehensive Asset Integration
- Mixed generator types with different characteristics
- Energy storage with round-trip efficiency modeling
- Realistic operational constraints (ramp rates, minimum runtime)

### Validation and Error Handling
- Input validation ensures model feasibility
- Clear error messages for configuration issues
- Type safety through Pydantic models

### Scalability
- Handles systems from small microgrids to large utility-scale portfolios
- Efficient mathematical formulation for fast solving
- Memory-efficient data structures

## Use Cases

The energy system framework supports various applications:

- **Capacity Planning**: Optimal sizing of generators and storage
- **Operational Dispatch**: Hourly/sub-hourly unit commitment and dispatch
- **Economic Analysis**: Cost optimization and scenario comparison
- **Integration Studies**: Renewable energy and storage integration analysis
