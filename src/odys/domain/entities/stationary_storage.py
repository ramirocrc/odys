"""Stationary storage asset implementation.

This module provides the StationaryStorage class for modeling stationary
energy storage devices in energy system optimization problems.
"""

from odys.domain.entities.storage import Storage


class StationaryStorage(Storage):
    """Stationary storage system in the energy system.

    Represents fixed battery storage assets with charge/discharge capabilities,
    efficiency losses, and state-of-charge dynamics.
    """

    def asset_type(self) -> str:
        """Return the type of storage asset."""
        return "stationary_storage"
