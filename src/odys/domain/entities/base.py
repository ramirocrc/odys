"""Base classes for energy system assets.

This module defines the base classes and interfaces for energy system assets
including the EnergyAsset abstract base class.
"""

from abc import ABC

from pydantic import BaseModel, ConfigDict


class EnergyEntity(BaseModel, ABC):  # pyright: ignore[reportUnsafeMultipleInheritance]
    """Base class for energy system entities.

    This abstract class defines the common interface for energy assets
    like generators, batteries, and other energy system components.
    """

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
    )

    name: str
