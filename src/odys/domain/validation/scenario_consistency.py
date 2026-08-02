"""Consistency checks between portfolio entities and per-scenario data keyed by entity name."""

from collections.abc import Mapping, Sequence
from typing import NamedTuple

from odys.domain.entities.fixed_load import FixedLoad
from odys.domain.entities.flexible_load import FlexibleLoad
from odys.domain.entities.market import EnergyMarket
from odys.domain.exceptions import OdysValidationError
from odys.domain.scenarios import StochasticScenario


class _DataKind(NamedTuple):
    """Wording used in error messages for one kind of scenario data."""

    entity_label: str
    data_label: str
    extra_noun: str
    container_label: str


_FIXED_LOAD_PROFILES = _DataKind("fixed loads", "fixed load profiles", "loads", "Portfolio")
_FLEXIBLE_LOAD_BASE_PROFILES = _DataKind("flexible loads", "flexible load base profiles", "loads", "Portfolio")
_MARKET_PRICES = _DataKind("markets", "market prices", "markets", "EnergySystem")


def _validate_scenario_data_consistent_with_entities(
    entity_names: list[str],
    scenario: StochasticScenario,
    scenario_data: Mapping[str, object] | None,
    kind: _DataKind,
) -> None:
    """Validate that scenario data keys exactly match the given entity names.

    If there are entities, the scenario must have data for each of them and
    nothing else. If there are no entities, the scenario data must be None.
    """
    if entity_names:
        if scenario_data is None:
            msg = (
                f"Portfolio contains {kind.entity_label} {entity_names}, "
                f"but scenario '{scenario.name}' has no {kind.data_label}."
            )
            raise OdysValidationError(msg)

        expected_names = set(entity_names)
        actual_names = set(scenario_data.keys())

        missing = expected_names - actual_names
        if missing:
            msg = f"Scenario '{scenario.name}' is missing {kind.data_label} for: {sorted(missing)}"
            raise OdysValidationError(msg)

        extra = actual_names - expected_names
        if extra:
            msg = (
                f"Scenario '{scenario.name}' has {kind.data_label} for {kind.extra_noun} not in portfolio: "
                f"{sorted(extra)}"
            )
            raise OdysValidationError(msg)
    elif scenario_data is not None:
        msg = (
            f"{kind.container_label} contains no {kind.entity_label}, but scenario '{scenario.name}' "
            f"has {kind.data_label}: {list(scenario_data.keys())}"
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
        _validate_scenario_data_consistent_with_entities(
            load_names,
            scenario,
            scenario.fixed_load_profiles,
            _FIXED_LOAD_PROFILES,
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
        _validate_scenario_data_consistent_with_entities(
            load_names,
            scenario,
            scenario.flexible_load_base_profiles,
            _FLEXIBLE_LOAD_BASE_PROFILES,
        )


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
        _validate_scenario_data_consistent_with_entities(
            market_names,
            scenario,
            scenario.market_prices,
            _MARKET_PRICES,
        )
