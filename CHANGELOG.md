# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- `Asset`, the public base class of all user-owned entities (generators, storage, electric vehicles, chargers, loads).
- `AssetPortfolio.assets_of(asset_type)` returns all assets of a given type.
- `OptimalDispatchResults` is exported from `odys`.
- `Battery`, a value object with the battery physics (capacity, power limits, efficiencies, state of charge, degradation, self-discharge).
- Typed scenario profiles that reference their entity: `LoadProfile(load=..., values=...)` (fixed load demand or flexible load base profile), `AvailableCapacityProfile(generator=..., values=...)` and `PriceProfile(market=..., values=...)`.
- `EnergySystem` rejects a profile whose entity differs from the system's entity of the same name (for example a copy of a generator with other parameters).
- `EnergySystem` rejects a non-positive `timestep` and fewer than one step (a pydantic `ValidationError` naming the field).
- A `PriceProfile` must have one value per timestep, like every other profile.
- `SolveStatus`, the solver status of a run (`ok`, `warning`, `error`, `aborted`, `unknown`), exported from `odys`.

### Changed

- Requires linopy 0.10 or later (was 0.7). Constraints that look at the previous or next timestep now state explicitly that the step outside the horizon counts as zero, so the model is the same under linopy's legacy and upcoming v1 semantics.
- **Breaking:** `AssetPortfolio` accepts only `Asset` instances and raises `OdysValidationError` for anything else, such as an `EnergyMarket` (before, a market in the portfolio was silently ignored).
- `EnergySystem` raises `OdysValidationError` for an asset type the optimizer cannot model (a bare `Asset` or a custom `Asset` subclass) instead of silently leaving it out of the model.
- **Breaking:** the per-type `AssetPortfolio` properties (`generators`, `standalone_storages`, `fixed_loads`, `flexible_loads`, `loads`, `electric_vehicles`, `chargers`) are removed; use `assets_of(Generator)` and so on.
- **Breaking (rename):** `StandaloneStorage` → `StationaryStorage`. Also `results.standalone_storages` → `results.stationary_storages`, `StandaloneStorageDispatch` → `StationaryStorageDispatch`, and the result dimension and variable names `standalone_storage*` → `stationary_storage*`.
- **Breaking:** `StationaryStorage` and `ElectricVehicle` take their battery fields in a `Battery`: `StationaryStorage(name=..., battery=Battery(capacity=..., ...))` and `ElectricVehicle(name=..., battery=Battery(...), trips=...)`. Read them as `storage.battery.capacity`. The `Storage` base class and the `asset_type()` method are removed.
- **Breaking:** scenarios hold typed profiles instead of one name-keyed mapping per asset kind, and `StochasticScenario` is merged into `Scenario` (`name` defaults to `"base"`, `probability` to `1.0`):

    ```python
    # Before
    Scenario(fixed_load_profiles={"load": [...]}, market_prices={"market": [...]})
    StochasticScenario(name="high", probability=0.5, available_capacity_profiles={"gen": [...]})

    # After
    Scenario(profiles=(LoadProfile(load=load, values=[...]), PriceProfile(market=market, values=[...])))
    Scenario(name="high", probability=0.5, profiles=(AvailableCapacityProfile(generator=gen, values=[...]),))
    ```

    A profile for the wrong kind of entity (such as available capacity for a battery) is now rejected when the profile is built.
- **Breaking (results):** a single deterministic scenario keeps its own name, so the `scenario` level of results is `"base"` by default (was `"deterministic_scenario"`).
- Validation errors are raised when the offending object is built, not when `EnergySystem` is created:
    - `ElectricVehicle` rejects overlapping trips, a trip departing at t=0 that needs more state of charge than `soc_start`, and a trip departing at t=0 that consumes more energy than the battery holds above `soc_min` at the start (it cannot charge before or during that trip). **Breaking:** the public methods `validate_no_overlapping_trips`, `validate_min_soc_at_departure_feasible` and `validate_trips_within_horizon` are removed; the horizon check is now `validate_horizon(horizon)`.
    - `AssetPortfolio` rejects electric vehicles without chargers and chargers without electric vehicles.
    - `AvailableCapacityProfile` rejects values outside 0 to the generator's nominal power, and a flexible-load `LoadProfile` rejects base values below the load's `max_decrease`.
- System validation is generic: it reaches entities through internal capability queries (maximum supply, minimum demand, maximum energy, horizon check) instead of listing asset kinds.
- Validation messages for missing, extra and wrong-length profiles are reworded around the profile type, for example "Scenario 's1' is missing a LoadProfile for: ['load2']".
- The supply check counts electric vehicle discharge (V2G) as supply, so EV fleets that can discharge pass where they were rejected before.
- The energy check counts a battery's energy as at most what it can discharge over the horizon at its maximum discharge power (was its full capacity), and now includes electric vehicle batteries.
- **Breaking:** `Objective` holds a tuple of terms instead of `profit` and `cvar` fields, and is frozen. It rejects a second term of the same type and requires a `ProfitTerm`. `Objective()` maximizes expected profit, and `Objective.term_of(CVaRTerm)` reads a term back. `EnergySystem.objective` defaults to `Objective()` and no longer accepts `None`:

    ```python
    # Before
    Objective(profit=ProfitTerm(weight=1.0), cvar=CVaRTerm(weight=0.5, confidence_level=0.95))

    # After
    Objective(terms=(ProfitTerm(weight=1.0), CVaRTerm(weight=0.5, confidence_level=0.95)))
    ```
- **Breaking (rename):** `TradeDirection` → `AllowedTradeDirection`, and `EnergyMarket.trade_direction` → `EnergyMarket.allowed_trade_direction`.
- **Breaking (rename):** `OptimalDisptachResults` → `OptimalDispatchResults` (spelling).
- Dispatch series are named by their property: `results.generators.power.name` is `"power"` (was the internal variable name `"generator_power"`), and derived series (`net_volume`, `actual_load`, charger `power`) are named too (were unnamed). This shows in `pd.concat` columns, `.to_frame()` and plot legends; values and indexes are unchanged.
- `results.solver_status` returns a `SolveStatus` instead of a `str`. It is a string enum, so `result.solver_status == "ok"` still works. `termination_condition` stays a `str`.
- **Breaking:** `MarketDispatch.net_volume` returns a `pd.Series`, like every other dispatch property (was `xr.DataArray`).
- **Breaking (results):** generator variable cost, market revenue/cost, and flexible-load value of consumption are now multiplied by the timestep length in hours, consistent with storage and EV degradation cost. Objective values (and CVaR values) change for any timestep other than one hour.

### Removed

- **Breaking:** `odys.utils` (`get_logger`, `setup_rich_logging`). It was never part of `__all__`; use the standard `logging` module.
- Internal `AssetRegistry`, which nothing used.
- Internal: the per-type dispatch plumbing in `odys.results`. Every dispatch view is now a `Dispatch` (one dataset of its series, with the container protocol written once; stationary storage and EVs share `BatteryDispatch`), each model formulation builds its own view with `dispatch(solution)`, and `OptimalDispatchResults` takes the solve outcome and `OptimizationProblem.dispatches`. `odys.results` no longer imports `odys.optimization` or linopy. Result properties, series values, `to_dataset()`/`to_dataframe()` contents and error messages are unchanged (series names: see Changed).
- Internal: `odys.solvers.solver.optimize_algebraic_model`. The solver's `solve(model, config)` now returns a `SolveOutcome` (status, termination condition, objective value, solution) and no longer builds results or knows the problem; `EnergySystem.optimize()` builds `OptimalDispatchResults` from the outcome. `odys.solvers` imports no model layer (import-linter contract).
- Internal: the per-asset `ModelDimension` members, `ModelContext.entity_coordinates` and `coordinates_of`, and the supported-asset list in `domain/validation.py`. Each formulation now names its own dimension and entity type and builds its coordinates; `ModelDimension` keeps only scenario and time, and an asset no formulation models is rejected (as before, when the `EnergySystem` is built) by `odys.optimization.formulations.validate_entities_supported`. Dimension names, variable names and every result are unchanged.
- Internal: `EnergyMILPModel`, `VariableStore`, `VariableDefinitionRegistry`, the linopy variable converter, `odys.optimization.model.objectives`, `CVaRConstraints`, `EnergySystemParameters` and `EnergyAlgebraicModelBuilder`. Each objective term is now a model formulation (`odys.optimization.objective_terms`: `ProfitTermFormulation`, `CVaRTermFormulation`) with its own variables and constraints, `OptimizationProblem.assemble` builds the entity and objective-term formulations, and `build_model` returns a plain `linopy.Model`. Variable and constraint names, objective values and every result are unchanged.
- Internal: `StationaryStorageConstraints`, `ElectricVehicleConstraints`, `ChargerConstraints`, the `storage_constraints` helpers and the storage, EV and charger variable registry entries. Every asset type is now a model formulation; stationary storage and EVs share the battery model `StorageFormulation`. Variable and constraint names, and every result, are unchanged.
- Internal: `GeneratorConstraints`, `MarketConstraints`, `ScenarioConstraints`, `ScenarioParameters` and the generator and market variable registry entries. Generators and energy markets are now model formulations; available capacity and non-anticipativity moved into them. Variable and constraint names, and every result, are unchanged.
- Internal: `FlexibleLoadConstraints`, the `load_adjustment` registry entry and `EnergySystem.build_parameters()`. Fixed and flexible loads are now model formulations (`odys.optimization.formulations`), the power balance is `PowerBalance`, and `EnergySystem.build_problem()` returns the `OptimizationProblem` the model builder takes. The `load_adjustment` variable and every result are unchanged.
- Internal: the six `*Parameters` classes in `odys.parameters.entity_parameters` (all but `ScenarioParameters`), `CoordinatesStore` and `ModelCoordinates`. Model dimensions and coordinates moved from `odys.optimization.model` to `odys.parameters`, and entity parameters are typed arrays built generically from the entity fields, with the same names as the domain fields. None of these were part of `__all__`.
- **Breaking:** `StochasticScenario` (use `Scenario` with `name` and `probability`) and the internal `validate_sequence_of_stochastic_scenarios` (its rules now live in `ScenarioSet`).

### Fixed

- An electric vehicle trip departing at the first timestep now draws its energy from the battery; before, the model added it to the state of charge (an EV at 50% SOC making a 10%-of-capacity trip at t=0 ended the first step at 60% instead of 40%).
- `AssetPortfolio` built from a one-shot iterable (such as a generator expression) now keeps all assets; before, it was silently empty.
- Objective terms priced per MWh now scale with the timestep length (see Changed).
- The supply check compares the sum of all loads with the maximum supply at each timestep; before, each load was checked on its own, so several loads that together exceeded supply passed validation and failed at solve time.
- Scenario probabilities are now checked with a floating-point tolerance, so equiprobable scenarios such as 49 × `1/49` are accepted.
- Stochastic scenarios passed as a tuple (or any non-list sequence) are now validated; before, the probability-sum and unique-name checks were skipped.
- `SolverConfig.solver_options` is now passed to the solver and overrides translated common options, as documented. Before, it was ignored.
- A solve that ends without a solution (for example an infeasible model, or a time limit reached before the first feasible solution) now returns results whose `solver_status` and `termination_condition` report it, and whose solution accessors raise `OdysSolverError`; before, `optimize()` crashed with an `AttributeError` from linopy.
- Unit descriptions: `EnergyMarket.max_trading_volume_per_step` is a power in MW, and generator startup/shutdown costs are per event.
- Documentation: result properties are documented as `pandas.Series` (were "DataFrame"), the available-capacity snippet in the generator guide no longer exceeds its generator's nominal power, the portfolio guide no longer lists a `Battery` as an asset, the README output shows the new series name, and the `odys.parameters` API pages moved out of `odys.optimization` to their own section.

### Known issues

- `Charger.efficiency` is accepted but not yet used by any constraint.

## [0.2.1] - 2026-08-04

### Added

- EV fleet optimization: `ElectricVehicle`, `Charger`, and `Trip` entities for modeling electric vehicle charging with trip constraints
- `StandaloneStorage` as the user-facing storage class for stationary battery assets
- Flexible loads: adjustable demand that optimizer can increase/decrease within bounds
- `FlexibleLoadDispatch` results class with `load_adjustment` and `actual_load` properties
- `results.flexible_loads` API for accessing flexible load dispatch results
- `Storage.degradation_cost` is now included in the objective function, applied to total energy throughput (charge + discharge) converted to MWh via the scenario timestep

### Changed

- **Breaking:** `Storage` is now an abstract base class; use `StandaloneStorage` for stationary battery assets
- **Breaking:** `Storage.max_power` split into `max_charge_power` and `max_discharge_power` to support asymmetric charge/discharge limits
- **Breaking:** `AssetPortfolio.storages` renamed to `AssetPortfolio.standalone_storages`
- Relaxed power demand validation for flexible loads to account for max_decrease capability
- Updated error message in `per_scenario_profit` to include flexible loads as a valid profit source
- `Storage.degradation_cost` now defaults to `0.0` instead of `None`, matching `Generator.startup_cost`. **Breaking:** explicitly passing `degradation_cost=None` is no longer accepted; omit the field or pass a float.

## [0.2.0] - 2026-07-05

### Added

- CVaR (Conditional Value at Risk) support for stochastic optimization
- Lower bound validation (`ge=0`) on `ObjectiveTerm.weight`

### Changed

- Restructured codebase into layered architecture
- Refactored results API
- Refactored objective definition
- Added `slots` and pydantic `frozen` configuration to data models
- Improved docstrings across market, load, scenario, and objective classes
- Migrated documentation from MkDocs to Zensical
- Fixed storage timedelta constraints

### Removed

- Removed load results from results API

## [0.1.2] - 2025-01-01

### Added

- Multi-stage optimization
- Energy market integration with buy/sell/both trade directions

### Changed

- Improved validation error messages

## [0.1.1] - 2024-12-01

### Added

- Stochastic optimization with multiple scenarios
- Storage (battery) assets with charge/discharge constraints
- Available capacity profiles for generators

## [0.1.0] - 2024-11-01

### Added

- Initial release
- Energy system modeling with generators, loads, and storage
- MILP optimization using HiGHS solver
- Pydantic-based input validation
- Basic examples and documentation
