"""Consistency checks between portfolio entities and per-scenario data keyed by entity name."""

from collections.abc import Sequence

from odys.domain.entities.fixed_load import FixedLoad
from odys.domain.entities.flexible_load import FlexibleLoad
from odys.domain.entities.market import EnergyMarket
from odys.domain.exceptions import OdysValidationError
from odys.domain.scenarios import StochasticScenario


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
