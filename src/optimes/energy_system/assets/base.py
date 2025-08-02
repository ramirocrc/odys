"""Base classes for energy system assets.

This module defines the base classes and interfaces for energy system assets
including the EnergyAsset abstract base class.
"""

from abc import ABC

from pydantic import BaseModel


class EnergyAsset(BaseModel, ABC, frozen=True):
    """Base class for all energy system assets.

    This abstract class defines the common interface for energy assets
    like generators, batteries, and other energy system components.
    """

    name: str
