"""Energy system input validation.

This module holds the rules that span entities and scenarios. Rules about a
single entity or profile live on that object and run when it is built. The
rules here treat every entity alike through its capability queries
(`max_supply`, `min_demand`, `max_energy_supply`, `validate_horizon`) and
every profile through its type's `entity_types` and `required` flags and its
`number_of_steps` and `operating_values`. A new
asset type is covered by overriding those queries (that the optimizer models
it is checked against its formulations, in `odys.optimization.formulations`);
a new profile type by adding it to `AnyProfile` and `PROFILE_TYPES` in
`profiles.py`. Conditions are checked through their own queries
(`validate_horizon`, `validate_operating_conditions`) and required per asset
through each initial condition type's `required_for`; a new initial condition
type is added to `INITIAL_CONDITION_TYPES` in `conditions.py`.
"""

from collections.abc import Mapping, Sequence

from odys.domain.conditions import INITIAL_CONDITION_TYPES, ConditionSet
from odys.domain.entities.base import Asset, EnergyEntity
from odys.domain.entities.market import EnergyMarket
from odys.domain.entities.portfolio import AssetPortfolio
from odys.domain.exceptions import OdysValidationError
from odys.domain.horizon import Horizon, OperatingConditions
from odys.domain.profiles import PROFILE_TYPES, FlexibleLoadProfile, LoadProfile, Profile
from odys.domain.scenario import Scenario, ScenarioSet


def validate_energy_system_inputs(
    portfolio: AssetPortfolio,
    scenario_set: ScenarioSet,
    markets: Sequence[EnergyMarket],
    horizon: Horizon,
    condition_set: ConditionSet,
) -> None:
    """Run all cross-domain validation checks on the energy system.

    Args:
        portfolio: The asset portfolio to validate against.
        scenario_set: The scenarios of the problem.
        markets: Normalized sequence of energy markets.
        horizon: The time grid of the optimization.
        condition_set: The initial and final conditions of the run.

    Raises:
        OdysValidationError: If any validation check fails.

    """
    entities: tuple[EnergyEntity, ...] = (*portfolio.assets.values(), *markets)
    for entity in entities:
        entity.validate_horizon(horizon)

    validate_conditions_reference_system_assets(condition_set, portfolio)
    validate_required_initial_conditions_present(condition_set, portfolio)

    scenarios = scenario_set.scenarios
    validate_profiles_reference_system_entities(scenarios, portfolio, markets)
    validate_required_profiles_present(scenarios, entities)
    validate_profile_lengths(scenarios, horizon)
    validate_conditions_fit_the_run(condition_set, scenarios, horizon)

    for scenario in scenarios:
        validate_has_load_or_market(scenario, markets)
        validate_enough_power_to_meet_demand(scenario, entities, horizon)
        if not markets:
            validate_enough_energy_to_meet_demand(scenario, entities, horizon)


def validate_profiles_reference_system_entities(
    scenarios: Sequence[Scenario],
    portfolio: AssetPortfolio,
    markets: Sequence[EnergyMarket],
) -> None:
    """Validate that each profile references an entity of the energy system.

    Assets and markets are looked up separately, since a market may share a
    name with an asset. A profile whose entity is missing from the system, or
    differs from the system's entity of that name (for example a copy with
    other parameters), would describe an entity that is not being optimized.

    Args:
        scenarios: Scenarios whose profiles to check.
        portfolio: The asset portfolio.
        markets: The energy markets.

    Raises:
        OdysValidationError: If a profile's entity is not the system's entity of that name.

    """
    markets_by_name: Mapping[str, EnergyEntity] = {market.name: market for market in markets}
    for scenario in scenarios:
        for profile in scenario.profiles:
            system_entities = portfolio.assets if isinstance(profile.entity, Asset) else markets_by_name
            _validate_profile_references(scenario, profile, system_entities.get(profile.entity.name))


def _validate_profile_references(scenario: Scenario, profile: Profile, system_entity: EnergyEntity | None) -> None:
    if system_entity is None:
        msg = (
            f"Scenario '{scenario.name}' has a {type(profile).__name__} for "
            f"'{profile.entity.name}', which is not in the energy system."
        )
        raise OdysValidationError(msg)
    if system_entity != profile.entity:
        msg = (
            f"Scenario '{scenario.name}': the {type(profile).__name__} for "
            f"'{profile.entity.name}' does not reference the entity of that name in the energy system."
        )
        raise OdysValidationError(msg)


def validate_conditions_reference_system_assets(condition_set: ConditionSet, portfolio: AssetPortfolio) -> None:
    """Validate that each condition references an asset of the energy system.

    A condition whose asset is missing from the portfolio, or differs from the
    portfolio's asset of that name, would describe an asset that is not being optimized.

    Args:
        condition_set: The initial and final conditions of the run.
        portfolio: The asset portfolio.

    Raises:
        OdysValidationError: If a condition's asset is not the portfolio's asset of that name.

    """
    for condition in condition_set.conditions:
        system_asset = portfolio.assets.get(condition.entity.name)
        if system_asset is None:
            msg = (
                f"The {type(condition).__name__} for '{condition.entity.name}' references an asset "
                "that is not in the energy system."
            )
            raise OdysValidationError(msg)
        if system_asset != condition.entity:
            msg = (
                f"The {type(condition).__name__} for '{condition.entity.name}' does not reference "
                "the asset of that name in the energy system."
            )
            raise OdysValidationError(msg)


def validate_required_initial_conditions_present(condition_set: ConditionSet, portfolio: AssetPortfolio) -> None:
    """Validate that every asset whose results depend on its starting state has an initial condition.

    Args:
        condition_set: The initial and final conditions of the run.
        portfolio: The asset portfolio.

    Raises:
        OdysValidationError: If an asset lacks an initial condition it requires.

    """
    for kind in INITIAL_CONDITION_TYPES:
        for asset in portfolio.assets.values():
            if not isinstance(asset, kind.entity_types) or condition_set.get(kind, asset) is not None:
                continue
            reason = kind.required_for(asset)
            if reason is not None:
                msg = f"{type(asset).__name__} '{asset.name}' needs a {kind.__name__} because {reason}."
                raise OdysValidationError(msg)


def validate_conditions_fit_the_run(
    condition_set: ConditionSet,
    scenarios: Sequence[Scenario],
    horizon: Horizon,
) -> None:
    """Validate every condition against the horizon and what its asset faces in each scenario.

    Conditions are reached through their `validate_horizon` and
    `validate_operating_conditions` queries, like entities through theirs.

    Args:
        condition_set: The initial and final conditions of the run.
        scenarios: The scenarios of the problem, whose profiles have one value per timestep.
        horizon: The time grid of the optimization.

    Raises:
        OdysValidationError: If a condition does not fit the horizon or cannot be met in a scenario.

    """
    for condition in condition_set.conditions:
        condition.validate_horizon(horizon)
        for scenario in scenarios:
            try:
                condition.validate_operating_conditions(_operating_conditions(scenario, condition.entity, horizon))
            except OdysValidationError as err:
                msg = f"Scenario '{scenario.name}': {err}"
                raise OdysValidationError(msg) from err


def validate_required_profiles_present(scenarios: Sequence[Scenario], entities: Sequence[EnergyEntity]) -> None:
    """Validate that every scenario has each required profile for every entity that needs one.

    Args:
        scenarios: Scenarios to check.
        entities: All assets and markets of the energy system.

    Raises:
        OdysValidationError: If a scenario lacks a required profile.

    """
    required_profile_types = [profile_type for profile_type in PROFILE_TYPES if profile_type.required]
    for scenario in scenarios:
        for profile_type in required_profile_types:
            missing = _names_missing_a_profile(scenario, profile_type, entities)
            if missing:
                msg = f"Scenario '{scenario.name}' is missing a {profile_type.__name__} for: {missing}"
                raise OdysValidationError(msg)


def _names_missing_a_profile(
    scenario: Scenario,
    profile_type: type[Profile],
    entities: Sequence[EnergyEntity],
) -> list[str]:
    given = {profile.entity.name for profile in scenario.profiles_of(profile_type)}
    return [
        entity.name for entity in entities if isinstance(entity, profile_type.entity_types) and entity.name not in given
    ]


def validate_profile_lengths(scenarios: Sequence[Scenario], horizon: Horizon) -> None:
    """Validate that every profile has one value per timestep.

    Args:
        scenarios: Scenarios whose profiles to check.
        horizon: The time grid of the optimization.

    Raises:
        OdysValidationError: If a profile's length differs from the number of timesteps.

    """
    for scenario in scenarios:
        for profile in scenario.profiles:
            if profile.number_of_steps != horizon.number_of_steps:
                msg = (
                    f"Scenario '{scenario.name}': the {type(profile).__name__} for '{profile.entity.name}' "
                    f"has {profile.number_of_steps} values, but the horizon has {horizon.number_of_steps} steps."
                )
                raise OdysValidationError(msg)


def validate_has_load_or_market(scenario: Scenario, markets: Sequence[EnergyMarket]) -> None:
    """Validate that the scenario has a load to serve or a market to trade in.

    Args:
        scenario: Scenario to check.
        markets: The energy markets.

    Raises:
        OdysValidationError: If the scenario has no load profile and there is no market.

    """
    if not scenario.profiles_of(LoadProfile) and not scenario.profiles_of(FlexibleLoadProfile) and not markets:
        msg = "Load profile is empty, there is nothing to balance."
        raise OdysValidationError(msg)


def _operating_conditions(scenario: Scenario, entity: EnergyEntity, horizon: Horizon) -> OperatingConditions:
    profile = scenario.profile_for(entity)
    profile_values = profile.operating_values if profile is not None else None
    return OperatingConditions(horizon=horizon, profile_values=profile_values)


def validate_enough_power_to_meet_demand(
    scenario: Scenario,
    entities: Sequence[EnergyEntity],
    horizon: Horizon,
) -> None:
    """Validate that the maximum supply can meet the minimum demand at every timestep.

    Sums, per timestep, every entity's `max_supply` (generation, storage and
    EV discharge, market volume) and every entity's `min_demand` (fixed loads,
    flexible loads after their maximum decrease).

    Args:
        scenario: Scenario to check.
        entities: All assets and markets of the energy system.
        horizon: The time grid of the optimization.

    Raises:
        OdysValidationError: If the minimum demand exceeds the maximum supply at any timestep.

    """
    conditions = [(entity, _operating_conditions(scenario, entity, horizon)) for entity in entities]
    max_supply = _sum_per_timestep([entity.max_supply(c) for entity, c in conditions], horizon)
    min_demand = _sum_per_timestep([entity.min_demand(c) for entity, c in conditions], horizon)
    for t, (supply_t, demand_t) in enumerate(zip(max_supply, min_demand, strict=True)):
        if demand_t > supply_t:
            msg = (
                f"Infeasible problem in scenario '{scenario.name}' at time index {t}: "
                f"minimum demand = {demand_t}, but maximum supply "
                f"(generation + storage and EV discharge + market volume) = {supply_t}."
            )
            raise OdysValidationError(msg)


def _sum_per_timestep(profiles: Sequence[Sequence[float]], horizon: Horizon) -> list[float]:
    return [sum(profile[t] for profile in profiles) for t in range(horizon.number_of_steps)]


def validate_enough_energy_to_meet_demand(
    scenario: Scenario,
    entities: Sequence[EnergyEntity],
    horizon: Horizon,
) -> None:
    """Validate that the energy available over the horizon can meet the minimum energy demand.

    A coarser, horizon-level counterpart to `validate_enough_power_to_meet_demand`:
    a system can pass every per-timestep power check and still be infeasible
    over the horizon, for example when a battery is too small for a long
    horizon. Every entity's `max_energy_supply` is an optimistic bound
    (storage is emptied once, generators run at their available capacity
    throughout), so this check can miss infeasibility but does not raise
    false positives.

    Args:
        scenario: Scenario to check.
        entities: All assets and markets of the energy system.
        horizon: The time grid of the optimization.

    Raises:
        OdysValidationError: If total minimum energy demand exceeds total available energy.

    """
    conditions = [(entity, _operating_conditions(scenario, entity, horizon)) for entity in entities]
    total_energy_demand = sum(sum(entity.min_demand(c)) for entity, c in conditions) * horizon.hours_per_step
    total_energy_supply = sum(entity.max_energy_supply(c) for entity, c in conditions)
    if total_energy_demand > total_energy_supply:
        msg = (
            f"Infeasible problem in scenario '{scenario.name}': total energy demand "
            f"({total_energy_demand}) over the horizon exceeds total available energy "
            f"({total_energy_supply})."
        )
        raise OdysValidationError(msg)
