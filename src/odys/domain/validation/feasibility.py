"""Coarse feasibility checks: can available power and energy meet demand."""

from collections.abc import Mapping, Sequence
from datetime import timedelta

from odys.domain.entities.flexible_load import FlexibleLoad
from odys.domain.entities.generator import Generator
from odys.domain.entities.market import EnergyMarket
from odys.domain.entities.portfolio import AssetPortfolio
from odys.domain.entities.standalone_storage import StandaloneStorage
from odys.domain.exceptions import OdysValidationError
from odys.domain.scenarios import StochasticScenario


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
    storages: Sequence[StandaloneStorage],
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

    baseline = sum(storage.max_discharge_power for storage in storages) + sum(
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
    storages: Sequence[StandaloneStorage],
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
    fixed_load_profiles = scenario.fixed_load_profiles
    flexible_load_base_profiles = scenario.flexible_load_base_profiles

    if not fixed_load_profiles and not flexible_load_base_profiles:
        return

    timestep_hours = timestep.total_seconds() / 3600

    if fixed_load_profiles:
        number_of_steps = len(next(iter(fixed_load_profiles.values())))
    elif flexible_load_base_profiles:
        number_of_steps = len(next(iter(flexible_load_base_profiles.values())))
    else:  # pragma: no cover - unreachable, the check above already excludes this
        return

    total_fixed_energy = 0.0
    if fixed_load_profiles:
        total_fixed_energy = sum(sum(profile) for profile in fixed_load_profiles.values()) * timestep_hours

    flexible_load_map = {load.name: load for load in portfolio.flexible_loads}
    total_flexible_energy = 0.0
    for load_name, profile in (flexible_load_base_profiles or {}).items():
        flexible_load = flexible_load_map.get(load_name)
        if flexible_load is None:
            continue
        total_flexible_energy += sum(value - flexible_load.max_decrease for value in profile) * timestep_hours

    total_energy_demand = total_fixed_energy + total_flexible_energy

    capacity_profiles = scenario.available_capacity_profiles or {}
    total_generator_energy = 0.0
    for generator in portfolio.generators:
        available_profile = capacity_profiles.get(generator.name)
        if available_profile is not None:
            total_generator_energy += sum(available_profile) * timestep_hours
        else:
            total_generator_energy += generator.nominal_power * number_of_steps * timestep_hours

    total_storage_energy = sum(storage.capacity for storage in portfolio.standalone_storages)
    total_market_volume = sum(market.max_trading_volume_per_step for market in markets)
    total_market_energy = total_market_volume * number_of_steps * timestep_hours

    total_energy_supply = total_generator_energy + total_storage_energy + total_market_energy

    if total_energy_demand > total_energy_supply:
        msg = (
            f"Infeasible problem in scenario '{scenario.name}': total energy demand "
            f"({total_energy_demand}) over the horizon exceeds total available energy "
            f"({total_energy_supply})."
        )
        raise OdysValidationError(msg)
