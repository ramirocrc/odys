# Roadmap

Odys aims to make stochastic optimization for energy portfolios as straightforward as possible. This roadmap outlines the direction for the next 12 months, organized by feature category.

## Asset Types

Energy system components that can be included in an optimization portfolio.

**Current:**
- Generator (ramp rates, min up/down time, startup/shutdown costs)
- StandaloneStorage (stationary battery with charge/discharge, efficiency, SOC constraints)
- ElectricVehicle (storage with trip schedules and charging constraints)
- Charger (EV charging infrastructure with power limits)
- FixedLoad (inelastic demand)
- FlexibleLoad (adjustable demand with increase/decrease bounds)
- EnergyMarket (buy/sell with trade direction and volume limits)

**Coming soon:**
- [ ] FlexibleLoad enhancements (min/max load, ramp rate constraints)
- [ ] Charger efficiency enforcement (apply existing efficiency parameter in constraints)
- [ ] ElectricVehicle temperature-dependent battery parameters (capacity, power, degradation)
- [ ] Trip regenerative braking (energy recovery during braking phases)
- [ ] Trip flexibility (earliest departure / latest arrival time windows)
- [ ] Transformer (grid connection point with power capacity limits for EV charging infrastructure)
- [ ] ElectricVehicle ancillary services / reserve products (V2G reserve-capacity bidding, frequency response beyond energy arbitrage)
- [ ] Charging-session operational limits (minimum connection duration, session ramp-rate limits, idle/parasitic charger draw)

## Scenarios & Uncertainty

Scenario definitions and uncertainty modeling for stochastic optimization.

**Current:**
- Scenario (deterministic single-scenario optimization)
- StochasticScenario (multiple scenarios with probabilities)
- Profiles: available_capacity, fixed_load, flexible_load_base, market_prices

**Coming soon:**
- [ ] Trip uncertainty (energy consumption, arrival/departure times across scenarios)
- [ ] Temperature/weather scenario profiles (ambient temperature affecting battery and trip behavior)

## Objective & Risk Management

Optimization objectives and risk metrics for decision-making under uncertainty.

**Current:**
- Objective (composable objective function)
- ProfitTerm (maximize expected profit)
- CVaRTerm (Conditional Value at Risk for risk-averse optimization)

**Coming soon:**
- [ ] ...

## Optimization Model

MILP formulation, constraints, solver infrastructure, and performance.

**Current:**
- MILP formulation via linopy (xarray-based algebraic modeling)
- Multi-stage optimization (stage_fixed decisions across scenarios)
- Asset-specific constraints (power balance, SOC dynamics, ramp rates, etc.)
- Solver support: HiGHS (default), Gurobi, CPLEX, SCIP
- SolverConfig (time_limit, mip_rel_gap, threads, presolve, log_output, solver_options)

**Coming soon:**
- [ ] Piecewise-linear CC-CV charging curve approximation (SoC-dependent power limits)
- [ ] DoD-dependent battery degradation (cyclic aging with depth-of-discharge bins, calendar aging)
- [ ] Grid/transformer capacity constraints (aggregate charger loads through transformer limits)
- [ ] Here-and-now staging (non-anticipativity) for EV charging and charger-assignment decisions (extend stage_fixed beyond markets)
- [ ] Remove redundant ev_net_power decision variable (derive net power in results post-processing; same applies to standalone_storage_net_power)

## Results & Output

Dispatch results, analysis capabilities, and export formats.

**Current:**
- OptimalDispatchResults (frozen snapshot of solved model)
- Per-asset dispatch classes (GeneratorDispatch, StandaloneStorageDispatch, etc.)
- Export: xarray Dataset, pandas DataFrame, pandas Series

**Coming soon:**
- [ ] ...

## Validation

Input validation and feasibility checks to catch errors early.

**Current:**
- Pydantic-based input validation (type checking, bounds, constraints)
- Energy system validation (power balance feasibility, scenario consistency)
- EV trip validation (overlapping trips, horizon bounds, min SOC feasibility)
- Custom exceptions (OdysError, OdysValidationError, OdysSolverError, OdysNoResultsError)

**Coming soon:**
- [ ] Charger-EV compatibility validation (plug type, power level matching)
- [ ] Transformer capacity feasibility check (aggregate load vs. transformer rating)

## Documentation & Examples

User guide, API reference, and worked examples to help users learn and use Odys.

**Current:**
- User guide (13 pages covering all major features)
- API reference (comprehensive documentation of all public classes)
- 6 worked examples (basic dispatch, battery, flexible load, market arbitrage, CVaR, EV fleet)
- Mathematical notation reference

**Coming soon:**
- [ ] ...
