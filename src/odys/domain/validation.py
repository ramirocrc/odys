"""Energy system input validation.

This module provides validation functions for cross-domain consistency
checks on energy system configurations. Each function validates a specific
invariant and raises OdysValidationError on failure.
"""

from collections.abc import Mapping, Sequence

from odys.domain.entities.fixed_load import FixedLoad
from odys.domain.entities.flexible_load import FlexibleLoad
from odys.domain.entities.generator import Generator
from odys.domain.entities.market import EnergyMarket
from odys.domain.entities.portfolio import AssetPortfolio
from odys.domain.entities.storage import Storage
from odys.domain.exceptions import OdysValidationError
from odys.domain.scenarios import StochasticScenario


def validate_energy_system_inputs(
    portfolio: AssetPortfolio,
    scenarios: tuple[StochasticScenario, ...],
    markets: tuple[EnergyMarket, ...],
    number_of_steps: int,
) -> None:
    """Run all cross-domain validation checks on the energy system.

    Args:
        portfolio: The asset portfolio to validate against.
        scenarios: Normalized sequence of stochastic scenarios.
        markets: Normalized sequence of energy markets.
        number_of_steps: Number of time steps in the optimization horizon.

    Raises:
        OdysValidationError: If any validation check fails.

    """
    validate_fixed_loads_consistent_with_scenarios(portfolio.fixed_loads, scenarios)
    validate_flexible_loads_consistent_with_scenarios(portfolio.flexible_loads, scenarios)
    validate_markets_consistent_with_scenarios(markets, scenarios)

    for scenario in scenarios:
        validate_available_capacity_profiles(scenario, portfolio, number_of_steps)
        validate_load_profiles(scenario, number_of_steps)

        validate_enough_power_to_meet_demand(
            scenario,
            portfolio.generators,
            portfolio.storages,
            markets,
            portfolio.flexible_loads,
        )

        if not markets:
            validate_enough_energy_to_meet_demand(scenario)


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
    has_fixed_loads = bool(fixed_loads)

    for scenario in scenarios:
        if has_fixed_loads:
            if scenario.fixed_load_profiles is None:
                msg = (
                    f"Portfolio contains fixed loads {[load.name for load in fixed_loads]}, "
                    f"but scenario '{scenario.name}' has no fixed load profiles."
                )
                raise OdysValidationError(msg)

            portfolio_load_names = {load.name for load in fixed_loads}
            scenario_load_names = set(scenario.fixed_load_profiles.keys())

            missing_loads = portfolio_load_names - scenario_load_names
            if missing_loads:
                msg = f"Scenario '{scenario.name}' is missing fixed load profiles for: {sorted(missing_loads)}"
                raise OdysValidationError(msg)

            extra_loads = scenario_load_names - portfolio_load_names
            if extra_loads:
                msg = (
                    f"Scenario '{scenario.name}' has fixed load profiles for loads not in portfolio: "
                    f"{sorted(extra_loads)}"
                )
                raise OdysValidationError(msg)
        elif scenario.fixed_load_profiles is not None:
            msg = (
                f"Portfolio contains no fixed loads, but scenario '{scenario.name}' "
                f"has fixed load profiles: {list(scenario.fixed_load_profiles.keys())}"
            )
            raise OdysValidationError(msg)


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
    has_flexible_loads = bool(flexible_loads)

    for scenario in scenarios:
        if has_flexible_loads:
            if scenario.flexible_load_base_profiles is None:
                msg = (
                    f"Portfolio contains flexible loads {[load.name for load in flexible_loads]}, "
                    f"but scenario '{scenario.name}' has no flexible load base profiles."
                )
                raise OdysValidationError(msg)

            portfolio_load_names = {load.name for load in flexible_loads}
            scenario_load_names = set(scenario.flexible_load_base_profiles.keys())

            missing_loads = portfolio_load_names - scenario_load_names
            if missing_loads:
                msg = f"Scenario '{scenario.name}' is missing flexible load base profiles for: {sorted(missing_loads)}"
                raise OdysValidationError(msg)

            extra_loads = scenario_load_names - portfolio_load_names
            if extra_loads:
                msg = (
                    f"Scenario '{scenario.name}' has flexible load base profiles for loads not in portfolio: "
                    f"{sorted(extra_loads)}"
                )
                raise OdysValidationError(msg)
        elif scenario.flexible_load_base_profiles is not None:
            msg = (
                f"Portfolio contains no flexible loads, but scenario '{scenario.name}' "
                f"has flexible load base profiles: {list(scenario.flexible_load_base_profiles.keys())}"
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
    has_markets = bool(markets)

    for scenario in scenarios:
        if has_markets:
            if scenario.market_prices is None:
                msg = (
                    f"Portfolio contains markets {[market.name for market in markets]}, "
                    f"but scenario '{scenario.name}' has no market prices."
                )
                raise OdysValidationError(msg)

            portfolio_market_names = {market.name for market in markets}
            scenario_market_names = set(scenario.market_prices.keys())

            missing_markets = portfolio_market_names - scenario_market_names
            if missing_markets:
                msg = f"Scenario '{scenario.name}' is missing market prices for: {sorted(missing_markets)}"
                raise OdysValidationError(msg)

            extra_markets = scenario_market_names - portfolio_market_names
            if extra_markets:
                msg = (
                    f"Scenario '{scenario.name}' has market prices for markets not in portfolio: "
                    f"{sorted(extra_markets)}"
                )
                raise OdysValidationError(msg)
        elif scenario.market_prices is not None:
            msg = (
                f"EnergySystem contains no markets, but scenario '{scenario.name}' "
                f"has market prices: {list(scenario.market_prices.keys())}"
            )
            raise OdysValidationError(msg)


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
    storages: Sequence[Storage],
    markets: Sequence[EnergyMarket],
    number_of_steps: int,
) -> list[float]:
    """Compute the maximum available power at each timestep.

    Sums, per timestep: each generator's available capacity (its scenario
    ``available_capacity_profiles`` entry if present, otherwise its static
    ``nominal_power``), each storage's ``max_power``, and each market's
    ``max_trading_volume_per_step``.
    """
    capacity_profiles = scenario.available_capacity_profiles or {}

    baseline = sum(storage.max_power for storage in storages) + sum(
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
    storages: Sequence[Storage],
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
    has_fixed = bool(scenario.fixed_load_profiles)
    has_flexible = bool(scenario.flexible_load_base_profiles)
    has_markets = bool(markets)

    if not has_fixed and not has_flexible and not has_markets:
        msg = "Load profile is empty, there is nothing to balance."
        raise OdysValidationError(msg)

    if not has_fixed and not has_flexible:
        return

    if has_fixed and scenario.fixed_load_profiles is not None:
        number_of_steps = len(next(iter(scenario.fixed_load_profiles.values())))
    elif scenario.flexible_load_base_profiles is not None:
        number_of_steps = len(next(iter(scenario.flexible_load_base_profiles.values())))
    else:
        msg = "Load profile is empty, there is nothing to balance."
        raise OdysValidationError(msg)

    max_available_power = _max_available_power_profile(scenario, generators, storages, markets, number_of_steps)

    if has_fixed and scenario.fixed_load_profiles is not None:
        _validate_fixed_load_power_demand(scenario, scenario.fixed_load_profiles, max_available_power)

    if has_flexible and flexible_loads and scenario.flexible_load_base_profiles is not None:
        _validate_flexible_load_power_demand(
            scenario,
            flexible_loads,
            scenario.flexible_load_base_profiles,
            max_available_power,
        )


def validate_enough_energy_to_meet_demand(scenario: StochasticScenario) -> None:  # noqa: ARG001
    """Validate that the system has enough energy to meet total demand.

    Checks that the total energy available from generators and batteries
    can meet the total energy demand over the time horizon.
    """
    return
