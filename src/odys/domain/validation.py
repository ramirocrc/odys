"""Energy system input validation.

This module holds the rules that span entities and scenarios. Rules about a
single entity or profile live on that object and run when it is built. The
rules here treat every entity alike through its capability queries
(`max_supply`, `min_demand`, `max_energy_supply`, `validate_horizon`) and
every profile through its type's `entity_types` and `required` flags. A new
asset type is covered by overriding those queries (that the optimizer models
it is checked against its formulations, in `odys.optimization.formulations`);
a new profile type by adding it to `AnyProfile` and `PROFILE_TYPES` in
`profiles.py`.
"""

from collections.abc import Mapping, Sequence

from odys.domain.entities.base import Asset, EnergyEntity
from odys.domain.entities.market import EnergyMarket
from odys.domain.entities.portfolio import AssetPortfolio
from odys.domain.exceptions import OdysValidationError
from odys.domain.horizon import Horizon, OperatingConditions
from odys.domain.profiles import PROFILE_TYPES, LoadProfile, Profile
from odys.domain.scenario import Scenario, ScenarioSet


def validate_energy_system_inputs(
    portfolio: AssetPortfolio,
    scenario_set: ScenarioSet,
    markets: Sequence[EnergyMarket],
    horizon: Horizon,
) -> None:
    """Run all cross-domain validation checks on the energy system.

    Args:
        portfolio: The asset portfolio to validate against.
        scenario_set: The scenarios of the problem.
        markets: Normalized sequence of energy markets.
        horizon: The time grid of the optimization.

    Raises:
        OdysValidationError: If any validation check fails.

    """
    entities: tuple[EnergyEntity, ...] = (*portfolio.assets.values(), *markets)
    for entity in entities:
        entity.validate_horizon(horizon)

    scenarios = scenario_set.scenarios
    validate_profiles_reference_system_entities(scenarios, portfolio, markets)
    validate_required_profiles_present(scenarios, entities)
    validate_profile_lengths(scenarios, horizon)

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
            if len(profile.values) != horizon.number_of_steps:
                msg = (
                    f"Scenario '{scenario.name}': the {type(profile).__name__} for '{profile.entity.name}' "
                    f"has {len(profile.values)} values, but the horizon has {horizon.number_of_steps} steps."
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
    if not scenario.profiles_of(LoadProfile) and not markets:
        msg = "Load profile is empty, there is nothing to balance."
        raise OdysValidationError(msg)


def _operating_conditions(scenario: Scenario, entity: EnergyEntity, horizon: Horizon) -> OperatingConditions:
    profile = scenario.profile_for(entity)
    profile_values = tuple(profile.values) if profile is not None else None
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
