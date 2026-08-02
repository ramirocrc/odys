"""Electric vehicle and charger validation checks."""

from odys.domain.entities.portfolio import AssetPortfolio
from odys.domain.exceptions import OdysValidationError


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
    for ev in portfolio.electric_vehicles:
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
    number_of_chargers = len(portfolio.chargers)
    number_of_evs = len(portfolio.electric_vehicles)
    if (number_of_chargers > 0) != (number_of_evs > 0):
        msg = (
            "Portfolio must contain both chargers and electric vehicles, or neither: "
            f"found {number_of_chargers} charger(s) and {number_of_evs} electric vehicle(s)"
        )
        raise OdysValidationError(msg)
