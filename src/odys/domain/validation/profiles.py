"""Shape and range checks on per-scenario profiles."""

from collections.abc import Sequence

from odys.domain.entities.flexible_load import FlexibleLoad
from odys.domain.entities.generator import Generator
from odys.domain.entities.portfolio import AssetPortfolio
from odys.domain.exceptions import OdysValidationError
from odys.domain.scenarios import StochasticScenario


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
        if scenario.flexible_load_base_profiles is None:
            continue

        for load_name, base_profile in scenario.flexible_load_base_profiles.items():
            flexible_load = flexible_load_map.get(load_name)
            if flexible_load is None:
                continue

            for t, base_t in enumerate(base_profile):
                if flexible_load.max_decrease > base_t:
                    msg = (
                        f"Flexible load '{load_name}' in scenario '{scenario.name}' has "
                        f"max_decrease ({flexible_load.max_decrease}) greater than the base "
                        f"profile value ({base_t}) at time index {t}. This would allow "
                        "actual load to go negative."
                    )
                    raise OdysValidationError(msg)
