"""Energy system input validation.

This module provides validation functions for cross-domain consistency
checks on energy system configurations. Each function validates a specific
invariant and raises OdysValidationError on failure.
"""

from collections.abc import Sequence

from odys.energy_system_models.assets.generator import Generator
from odys.energy_system_models.assets.load import Load
from odys.energy_system_models.assets.portfolio import AssetPortfolio
from odys.energy_system_models.assets.storage import Storage
from odys.energy_system_models.markets import EnergyMarket
from odys.energy_system_models.scenarios import StochasticScenario
from odys.exceptions import OdysValidationError


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
    validate_loads_consistent_with_scenarios(portfolio.loads, scenarios)
    validate_markets_consistent_with_scenarios(markets, scenarios)

    for scenario in scenarios:
        validate_available_capacity_profiles(scenario, portfolio, number_of_steps)
        validate_load_profiles(scenario, number_of_steps)

        if not markets:
            validate_enough_power_to_meet_demand(scenario, portfolio.generators, portfolio.storages)
            validate_enough_energy_to_meet_demand(scenario)


def validate_loads_consistent_with_scenarios(
    loads: Sequence[Load],
    scenarios: tuple[StochasticScenario, ...],
) -> None:
    """Validate consistency between portfolio loads and scenario load profiles.

    If there are loads in the portfolio, each scenario must have a profile for each load.
    If there are no loads, all scenarios should have load_profiles=None.

    Args:
        loads: Loads from the asset portfolio.
        scenarios: Stochastic scenarios to validate against.

    Raises:
        OdysValidationError: If load profiles are inconsistent with portfolio loads.

    """
    has_loads = bool(loads)

    for scenario in scenarios:
        if has_loads:
            if scenario.load_profiles is None:
                msg = (
                    f"Portfolio contains loads {[load.name for load in loads]}, "
                    f"but scenario '{scenario.name}' has no load profiles."
                )
                raise OdysValidationError(msg)

            portfolio_load_names = {load.name for load in loads}
            scenario_load_names = set(scenario.load_profiles.keys())

            missing_loads = portfolio_load_names - scenario_load_names
            if missing_loads:
                msg = f"Scenario '{scenario.name}' is missing load profiles for: {sorted(missing_loads)}"
                raise OdysValidationError(msg)

            extra_loads = scenario_load_names - portfolio_load_names
            if extra_loads:
                msg = f"Scenario '{scenario.name}' has load profiles for loads not in portfolio: {sorted(extra_loads)}"
                raise OdysValidationError(msg)
        elif scenario.load_profiles is not None:
            msg = (
                f"Portfolio contains no loads, but scenario '{scenario.name}' "
                f"has load profiles: {list(scenario.load_profiles.keys())}"
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
    if scenario.load_profiles is None:
        return

    for load_name, load_profile in scenario.load_profiles.items():
        if len(load_profile) != number_of_steps:
            msg = (
                f"Length of load profile {load_name} ({len(load_profile)})"
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


def validate_enough_power_to_meet_demand(
    scenario: StochasticScenario,
    generators: Sequence[Generator],
    storages: Sequence[Storage],
) -> None:
    """Validate that maximum available power can meet peak demand.

    Checks that the sum of generator nominal power and storage capacity
    can meet the maximum demand at any time period.

    Args:
        scenario: Scenario with load profiles to check against.
        generators: Generators in the portfolio.
        storages: Storages in the portfolio.

    Raises:
        OdysValidationError: If maximum available power is insufficient for peak demand.

    """
    if scenario.load_profiles is None:
        msg = "Load profile is empty, there is nothing to balance."
        raise OdysValidationError(msg)

    cumulative_generators_power = sum(gen.nominal_power for gen in generators)
    # TODO: We assume full capacity can be discharged -> Needs to be limited by max power
    cumulative_storage_capacities = sum(storage.capacity for storage in storages)
    max_available_power = cumulative_generators_power + cumulative_storage_capacities

    for load_name, load_profile in scenario.load_profiles.items():
        for t, demand_t in enumerate(load_profile):
            if max_available_power < demand_t:
                msg = (
                    f"Infeasible problem in scenario '{scenario.name}' for load '{load_name}' at time index {t}: "
                    f"Demand = {demand_t}, but maximum available generation + storage = {max_available_power}."
                )
                raise OdysValidationError(msg)


def validate_enough_energy_to_meet_demand(scenario: StochasticScenario) -> None:  # noqa: ARG001
    """Validate that the system has enough energy to meet total demand.

    Checks that the total energy available from generators and batteries
    can meet the total energy demand over the time horizon.
    """
    # TODO: Implement energy adequacy validation
    return
