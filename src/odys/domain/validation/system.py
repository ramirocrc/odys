"""Top-level orchestration of all cross-domain validation checks."""

from datetime import timedelta

from odys.domain.entities.market import EnergyMarket
from odys.domain.entities.portfolio import AssetPortfolio
from odys.domain.scenarios import StochasticScenario
from odys.domain.validation.electric_vehicles import (
    validate_chargers_and_evs_consistency,
    validate_electric_vehicle_trips,
)
from odys.domain.validation.feasibility import (
    validate_enough_energy_to_meet_demand,
    validate_enough_power_to_meet_demand,
)
from odys.domain.validation.profiles import (
    validate_available_capacity_profiles,
    validate_flexible_load_max_decrease_within_base_profile,
    validate_load_profiles,
)
from odys.domain.validation.scenario_consistency import (
    validate_fixed_loads_consistent_with_scenarios,
    validate_flexible_loads_consistent_with_scenarios,
    validate_markets_consistent_with_scenarios,
)


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
    validate_fixed_loads_consistent_with_scenarios(portfolio.fixed_loads, scenarios)
    validate_flexible_loads_consistent_with_scenarios(portfolio.flexible_loads, scenarios)
    validate_flexible_load_max_decrease_within_base_profile(portfolio.flexible_loads, scenarios)
    validate_markets_consistent_with_scenarios(markets, scenarios)
    validate_electric_vehicle_trips(portfolio, number_of_steps)
    validate_chargers_and_evs_consistency(portfolio)

    for scenario in scenarios:
        validate_available_capacity_profiles(scenario, portfolio, number_of_steps)
        validate_load_profiles(scenario, number_of_steps)

        validate_enough_power_to_meet_demand(
            scenario,
            portfolio.generators,
            portfolio.standalone_storages,
            markets,
            portfolio.flexible_loads,
        )

        if not markets:
            validate_enough_energy_to_meet_demand(scenario, portfolio, markets, timestep)
