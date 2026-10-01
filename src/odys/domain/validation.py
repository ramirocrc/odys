"""Energy system input validation.

This module provides validation functions for cross-domain consistency
checks on energy system configurations. Each function validates a specific
invariant and raises OdysValidationError on failure.
"""

from collections.abc import Mapping, Sequence
from datetime import timedelta

from pydantic import BaseModel, ConfigDict

from odys.domain.entities.base import Asset
from odys.domain.entities.charger import Charger
from odys.domain.entities.electric_vehicle import ElectricVehicle
from odys.domain.entities.fixed_load import FixedLoad
from odys.domain.entities.flexible_load import FlexibleLoad
from odys.domain.entities.generator import Generator
from odys.domain.entities.market import EnergyMarket
from odys.domain.entities.portfolio import AssetPortfolio
from odys.domain.entities.stationary_storage import StationaryStorage
from odys.domain.exceptions import OdysValidationError
from odys.domain.scenarios import StochasticScenario


def validate_energy_system_inputs(
    portfolio: AssetPortfolio,
    scenarios: tuple[StochasticScenario, ...],
    markets: tuple[EnergyMarket, ...],
    number_of_steps: int,
    timestep: timedelta,
) -> None:
    """Run all cross-domain validation checks on the energy system.

    Args:
        portfolio: The asset portfolio to validate against.
        scenarios: Normalized sequence of stochastic scenarios.
        markets: Normalized sequence of energy markets.
        number_of_steps: Number of time steps in the optimization horizon.
        timestep: Duration of a single optimization timestep.

    Raises:
        OdysValidationError: If any validation check fails.

    """
    validate_assets_are_supported(portfolio)

    generators = portfolio.assets_of(Generator)
    stationary_storages = portfolio.assets_of(StationaryStorage)
    flexible_loads = portfolio.assets_of(FlexibleLoad)
    validate_fixed_loads_consistent_with_scenarios(portfolio.assets_of(FixedLoad), scenarios)
    validate_flexible_loads_consistent_with_scenarios(flexible_loads, scenarios)
    validate_flexible_load_max_decrease_within_base_profile(flexible_loads, scenarios)
    validate_markets_consistent_with_scenarios(markets, scenarios)
    validate_electric_vehicle_trips(portfolio, number_of_steps)
    validate_chargers_and_evs_consistency(portfolio)

    for scenario in scenarios:
        validate_available_capacity_profiles(scenario, portfolio, number_of_steps)
        validate_load_profiles(scenario, number_of_steps)

        validate_enough_power_to_meet_demand(
            scenario,
            generators,
            stationary_storages,
            markets,
            flexible_loads,
        )

        if not markets:
            validate_enough_energy_to_meet_demand(scenario, portfolio, markets, timestep)


_SUPPORTED_ASSET_TYPES: tuple[type[Asset], ...] = (
    Generator,
    StationaryStorage,
    ElectricVehicle,
    Charger,
    FixedLoad,
    FlexibleLoad,
)


def validate_assets_are_supported(portfolio: AssetPortfolio) -> None:
    """Validate that every asset is of a type the optimizer can model.

    A bare `Asset` or a user-defined `Asset` subclass would otherwise be
    accepted and then silently left out of the model.

    Args:
        portfolio: The asset portfolio to validate.

    Raises:
        OdysValidationError: If an asset's type is not supported.

    """
    for asset in portfolio.assets.values():
        if not isinstance(asset, _SUPPORTED_ASSET_TYPES):
            supported = ", ".join(asset_type.__name__ for asset_type in _SUPPORTED_ASSET_TYPES)
            msg = (
                f"Asset type {type(asset).__name__} is not supported by the optimizer: '{asset.name}'. "
                f"Supported types: {supported}."
            )
            raise OdysValidationError(msg)


class _ScenarioProfileSpec(BaseModel):
    """Wording for mismatches between portfolio assets and the scenario profiles keyed by them."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    assets: str
    profiles: str
    extra_assets: str
    owner: str = "Portfolio"


_FIXED_LOAD_PROFILES = _ScenarioProfileSpec(
    assets="fixed loads",
    profiles="fixed load profiles",
    extra_assets="loads",
)
_FLEXIBLE_LOAD_BASE_PROFILES = _ScenarioProfileSpec(
    assets="flexible loads",
    profiles="flexible load base profiles",
    extra_assets="loads",
)
_MARKET_PRICES = _ScenarioProfileSpec(
    assets="markets",
    profiles="market prices",
    extra_assets="markets",
    owner="EnergySystem",
)


def _validate_scenario_profiles_match_assets(
    spec: _ScenarioProfileSpec,
    asset_names: list[str],
    scenario_name: str,
    profiles: Mapping[str, Sequence[float]] | None,
) -> None:
    if not asset_names:
        if profiles is not None:
            msg = (
                f"{spec.owner} contains no {spec.assets}, but scenario '{scenario_name}' "
                f"has {spec.profiles}: {list(profiles.keys())}"
            )
            raise OdysValidationError(msg)
        return

    if profiles is None:
        msg = f"Portfolio contains {spec.assets} {asset_names}, but scenario '{scenario_name}' has no {spec.profiles}."
        raise OdysValidationError(msg)

    missing = set(asset_names) - set(profiles)
    if missing:
        msg = f"Scenario '{scenario_name}' is missing {spec.profiles} for: {sorted(missing)}"
        raise OdysValidationError(msg)

    extra = set(profiles) - set(asset_names)
    if extra:
        msg = (
            f"Scenario '{scenario_name}' has {spec.profiles} for {spec.extra_assets} not in portfolio: {sorted(extra)}"
        )
        raise OdysValidationError(msg)


def validate_fixed_loads_consistent_with_scenarios(
    fixed_loads: Sequence[FixedLoad],
    scenarios: tuple[StochasticScenario, ...],
) -> None:
    """Validate consistency between portfolio fixed loads and scenario load profiles.

    If there are fixed loads in the portfolio, each scenario must have a profile for each.
    If there are no fixed loads, all scenarios should have fixed_load_profiles=None.

    Args:
        fixed_loads: Fixed loads from the asset portfolio.
        scenarios: Stochastic scenarios to validate against.

    Raises:
        OdysValidationError: If load profiles are inconsistent with portfolio loads.

    """
    load_names = [load.name for load in fixed_loads]
    for scenario in scenarios:
        _validate_scenario_profiles_match_assets(
            _FIXED_LOAD_PROFILES,
            load_names,
            scenario.name,
            scenario.fixed_load_profiles,
        )


def validate_flexible_loads_consistent_with_scenarios(
    flexible_loads: Sequence[FlexibleLoad],
    scenarios: tuple[StochasticScenario, ...],
) -> None:
    """Validate consistency between portfolio flexible loads and scenario base profiles.

    If there are flexible loads in the portfolio, each scenario must have a base profile for each.
    If there are no flexible loads, all scenarios should have flexible_load_base_profiles=None.

    Args:
        flexible_loads: Flexible loads from the asset portfolio.
        scenarios: Stochastic scenarios to validate against.

    Raises:
        OdysValidationError: If base profiles are inconsistent with portfolio loads.

    """
    load_names = [load.name for load in flexible_loads]
    for scenario in scenarios:
        _validate_scenario_profiles_match_assets(
            _FLEXIBLE_LOAD_BASE_PROFILES,
            load_names,
            scenario.name,
            scenario.flexible_load_base_profiles,
        )


def validate_flexible_load_max_decrease_within_base_profile(
    flexible_loads: Sequence[FlexibleLoad],
    scenarios: tuple[StochasticScenario, ...],
) -> None:
    """Validate that max_decrease never exceeds the base profile at any timestep.

    If max_decrease is greater than the base load at a given timestep, the
    optimizer would be allowed to push actual load (base - decrease) below
    zero, which is not physically meaningful for a load.

    Args:
        flexible_loads: Flexible loads from the asset portfolio.
        scenarios: Stochastic scenarios to validate against.

    Raises:
        OdysValidationError: If max_decrease exceeds the base profile at any timestep.

    """
    flexible_load_map = {load.name: load for load in flexible_loads}

    for scenario in scenarios:
        for load_name, base_profile in (scenario.flexible_load_base_profiles or {}).items():
            flexible_load = flexible_load_map.get(load_name)
            if flexible_load is not None:
                _validate_max_decrease_within_base_profile(flexible_load, scenario.name, base_profile)


def _validate_max_decrease_within_base_profile(
    flexible_load: FlexibleLoad,
    scenario_name: str,
    base_profile: Sequence[float],
) -> None:
    for t, base_t in enumerate(base_profile):
        if flexible_load.max_decrease > base_t:
            msg = (
                f"Flexible load '{flexible_load.name}' in scenario '{scenario_name}' has "
                f"max_decrease ({flexible_load.max_decrease}) greater than the base "
                f"profile value ({base_t}) at time index {t}. This would allow "
                "actual load to go negative."
            )
            raise OdysValidationError(msg)


def validate_markets_consistent_with_scenarios(
    markets: tuple[EnergyMarket, ...],
    scenarios: tuple[StochasticScenario, ...],
) -> None:
    """Validate consistency between markets and scenario market prices.

    If there are markets, each scenario must have prices for each market.
    If there are no markets, all scenarios should have market_prices=None.

    Args:
        markets: Energy markets to validate against.
        scenarios: Stochastic scenarios to validate against.

    Raises:
        OdysValidationError: If market prices are inconsistent with markets.

    """
    market_names = [market.name for market in markets]
    for scenario in scenarios:
        _validate_scenario_profiles_match_assets(
            _MARKET_PRICES,
            market_names,
            scenario.name,
            scenario.market_prices,
        )


def validate_load_profiles(scenario: StochasticScenario, number_of_steps: int) -> None:
    """Validate that load profile lengths match the number of time steps.

    Args:
        scenario: Scenario whose load profiles to validate.
        number_of_steps: Expected number of time steps.

    Raises:
        OdysValidationError: If a load profile length doesn't match the number of time steps.

    """
    if scenario.fixed_load_profiles is not None:
        for load_name, load_profile in scenario.fixed_load_profiles.items():
            if len(load_profile) != number_of_steps:
                msg = (
                    f"Length of fixed load profile {load_name} ({len(load_profile)})"
                    f" does not match the number of time steps ({number_of_steps})."
                )
                raise OdysValidationError(msg)

    if scenario.flexible_load_base_profiles is not None:
        for load_name, load_profile in scenario.flexible_load_base_profiles.items():
            if len(load_profile) != number_of_steps:
                msg = (
                    f"Length of flexible load base profile {load_name} ({len(load_profile)})"
                    f" does not match the number of time steps ({number_of_steps})."
                )
                raise OdysValidationError(msg)


def validate_available_capacity_profiles(
    scenario: StochasticScenario,
    portfolio: AssetPortfolio,
    number_of_steps: int,
) -> None:
    """Validate that available capacity profiles are only for generators and have correct lengths.

    Args:
        scenario: Scenario whose capacity profiles to validate.
        portfolio: Asset portfolio for asset lookup and type checking.
        number_of_steps: Expected number of time steps.

    Raises:
        OdysValidationError: If capacity is specified for non-generators,
            profile length doesn't match, or values are out of range.

    """
    if scenario.available_capacity_profiles is None:
        return

    for asset_name, capacity_profile in scenario.available_capacity_profiles.items():
        asset = portfolio.get_asset(asset_name)
        if not isinstance(asset, Generator):
            msg = (
                "Available capacity can only be specified for generators, "
                f"but got '{asset_name}' of type {type(asset)}."
            )
            raise OdysValidationError(msg)
        if len(capacity_profile) != number_of_steps:
            msg = (
                f"Length of capacity profile for {asset_name} ({len(capacity_profile)})"
                f" does not match the number of time steps ({number_of_steps})."
            )
            raise OdysValidationError(msg)
        for capacity_i in capacity_profile:
            if not (0 <= capacity_i <= asset.nominal_power):
                msg = (
                    f"Available capacity value {capacity_i} for asset '{asset_name}' is invalid. "
                    f"Values must be between 0 and the asset's nominal power ({asset.nominal_power})."
                )
                raise OdysValidationError(msg)


def _validate_fixed_load_power_demand(
    scenario: StochasticScenario,
    fixed_load_profiles: Mapping[str, Sequence[float]],
    max_available_power: Sequence[float],
) -> None:
    """Validate that fixed load demand can be met."""
    for load_name, load_profile in fixed_load_profiles.items():
        for t, demand_t in enumerate(load_profile):
            if max_available_power[t] < demand_t:
                msg = (
                    f"Infeasible problem in scenario '{scenario.name}' for fixed load '{load_name}' "
                    f"at time index {t}: Demand = {demand_t}, but maximum available "
                    f"generation + storage + market volume = {max_available_power[t]}."
                )
                raise OdysValidationError(msg)


def _validate_flexible_load_power_demand(
    scenario: StochasticScenario,
    flexible_loads: Sequence[FlexibleLoad],
    flexible_load_base_profiles: Mapping[str, Sequence[float]],
    max_available_power: Sequence[float],
) -> None:
    """Validate that flexible load minimum demand can be met."""
    flexible_load_map = {load.name: load for load in flexible_loads}
    for load_name, load_profile in flexible_load_base_profiles.items():
        flexible_load = flexible_load_map.get(load_name)
        if flexible_load is None:
            continue
        for t, demand_t in enumerate(load_profile):
            min_possible_demand = max(0.0, demand_t - flexible_load.max_decrease)
            if max_available_power[t] < min_possible_demand:
                msg = (
                    f"Infeasible problem in scenario '{scenario.name}' for flexible load '{load_name}' "
                    f"at time index {t}: Minimum possible demand (base - max_decrease) = {min_possible_demand}, "
                    f"but maximum available generation + storage + market volume = {max_available_power[t]}."
                )
                raise OdysValidationError(msg)


def _max_available_power_profile(
    scenario: StochasticScenario,
    generators: Sequence[Generator],
    storages: Sequence[StationaryStorage],
    markets: Sequence[EnergyMarket],
    number_of_steps: int,
) -> list[float]:
    """Compute the maximum available power at each timestep.

    Sums, per timestep: each generator's available capacity (its scenario
    ``available_capacity_profiles`` entry if present, otherwise its static
    ``nominal_power``), each storage's ``max_discharge_power``, and each market's
    ``max_trading_volume_per_step``.
    """
    capacity_profiles = scenario.available_capacity_profiles or {}

    baseline = sum(storage.battery.max_discharge_power for storage in storages) + sum(
        market.max_trading_volume_per_step for market in markets
    )
    profile = [baseline] * number_of_steps

    for generator in generators:
        available_profile = capacity_profiles.get(generator.name)
        for t in range(number_of_steps):
            profile[t] += available_profile[t] if available_profile is not None else generator.nominal_power

    return profile


def validate_enough_power_to_meet_demand(
    scenario: StochasticScenario,
    generators: Sequence[Generator],
    storages: Sequence[StationaryStorage],
    markets: Sequence[EnergyMarket],
    flexible_loads: Sequence[FlexibleLoad] | None = None,
) -> None:
    """Validate that maximum available power can meet peak demand at every timestep.

    Checks, at each timestep, that the sum of generator available capacity
    (scenario capacity profile if given, otherwise nominal power), storage
    max power, and market max trading volume can meet demand.

    If there is no fixed or flexible load at all (e.g. a market-only merchant
    generator with no obligation to serve any load), this is a no-op: there is
    no forced demand to validate against.

    Args:
        scenario: Scenario with load profiles to check against.
        generators: Generators in the portfolio.
        storages: Storages in the portfolio.
        markets: Markets in the portfolio.
        flexible_loads: Flexible loads in the portfolio.

    Raises:
        OdysValidationError: If maximum available power is insufficient for peak demand
            at any timestep, or if there is no load and no market at all.

    """
    fixed_load_profiles = scenario.fixed_load_profiles
    flexible_load_base_profiles = scenario.flexible_load_base_profiles
    has_markets = bool(markets)

    if not fixed_load_profiles and not flexible_load_base_profiles and not has_markets:
        msg = "Load profile is empty, there is nothing to balance."
        raise OdysValidationError(msg)

    if not fixed_load_profiles and not flexible_load_base_profiles:
        return

    if fixed_load_profiles:
        number_of_steps = len(next(iter(fixed_load_profiles.values())))
    elif flexible_load_base_profiles:
        number_of_steps = len(next(iter(flexible_load_base_profiles.values())))
    else:
        msg = "Load profile is empty, there is nothing to balance."
        raise OdysValidationError(msg)

    max_available_power = _max_available_power_profile(scenario, generators, storages, markets, number_of_steps)

    if fixed_load_profiles:
        _validate_fixed_load_power_demand(scenario, fixed_load_profiles, max_available_power)

    if flexible_load_base_profiles and flexible_loads:
        _validate_flexible_load_power_demand(
            scenario,
            flexible_loads,
            flexible_load_base_profiles,
            max_available_power,
        )


def validate_enough_energy_to_meet_demand(
    scenario: StochasticScenario,
    portfolio: AssetPortfolio,
    markets: Sequence[EnergyMarket],
    timestep: timedelta,
) -> None:
    """Validate that total energy available over the horizon can meet total energy demand.

    Checks that the sum, across all timesteps, of generator available energy
    (capacity profile if given, otherwise nominal power, times timestep
    duration), storage energy capacity, and market trading energy can meet
    the sum of fixed and minimum flexible load energy demand over the same
    horizon.

    This is a coarser, horizon-level counterpart to
    ``validate_enough_power_to_meet_demand``: a system can pass every
    per-timestep power check and still be infeasible over the full horizon,
    for example when total available energy (limited fuel, a small battery
    relative to a long horizon) is not enough even though instantaneous
    power always is.

    Two simplifications, matching how this check is specified: storage
    contributes its full capacity once (not scaled by however many times it
    could cycle over the horizon), and a generator without a capacity
    profile is assumed able to run at nominal power for every timestep
    (ignoring ramp rates and minimum up/down time). Both make this an
    optimistic bound on available energy, so it can under-detect
    infeasibility but should not raise false positives from those factors
    alone.

    If there is no fixed or flexible load at all, this is a no-op.

    The minimum flexible load demand term (base minus max_decrease) assumes
    max_decrease never exceeds the base profile at any timestep. That
    invariant is enforced separately, unconditionally, before this function
    runs (see ``validate_flexible_load_max_decrease_within_base_profile``),
    so it is not re-checked here.

    Args:
        scenario: Scenario with load profiles to check against.
        portfolio: The asset portfolio to validate against.
        markets: Markets in the portfolio.
        timestep: Duration of a single optimization timestep.

    Raises:
        OdysValidationError: If total available energy is insufficient for total
            energy demand over the horizon.

    """
    demand_profiles = scenario.fixed_load_profiles or scenario.flexible_load_base_profiles
    if not demand_profiles:
        return

    timestep_hours = timestep.total_seconds() / 3600
    number_of_steps = len(next(iter(demand_profiles.values())))

    total_energy_demand = _total_energy_demand(scenario, portfolio.assets_of(FlexibleLoad), timestep_hours)
    total_energy_supply = _total_energy_supply(scenario, portfolio, markets, number_of_steps, timestep_hours)

    if total_energy_demand > total_energy_supply:
        msg = (
            f"Infeasible problem in scenario '{scenario.name}': total energy demand "
            f"({total_energy_demand}) over the horizon exceeds total available energy "
            f"({total_energy_supply})."
        )
        raise OdysValidationError(msg)


def _total_energy_demand(
    scenario: StochasticScenario,
    flexible_loads: Sequence[FlexibleLoad],
    timestep_hours: float,
) -> float:
    fixed_profiles = (scenario.fixed_load_profiles or {}).values()
    total_fixed_energy = sum(sum(profile) for profile in fixed_profiles) * timestep_hours

    flexible_load_map = {load.name: load for load in flexible_loads}
    total_flexible_energy = 0.0
    for load_name, profile in (scenario.flexible_load_base_profiles or {}).items():
        flexible_load = flexible_load_map.get(load_name)
        if flexible_load is not None:
            total_flexible_energy += sum(value - flexible_load.max_decrease for value in profile) * timestep_hours

    return total_fixed_energy + total_flexible_energy


def _total_energy_supply(
    scenario: StochasticScenario,
    portfolio: AssetPortfolio,
    markets: Sequence[EnergyMarket],
    number_of_steps: int,
    timestep_hours: float,
) -> float:
    capacity_profiles = scenario.available_capacity_profiles or {}
    total_generator_energy = 0.0
    for generator in portfolio.assets_of(Generator):
        available_profile = capacity_profiles.get(generator.name)
        if available_profile is not None:
            total_generator_energy += sum(available_profile) * timestep_hours
        else:
            total_generator_energy += generator.nominal_power * number_of_steps * timestep_hours

    total_storage_energy = sum(storage.battery.capacity for storage in portfolio.assets_of(StationaryStorage))
    total_market_volume = sum(market.max_trading_volume_per_step for market in markets)
    total_market_energy = total_market_volume * number_of_steps * timestep_hours

    return total_generator_energy + total_storage_energy + total_market_energy


def validate_electric_vehicle_trips(
    portfolio: AssetPortfolio,
    number_of_steps: int,
) -> None:
    """Validate that all electric vehicle trips are valid.

    Checks that trips for each vehicle do not overlap and that all trips
    fall within the optimization horizon.

    Args:
        portfolio: The asset portfolio containing electric vehicles.
        number_of_steps: Number of time steps in the optimization horizon.

    Raises:
        OdysValidationError: If any trip validation fails.

    """
    for ev in portfolio.assets_of(ElectricVehicle):
        ev.validate_no_overlapping_trips()
        ev.validate_trips_within_horizon(number_of_steps)
        ev.validate_min_soc_at_departure_feasible()


def validate_chargers_and_evs_consistency(portfolio: AssetPortfolio) -> None:
    """Validate that chargers and electric vehicles are either both present or both absent.

    Electric vehicles can only charge through a charger, and a charger without
    electric vehicles serves no purpose.

    Args:
        portfolio: The asset portfolio containing chargers and electric vehicles.

    Raises:
        OdysValidationError: If the portfolio contains chargers without electric
            vehicles, or electric vehicles without chargers.

    """
    number_of_chargers = len(portfolio.assets_of(Charger))
    number_of_evs = len(portfolio.assets_of(ElectricVehicle))
    if (number_of_chargers > 0) != (number_of_evs > 0):
        msg = (
            "Portfolio must contain both chargers and electric vehicles, or neither: "
            f"found {number_of_chargers} charger(s) and {number_of_evs} electric vehicle(s)"
        )
        raise OdysValidationError(msg)
