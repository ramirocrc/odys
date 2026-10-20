# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

- Documentation: a simpler landing page, laid out like vuejs.org's. It has a hero with three buttons (Get started, `pip install odys`, GitHub), one figure of price scenarios going in and the battery schedule Odys commits to coming out, a "Built on" strip and six highlights. It follows the light/dark toggle and keeps the docs header and navigation tabs.
- Documentation: the docs follow vuejs.org's colour scheme in both modes: a white or `#1a1a1a` background and header (the light mode header was violet), neutral greys for text, code blocks and the example charts' gridlines and axes, Vue's green as the dark mode accent. Links stay the brand violet.

## [0.3.0] - 2026-10-18


### Added

- `Asset`, the public base class of all user-owned entities (generators, storage, electric vehicles, chargers, loads).
- `AssetPortfolio.assets_of(asset_type)` returns all assets of a given type.
- `OptimalDispatchResults` is exported from `odys`.
- `OdysError`, `OdysValidationError`, `OdysSolverError` and `OdysNoResultsError` are exported from `odys`, so `except odys.OdysValidationError` works; before, they were only importable from the internal `odys.domain.exceptions`.
- `Battery`, a value object with the battery physics (capacity, power limits, efficiencies, state of charge, degradation, self-discharge).
- Typed scenario profiles that reference their entity: `LoadProfile(load=..., values=...)` (fixed load demand or flexible load base profile), `AvailableCapacityProfile(generator=..., values=...)` and `PriceProfile(market=..., values=...)`.
- `EnergySystem` rejects a profile whose entity differs from the system's entity of the same name (for example a copy of a generator with other parameters).
- `EnergySystem` rejects a non-positive `timestep` and fewer than one step (a pydantic `ValidationError` naming the field).
- A `PriceProfile` must have one value per timestep, like every other profile.
- `SolveStatus`, the solver status of a run (`ok`, `warning`, `error`, `aborted`, `unknown`), exported from `odys`.
- `FlexibleLoad.min_load` and `FlexibleLoad.max_load`: optional absolute consumption bounds in MW that override `max_decrease` / `max_increase` when set (#80). A flexible load's `LoadProfile` must stay within them.
- Initial and final conditions of a run, passed as `EnergySystem(initial_conditions=..., final_conditions=...)` and shared by all scenarios: `GeneratorInitialState(generator=..., power=..., time_in_state=...)`, `GeneratorFinalState(generator=..., power=...)`, `StorageInitialState` / `StorageFinalState(storage=..., soc=...)` and `ElectricVehicleInitialState` / `ElectricVehicleFinalState(vehicle=..., soc=...)`. A generator's status follows its power (0 is off).
    - A generator starting on pays no startup cost at t=0, ramp limits apply from its initial power at t=0, and its minimum up or down time carries over from `time_in_state`.
    - `GeneratorFinalState` fixes the output at the last step; 0 turns the generator off. It must fit the generator's available capacity at the last step.
    - Every storage and electric vehicle needs an initial state, and so does every generator with `ramp_up`, `ramp_down`, `min_up_time`, `min_down_time`, `startup_cost` or `shutdown_cost`. `time_in_state` is required when the matching minimum time is set. Missing or inconsistent conditions raise `OdysValidationError`.
- Contributor guidance that works with any coding agent: `AGENTS.md` (conventions, Definition of Done, architecture) and step-by-step playbooks in `.agents/skills/`. `tests/test_escape_hatches.py` fails on any new lint or type-check suppression, and `tests/test_agent_guidelines.py` keeps the paths in the guidance current.
- The Odys logo: a wordmark set in Michroma whose O has an open top-right corner with a dot. It is the docs header logo (the dark wordmark on the light scheme, the light one on the dark scheme and the landing page) and favicon and heads the README; the SVGs for dark and light backgrounds are in `docs/assets/brand/`. `just generate-logo` rebuilds them from the vendored font (`tools/docs/brand/fonts/`) with `tools/docs/generate_logo.py`. The favicon is the O alone on a transparent background, dark on light browser themes and light on dark ones (a script in `overrides/main.html` swaps it when the theme changes), drawn heavier so it stays legible at 16 px.
- `just docs-build` runs every code block of the User Guide (`tools/docs/check_user_guide.py`) and fails when one raises or prints something other than the output the page shows.

### Changed

- **Breaking:** `Trip.start_time` and `Trip.end_time` are `timedelta`s measured from the start of the horizon, like the other times in odys; they were step indices. Each must be a whole number of timesteps, which the `EnergySystem` checks:

    ```python
    # Before (hourly steps)
    Trip(name="delivery", start_time=7, end_time=9, energy_consumption=0.015)

    # After
    Trip(name="delivery", start_time=timedelta(hours=7), end_time=timedelta(hours=9), energy_consumption=0.015)
    ```

- `SolverConfig.presolve` defaults to `None`, which leaves presolve to each solver's own default (on or automatic in every supported solver). Before, the default `False` turned presolve off. `True` and `False` still force it on or off.
- `to_dataframe()` of a results container has one row per label of the dimensions all its series share. For chargers, that is one row per time and charger, with one `assignment[<vehicle>]` column per vehicle; before, each charger's `power` was repeated on the row of every vehicle.
- **Breaking:** `Battery.soc_start` and `Battery.soc_end` are removed; the state of charge at the start and end of a run is an initial or final condition of the `EnergySystem`:

    ```python
    # Before
    bess = BatteryStorage(name="bess", battery=Battery(capacity=50.0, ..., soc_start=0.5, soc_end=0.5))
    EnergySystem(portfolio=..., ...)

    # After
    bess = BatteryStorage(name="bess", battery=Battery(capacity=50.0, ...))
    EnergySystem(
        portfolio=...,
        ...,
        initial_conditions=(StorageInitialState(storage=bess, soc=0.5),),
        final_conditions=(StorageFinalState(storage=bess, soc=0.5),),
    )
    ```

    Electric vehicles use `ElectricVehicleInitialState` and `ElectricVehicleFinalState`. The checks that a trip departing at t=0 fits the starting charge move from `ElectricVehicle` to `ElectricVehicleInitialState`.
- **Breaking:** `Generator.min_up_time` and `Generator.min_down_time` are `timedelta | None` (default `None`, no minimum) instead of a number of timesteps (default 1). They must be a whole number of timesteps. Write `min_up_time=timedelta(hours=4)` for 4 hourly steps.
- **Breaking:** a generator with ramp limits, minimum up or down times, or startup or shutdown costs needs a `GeneratorInitialState`. Before, it was assumed off at 0 MW before the horizon, but its ramp limits did not apply at t=0. Ramp limits now apply at t=0 from the initial power.
- `FlexibleLoad.max_increase` and `max_decrease` are now optional; each side needs a relative or an absolute bound. Leaving out both bounds of a side raises `OdysValidationError` (before, omitting `max_increase` or `max_decrease` raised a pydantic `ValidationError`).
- Requires linopy 0.10 or later (was 0.7). Constraints that look at the previous or next timestep now state explicitly that the step outside the horizon counts as zero, so the model is the same under linopy's legacy and upcoming v1 semantics.
- **Breaking:** `AssetPortfolio` accepts only `Asset` instances and raises `OdysValidationError` for anything else, such as an `EnergyMarket` (before, a market in the portfolio was silently ignored).
- `EnergySystem` raises `OdysValidationError` for an asset type the optimizer cannot model (a bare `Asset` or a custom `Asset` subclass) instead of silently leaving it out of the model.
- **Breaking:** the per-type `AssetPortfolio` properties (`generators`, `standalone_storages`, `fixed_loads`, `flexible_loads`, `loads`, `electric_vehicles`, `chargers`) are removed; use `assets_of(Generator)` and so on.
- **Breaking (rename):** `StandaloneStorage` → `BatteryStorage`, the grid-connected battery (BESS). Also `results.standalone_storages` → `results.battery_storages`, `StandaloneStorageDispatch` → `BatteryStorageDispatch`, and the result dimension and variable names `standalone_storage*` → `battery_storage*`.
- **Breaking:** `BatteryStorage` and `ElectricVehicle` take their battery fields in a `Battery`: `BatteryStorage(name=..., battery=Battery(capacity=..., ...))` and `ElectricVehicle(name=..., battery=Battery(...), trips=...)`. Read them as `storage.battery.capacity`. The `Storage` base class and the `asset_type()` method are removed.
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
    - `ElectricVehicle` rejects overlapping trips. `ElectricVehicleInitialState` rejects a trip departing at t=0 that needs more state of charge than the initial `soc`, and one that consumes more energy than the battery holds above `soc_min` at the start (it cannot charge before or during that trip). **Breaking:** the public methods `validate_no_overlapping_trips`, `validate_min_soc_at_departure_feasible` and `validate_trips_within_horizon` are removed; the horizon check is now `validate_horizon(horizon)`.
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
- Documentation: the User Guide now follows one running example, a site with a CCGT, a wind farm, a battery, a factory, a flexible process and a day-ahead market, that grows page by page. Every code block runs in order on its page, and the printed outputs are those of a real solve. Asset pages share one template and each links its worked example. The overview has a "Units and time" section, the Results page covers selecting one asset, solves without a solution and the meaning of `objective_value`, and the Stochastic page explains which decisions are shared across scenarios (stage-fixed trades) and which adapt to each one. Results comes before Stochastic optimization in the navigation, and Battery follows BatteryStorage.
- Documentation: a new Mathematical Formulation section writes out the model, one page per part (generators, batteries, electric vehicles, flexible loads, markets, power balance, scenarios, non-anticipativity, objective), with numbered constraints, the reason for each one's form, what it doesn't model, and the notation. The User Guide holds no math any more and links to these constraints instead.
- Documentation: the User Guide is organized by workflow: Building a model (Your first model, Scenario, Time and units); Assets; Markets; Solving and results (Results, Solvers, Validation and errors); Uncertainty and risk (Several scenarios, Risk (CVaR)). The Core concepts and Optimization pages are folded into these, and their URLs changed. The navigation shows every page of a section.
- Documentation: the examples are named after the planning problem they solve, with new file names and URLs: Basic Dispatch is Merit-Order Dispatch (`merit_order_dispatch`), Battery Dispatch is Storing Solar for the Evening (`solar_storage`), Flexible Load Market is Industrial Demand Response (`demand_response`), CVaR Market Risk is Day-Ahead or Intraday (`day_ahead_or_intraday`) and EV Fleet Optimization is Depot Charging with V2G (`depot_charging`). The write-docs example template states the naming rule.
- Documentation: the User Guide opens directly on Your first model, which now holds the one-bus rule and a short Units section. The Overview page, with its object diagram and running example table, and its URL are gone. The Profiles page becomes Scenario (`model/scenario.md`), which says what a scenario describes (availability, demand, prices) and that each one is a profile; it follows Your first model, the uncertainty page is renamed Several scenarios, and Time and units moves to the end of Building a model as a reference page.

### Removed

- **Breaking:** `odys.utils` (`get_logger`, `setup_rich_logging`). It was never part of `__all__`; use the standard `logging` module.
- Internal `AssetRegistry`, which nothing used.
- Internal: the per-type dispatch plumbing in `odys.results`. Every dispatch view is now a `Dispatch` (one dataset of its series, with the container protocol written once; battery storage and EVs share `BatteryDispatch`), each model formulation builds its own view with `dispatch(solution)`, and `OptimalDispatchResults` takes the solve outcome and `OptimizationProblem.dispatches`. `odys.results` no longer imports `odys.optimization` or linopy. Result properties, series values, `to_dataset()`/`to_dataframe()` contents and error messages are unchanged (series names: see Changed).
- Internal: `odys.solvers.solver.optimize_algebraic_model`. The solver's `solve(model, config)` now returns a `SolveOutcome` (status, termination condition, objective value, solution) and no longer builds results or knows the problem; `EnergySystem.optimize()` builds `OptimalDispatchResults` from the outcome. `odys.solvers` imports no model layer (import-linter contract).
- Internal: the per-asset `ModelDimension` members, `ModelContext.entity_coordinates` and `coordinates_of`, and the supported-asset list in `domain/validation.py`. Each formulation now names its own dimension and entity type and builds its coordinates; `ModelDimension` keeps only scenario and time, and an asset no formulation models is rejected (as before, when the `EnergySystem` is built) by `odys.optimization.formulations.validate_entities_supported`. Dimension names, variable names and every result are unchanged.
- Internal: `EnergyMILPModel`, `VariableStore`, `VariableDefinitionRegistry`, the linopy variable converter, `odys.optimization.model.objectives`, `CVaRConstraints`, `EnergySystemParameters` and `EnergyAlgebraicModelBuilder`. Each objective term is now a model formulation (`odys.optimization.objective_terms`: `ProfitTermFormulation`, `CVaRTermFormulation`) with its own variables and constraints, `OptimizationProblem.assemble` builds the entity and objective-term formulations, and `build_model` returns a plain `linopy.Model`. Variable and constraint names, objective values and every result are unchanged.
- Internal: `StationaryStorageConstraints`, `ElectricVehicleConstraints`, `ChargerConstraints`, the `storage_constraints` helpers and the storage, EV and charger variable registry entries. Every asset type is now a model formulation; battery storage and EVs share the battery model `StorageFormulation`. Variable and constraint names, and every result, are unchanged.
- Internal: `GeneratorConstraints`, `MarketConstraints`, `ScenarioConstraints`, `ScenarioParameters` and the generator and market variable registry entries. Generators and energy markets are now model formulations; available capacity and non-anticipativity moved into them. Variable and constraint names, and every result, are unchanged.
- Internal: `FlexibleLoadConstraints`, the `load_adjustment` registry entry and `EnergySystem.build_parameters()`. Fixed and flexible loads are now model formulations (`odys.optimization.formulations`), the power balance is `PowerBalance`, and `EnergySystem.build_problem()` returns the `OptimizationProblem` the model builder takes. The `load_adjustment` variable and every result are unchanged.
- Internal: the six `*Parameters` classes in `odys.parameters.entity_parameters` (all but `ScenarioParameters`), `CoordinatesStore` and `ModelCoordinates`. Model dimensions and coordinates moved from `odys.optimization.model` to `odys.parameters`, and entity parameters are typed arrays built generically from the entity fields, with the same names as the domain fields. None of these were part of `__all__`.
- **Breaking:** `StochasticScenario` (use `Scenario` with `name` and `probability`) and the internal `validate_sequence_of_stochastic_scenarios` (its rules now live in `ScenarioSet`).

### Fixed

- A battery's self-discharge now applies at the first step too; before, the state of charge after the first step started from the full initial state of charge, so storage and EVs lost less energy than `self_discharge_rate` says.
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
- Documentation: the battery dispatch figure's hover now shows each asset's own power; before, it showed the top of each stacked bar, so values at a timestep did not add up to the load. The state of charge is labelled as a percentage (was "MWh").
- Documentation: the EV fleet example no longer names the exact hour ev_2 and ev_3 charge, since any 5 $/MWh hour is equally optimal and the solver's choice changed (t21 → t23). Example figures are no longer committed; they are generated on every docs build, which also checks the facts the battery and EV example pages state.
- Documentation: ramp limits are per timestep (the conditions guide called them MW/h), the generator and storage guides say the optimizer maximizes profit (they said it minimizes cost), `result.chargers.power` is documented as charging power only, without V2G discharge, and the value at risk is written ζ instead of η, which is also the battery efficiency.
- Documentation: a review of every page on markets against the `energy-markets` playbook. Intraday is described as traded knowing the scenario's whole future, an optimistic simplification (Several scenarios, EnergyMarket, Non-anticipativity, CVaR example). The CVaR Market Risk example's day-ahead and intraday prices now move together, with intraday the more volatile, and its CCGT costs 120 $/MWh (it was 20): the risk-neutral run sells everything intraday and the CVaR run everything day-ahead (it was an 87.5 / 12.5 mix, from prices moving in opposite directions). The Market Arbitrage example is renamed Make or Buy (`examples/make_or_buy.py`, `docs/examples/make_or_buy.md`), since it chooses between running a CCGT and buying. M-2 explains the one-direction rule by the single price instead of "trading with yourself".
- Documentation: the Several scenarios and Risk pages bid day-ahead before the market clears, so each scenario has its own day-ahead prices, lower when it's windy (they were the same in both, as if already known). The EnergyMarket page and NA-1 say that a stage-fixed trade is a price-independent bid, not a price-quantity curve. A new `energy-markets` playbook in `.agents/skills/` holds the European market timeline and how it maps onto odys.
- Documentation: every example page shows its script's code exactly and states only results checked against a run. The examples changed to show what their pages claim: the battery dispatch battery is 95 % efficient each way (it was lossless, so the optimum was degenerate), the flexible load and market arbitrage prices no longer tie with the value of consumption or the CCGT cost, market arbitrage sells as well as buys, the CVaR example is one hourly step (it was one 24-hour step, so the page's profits were 24 times too small), and all three vans of the EV fleet can sell back, so they compete for the two chargers. The landing page's state-of-charge snippet uses the formulation's notation.

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
