"""Base classes for energy system entities.

This module defines `EnergyEntity`, the base of every named thing in the
energy system, and `Asset`, the base of entities the user owns and operates.
"""

from abc import ABC

from pydantic import BaseModel, ConfigDict


class EnergyEntity(BaseModel, ABC):  # pyright: ignore[reportUnsafeMultipleInheritance]
    """Base class for energy system entities.

    An entity is any named thing in the energy system: assets the user owns,
    and external counterparts such as energy markets.
    """

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
    )

    name: str


class Asset(EnergyEntity, ABC):
    """Base class for entities the user owns and operates.

    Only assets can be placed in an `AssetPortfolio`. Markets are entities
    but not assets, and are passed to `EnergySystem` separately.
    """
