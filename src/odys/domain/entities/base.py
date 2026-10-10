"""Base classes for energy system entities.

This module defines `EnergyEntity`, the base of every named thing in the
energy system, and `Asset`, the base of entities the user owns and operates.
"""

from abc import ABC

from pydantic import BaseModel, ConfigDict

from odys.domain.horizon import Horizon, OperatingConditions


class EnergyEntity(BaseModel, ABC):  # pyright: ignore[reportUnsafeMultipleInheritance]
    """Base class for energy system entities.

    An entity is any named thing in the energy system: assets the user owns,
    and external counterparts such as energy markets.

    The capability queries (`max_supply`, `min_demand`, `max_energy_supply`
    and `validate_horizon`) let system-level validation treat every entity
    alike. Each defaults to "none"; entity types that supply power, demand
    power or depend on the horizon override them.
    """

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
    )

    name: str

    def max_supply(self, conditions: OperatingConditions) -> tuple[float, ...]:
        """Return the most power this entity can inject at each timestep, in MW.

        Args:
            conditions: The horizon and this entity's profile values in one scenario.

        Returns:
            One value per timestep. The default is zero.
        """
        return (0.0,) * conditions.horizon.number_of_steps

    def min_demand(self, conditions: OperatingConditions) -> tuple[float, ...]:
        """Return the least power this entity must withdraw at each timestep, in MW.

        Args:
            conditions: The horizon and this entity's profile values in one scenario.

        Returns:
            One value per timestep. The default is zero.
        """
        return (0.0,) * conditions.horizon.number_of_steps

    def max_energy_supply(self, conditions: OperatingConditions) -> float:
        """Return the most energy this entity can inject over the horizon, in MWh.

        Args:
            conditions: The horizon and this entity's profile values in one scenario.

        Returns:
            The default is `max_supply` summed over the horizon, times the step length in hours.
        """
        return sum(self.max_supply(conditions)) * conditions.horizon.hours_per_step

    def validate_horizon(self, horizon: Horizon) -> None:
        """Check that this entity fits the optimization horizon. The default accepts any horizon.

        Args:
            horizon: The time grid of the optimization.

        Raises:
            OdysValidationError: If the entity does not fit the horizon.
        """


class Asset(EnergyEntity, ABC):
    """Base class for entities the user owns and operates.

    Only assets can be placed in an `AssetPortfolio`. Markets are entities
    but not assets, and are passed to `EnergySystem` separately.
    """
