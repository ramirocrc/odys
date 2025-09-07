# Optimization

The optimization engine in optimes transforms energy system models into mathematical optimization problems and solves them using state-of-the-art solvers.

## Mathematical Framework

### Problem Formulation

The energy system optimization is formulated as a linear programming (LP) problem:

```
Minimize: Total Cost = Generation Cost + Storage Cost + Startup Cost + Emissions Cost

Subject to:
- Power balance constraints
- Generator capacity limits
- Battery energy balance
- Operational constraints (ramp rates, minimum up/down times)
- State of charge limits
```

### Variables

The optimization model includes the following decision variables:

- **Generator Power**: `var_generator_power[generator, time]` - Power output for each generator at each time period
- **Battery Charge**: `var_battery_charge[battery, time]` - Charging power for each battery
- **Battery Discharge**: `var_battery_discharge[battery, time]` - Discharging power for each battery
- **Battery SOC**: `var_battery_soc[battery, time]` - State of charge for each battery
- **Generator Status**: Binary variables for unit commitment (on/off status)

## Optimization Process

### 1. Model Building

The `EnergyAlgebraicModelBuilder` constructs the mathematical model:

```python
from optimes._math_model.model_builder import EnergyAlgebraicModelBuilder

model_builder = EnergyAlgebraicModelBuilder(
    energy_system_parameters=validated_system.parameters
)
linopy_model = model_builder.build()
```

### 2. Solver Integration

The model uses the HiGHS solver for high-performance linear programming:

```python
from optimes.solvers.highs_solver import optimize_algebraic_model

results = optimize_algebraic_model(linopy_model)
```

### 3. Result Processing

Results are returned as `OptimizationResults` objects containing:

- **Objective Value**: Total optimized cost
- **Variable Solutions**: Optimal values for all decision variables
- **Constraint Information**: Shadow prices and binding constraints
- **Solver Metadata**: Solution status, solve time, iterations

## Key Constraints

### Power Balance
Ensures supply equals demand at every time period:
```
Sum(generator_power) + Sum(battery_discharge) - Sum(battery_charge) = demand
```

### Generator Limits
Respects capacity and operational constraints:
```
0 d generator_power d nominal_power * availability
ramp_down d power_change d ramp_up
```

### Battery Energy Balance
Maintains energy conservation in storage:
```
soc[t+1] = soc[t] + charge[t] * efficiency_charging - discharge[t] / efficiency_discharging
soc_min d soc[t] d soc_max
```

## Solver Features

### HiGHS Integration
- **High Performance**: State-of-the-art linear programming solver
- **Reliability**: Robust solution for large-scale problems
- **Open Source**: No licensing restrictions
- **Active Development**: Regular updates and improvements

### Solution Quality
- **Optimal Solutions**: Guaranteed global optimum for linear problems
- **Numerical Stability**: Robust handling of numerical precision
- **Feasibility Detection**: Clear indication of infeasible problems
- **Sensitivity Analysis**: Access to dual variables and reduced costs

## Optimization Results

### Accessing Results
```python
# Run optimization
results = energy_system.optimize()

# Access solution details
optimal_cost = results.objective_value
solution_status = results.termination_condition
solve_time = results.solve_time

# Convert to DataFrame for analysis
results_df = results.to_dataframe()
```

### Result Analysis
The results provide comprehensive information for analysis:

- **Dispatch Schedule**: Optimal operation of all assets over time
- **Cost Breakdown**: Detailed cost attribution by component
- **Utilization Rates**: Asset capacity factors and efficiency metrics
- **Constraint Analysis**: Which constraints are binding at optimum

## Advanced Features

### Scenario Analysis
```python
# Compare different demand scenarios
high_demand = [150, 180, 200, 175, 160]
low_demand = [80, 100, 120, 110, 90]

results_high = energy_system_high.optimize()
results_low = energy_system_low.optimize()
```

### Sensitivity Analysis
```python
# Analyze impact of fuel price changes
base_cost = generator.variable_cost
for multiplier in [0.8, 1.0, 1.2, 1.5]:
    generator.variable_cost = base_cost * multiplier
    results = energy_system.optimize()
    print(f"Price multiplier {multiplier}: Cost = {results.objective_value}")
```

## Performance Considerations

### Model Size
- **Linear Scaling**: Solve time scales approximately linearly with problem size
- **Memory Efficient**: Optimized data structures minimize memory usage
- **Sparse Formulation**: Takes advantage of constraint matrix sparsity

### Best Practices
- Use appropriate time resolution (hourly vs. sub-hourly)
- Consider model complexity vs. solution accuracy trade-offs
- Validate input data quality before optimization
- Monitor solver convergence and solution quality

The optimization framework provides a robust foundation for energy system analysis, from small microgrids to large utility-scale systems.
