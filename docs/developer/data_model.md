---
icon: lucide/boxes
---

# Data model

The classes of each layer and how they relate. Each section links to the API reference of its packages; the [overview](index.md) shows how the layers depend on each other, and [sequence diagrams](sequences.md) shows how they interact during `optimize()`.

## Domain

The user-facing layer: pydantic models validated at construction. It imports nothing else from `odys` and no numerical library. API reference: [`odys.domain`](api/domain/index.md).

```mermaid
classDiagram
    class EnergyEntity {
        <<abstract>>
        +name: str
        +max_supply(conditions)
        +min_demand(conditions)
        +max_energy_supply(conditions)
        +validate_horizon(conditions)
    }
    class Asset {
        <<abstract>>
    }
    class Generator {
        +nominal_power
        +variable_cost
        +min_power
        +ramp_up
        +ramp_down
        +min_up_time
        +min_down_time
        +startup_cost
        +shutdown_cost
    }
    class Battery {
        <<value object>>
        +capacity
        +max_charge_power
        +max_discharge_power
        +efficiency_charging
        +efficiency_discharging
        +soc_min
        +soc_max
        +degradation_cost
        +self_discharge_rate
    }
    class StationaryStorage {
        +battery: Battery
    }
    class ElectricVehicle {
        +battery: Battery
        +trips: tuple~Trip~
    }
    class Trip {
        <<value object>>
        +start_time
        +end_time
        +energy_consumption
        +min_soc_at_departure
    }
    class Charger {
        +max_power
    }
    class FixedLoad
    class FlexibleLoad {
        +max_increase
        +max_decrease
        +value_of_consumption
    }
    class EnergyMarket {
        +max_trading_volume_per_step
        +allowed_trade_direction: AllowedTradeDirection
        +stage_fixed: bool
    }
    class AllowedTradeDirection {
        <<StrEnum>>
    }
    class AssetPortfolio {
        +assets: tuple~Asset~
        +get_asset(name) Asset
        +assets_of(asset_type) tuple
    }
    class Horizon {
        <<value object>>
        +timestep: timedelta
        +number_of_steps: int
        +hours_per_step: float
        +is_whole_steps(duration) bool
        +steps_in(duration) int
    }
    class OperatingConditions {
        <<value object>>
        +horizon: Horizon
        +profile_values
    }
    class Profile {
        <<abstract>>
        +entity_types: ClassVar
        +required: ClassVar
        +values: tuple~float~
        +entity: EnergyEntity
    }
    class LoadProfile {
        +load: FixedLoad or FlexibleLoad
    }
    class AvailableCapacityProfile {
        +generator: Generator
    }
    class PriceProfile {
        +market: EnergyMarket
    }
    class Scenario {
        +name: str
        +probability: float
        +profiles: tuple~Profile~
        +profiles_of(kind)
        +profile_for(kind, entity)
    }
    class ScenarioSet {
        +scenarios: tuple~Scenario~
        +names
    }
    class Condition {
        <<abstract>>
        +entity_types: ClassVar
        +entity: Asset
    }
    class InitialCondition {
        <<abstract>>
        +required_for(entity) str or None
    }
    class FinalCondition {
        <<abstract>>
    }
    class GeneratorInitialState {
        +generator: Generator
        +power: float
        +time_in_state: timedelta or None
        +is_on: bool
    }
    class GeneratorFinalState {
        +generator: Generator
        +power: float
    }
    class StorageInitialState {
        +storage: StationaryStorage
        +soc: float
    }
    class StorageFinalState {
        +storage: StationaryStorage
        +soc: float
    }
    class ElectricVehicleInitialState {
        +vehicle: ElectricVehicle
        +soc: float
    }
    class ElectricVehicleFinalState {
        +vehicle: ElectricVehicle
        +soc: float
    }
    class ConditionSet {
        +initial: tuple~InitialCondition~
        +final: tuple~FinalCondition~
        +conditions
        +get(kind, entity)
    }
    class ObjectiveTerm {
        <<abstract>>
        +weight: float
    }
    class ProfitTerm
    class CVaRTerm {
        +confidence_level: float
    }
    class Objective {
        +terms: tuple~ObjectiveTerm~
        +term_of(term_type)
    }

    EnergyEntity <|-- Asset
    EnergyEntity <|-- EnergyMarket
    Asset <|-- Generator
    Asset <|-- StationaryStorage
    Asset <|-- ElectricVehicle
    Asset <|-- Charger
    Asset <|-- FixedLoad
    Asset <|-- FlexibleLoad
    StationaryStorage *-- Battery
    ElectricVehicle *-- Battery
    ElectricVehicle *-- "0..*" Trip
    EnergyMarket --> AllowedTradeDirection
    AssetPortfolio o-- "0..*" Asset
    Profile <|-- LoadProfile
    Profile <|-- AvailableCapacityProfile
    Profile <|-- PriceProfile
    LoadProfile --> FixedLoad
    LoadProfile --> FlexibleLoad
    AvailableCapacityProfile --> Generator
    PriceProfile --> EnergyMarket
    Scenario *-- "0..*" Profile
    ScenarioSet *-- "1..*" Scenario
    OperatingConditions --> Horizon
    Condition <|-- InitialCondition
    Condition <|-- FinalCondition
    InitialCondition <|-- GeneratorInitialState
    InitialCondition <|-- StorageInitialState
    InitialCondition <|-- ElectricVehicleInitialState
    FinalCondition <|-- GeneratorFinalState
    FinalCondition <|-- StorageFinalState
    FinalCondition <|-- ElectricVehicleFinalState
    GeneratorInitialState --> Generator
    GeneratorFinalState --> Generator
    StorageInitialState --> StationaryStorage
    StorageFinalState --> StationaryStorage
    ElectricVehicleInitialState --> ElectricVehicle
    ElectricVehicleFinalState --> ElectricVehicle
    ConditionSet *-- "0..*" Condition
    ObjectiveTerm <|-- ProfitTerm
    ObjectiveTerm <|-- CVaRTerm
    Objective *-- "1..*" ObjectiveTerm
```

## Parameters and optimization

`OptimizationProblem.assemble` builds one `ModelContext` and every formulation whose entity type is present (`FORMULATIONS` order), then every objective term the objective holds (`OBJECTIVE_TERM_FORMULATIONS`). Each formulation vectorizes its entities into its `EntityArrays` subclass with `vectorize`, reads scenario profiles (`context.profiles`) and the run's initial and final conditions (`context.conditions`) through the context, owns its variables, constraints, power injection, profit and results view, and names its own entity axis. `build_model` adds variables, every `ConstraintGroup`'s constraints and `PowerBalance`, and maximizes the sum of the objective-term expressions. API reference: [`odys.parameters`](api/parameters/index.md), [`odys.optimization`](api/optimization/index.md).

```mermaid
classDiagram
    class ModelContext {
        +horizon: Horizon
        +scenario_set: ScenarioSet
        +condition_set: ConditionSet
        +time: Coordinates
        +scenarios: Coordinates
        +timestep_hours: float
        +probabilities
        +variable_coords(coordinates)
        +profiles(kind, entities, coordinates)
        +conditions(kind, entities, coordinates, value)
    }
    class Coordinates {
        +dimension: str
        +labels: tuple~str~
        +of_entities(dimension, entities)
    }
    class ModelDimension {
        <<StrEnum>>
        +Scenarios
        +Time
    }
    class EntityArrays {
        <<abstract>>
    }
    class ConstraintGroup {
        +collect_constraints()
        +add_to_model(model)
    }
    class VariableOwner~V~ {
        <<abstract>>
        +variables: V
        +add_variables(model)
    }
    class FormulationInputs {
        +entities
        +context: ModelContext
        +built
        +of_type(entity_type)
        +formulation_of(formulation_type)
    }
    class Formulation {
        <<abstract>>
        +dimension: ClassVar~str~
        +entity_type: ClassVar
        +build(inputs)
        +add_variables(model)
        +power_injection()
        +profit()
        +dispatch(solution) Dispatch
    }
    class VariableFormulation~V~ {
        <<abstract>>
    }
    class GeneratorFormulation
    class EnergyMarketFormulation
    class FixedLoadFormulation
    class FlexibleLoadFormulation
    class StationaryStorageFormulation
    class ElectricVehicleFormulation
    class ChargingFormulation
    class StorageFormulation {
        +create_variables(model)
        +power_injection(variables)
        +dispatch_data(solution)
    }
    class PowerBalance
    class ObjectiveTermInputs {
        +objective: Objective
        +context: ModelContext
        +formulations
    }
    class ObjectiveTermFormulation {
        <<abstract>>
        +build(inputs)
        +add_variables(model)
        +expression()
    }
    class ProfitTermFormulation
    class CVaRTermFormulation
    class OptimizationProblem {
        +context: ModelContext
        +formulations: tuple~Formulation~
        +objective_terms: tuple~ObjectiveTermFormulation~
        +assemble(entities, horizon, scenario_set, condition_set, objective)
        +formulation_of(formulation_type)
        +dispatches(solution)
    }

    ModelContext --> Coordinates
    Coordinates ..> ModelDimension
    ConstraintGroup <|-- Formulation
    ConstraintGroup <|-- ObjectiveTermFormulation
    ConstraintGroup <|-- PowerBalance
    Formulation <|-- VariableFormulation
    VariableOwner <|-- VariableFormulation
    Formulation <|-- FixedLoadFormulation
    VariableFormulation <|-- GeneratorFormulation
    VariableFormulation <|-- EnergyMarketFormulation
    VariableFormulation <|-- FlexibleLoadFormulation
    VariableFormulation <|-- StationaryStorageFormulation
    VariableFormulation <|-- ElectricVehicleFormulation
    VariableFormulation <|-- ChargingFormulation
    StationaryStorageFormulation *-- StorageFormulation
    ElectricVehicleFormulation *-- StorageFormulation
    ChargingFormulation --> ElectricVehicleFormulation
    Formulation --> ModelContext
    Formulation ..> EntityArrays : vectorize
    Formulation ..> FormulationInputs : build
    PowerBalance o-- "1..*" Formulation
    ObjectiveTermFormulation <|-- ProfitTermFormulation
    ObjectiveTermFormulation <|-- CVaRTermFormulation
    VariableOwner <|-- CVaRTermFormulation
    ObjectiveTermFormulation ..> ObjectiveTermInputs : build
    OptimizationProblem *-- ModelContext
    OptimizationProblem *-- "1..*" Formulation
    OptimizationProblem *-- "1..*" ObjectiveTermFormulation
```

## Solving and results

`solve` takes a `linopy.Model` and returns a `SolveOutcome` with an odys-owned status. Whether a solution exists is `has_solution`, not the status: linopy reports `ok` for a time limit reached before the first feasible solution. `OptimalDispatchResults` builds the dispatches from the outcome only when there is a solution, squeezes a single scenario once, and serves one typed property per entity type. API reference: [`odys.solvers`](api/solvers/index.md), [`odys.results`](api/results/index.md), [`odys.energy_system`](api/energy_system.md).

```mermaid
classDiagram
    class EnergySystem {
        +portfolio: AssetPortfolio
        +markets
        +scenarios
        +initial_conditions
        +final_conditions
        +objective: Objective
        +condition_set: ConditionSet
        +build_problem() OptimizationProblem
        +optimize(solver_config) OptimalDispatchResults
    }
    class SolverName {
        <<StrEnum>>
        +HIGHS
        +GUROBI
        +CPLEX
        +SCIP
    }
    class SolverConfig {
        +solver_name: SolverName
        +time_limit
        +mip_rel_gap
        +solver_options
    }
    class SolveStatus {
        <<StrEnum>>
        +OK
        +WARNING
        +ERROR
        +ABORTED
        +UNKNOWN
    }
    class SolveOutcome {
        +status: SolveStatus
        +termination_condition: str
        +objective_value: float or None
        +solution: Dataset
        +has_solution: bool
    }
    class Dispatch {
        <<abstract>>
        +label: ClassVar~str~
        +dimension: str
        +to_dataset()
        +to_dataframe()
    }
    class GeneratorDispatch {
        +power
        +status
        +startup
        +shutdown
    }
    class BatteryDispatch {
        +net_power
        +soc
        +charge_mode
    }
    class StationaryStorageDispatch
    class ElectricVehicleDispatch
    class ChargerDispatch {
        +assignment
        +power
    }
    class MarketDispatch {
        +sell_volume
        +buy_volume
        +net_volume
    }
    class FlexibleLoadDispatch {
        +load_adjustment
        +actual_load
    }
    class OptimalDispatchResults {
        +solver_status: SolveStatus
        +termination_condition: str
        +objective_value: float
        +generators: GeneratorDispatch
        +stationary_storages: StationaryStorageDispatch
        +electric_vehicles: ElectricVehicleDispatch
        +chargers: ChargerDispatch
        +markets: MarketDispatch
        +flexible_loads: FlexibleLoadDispatch
        +to_dataset()
    }

    EnergySystem ..> OptimizationProblem : build_problem
    EnergySystem ..> SolverConfig : optimize
    EnergySystem ..> OptimalDispatchResults : optimize
    SolverConfig --> SolverName
    SolveOutcome --> SolveStatus
    OptimalDispatchResults ..> SolveOutcome : reads
    OptimalDispatchResults o-- "0..*" Dispatch
    Dispatch <|-- GeneratorDispatch
    Dispatch <|-- BatteryDispatch
    BatteryDispatch <|-- StationaryStorageDispatch
    BatteryDispatch <|-- ElectricVehicleDispatch
    Dispatch <|-- ChargerDispatch
    Dispatch <|-- MarketDispatch
    Dispatch <|-- FlexibleLoadDispatch
```
