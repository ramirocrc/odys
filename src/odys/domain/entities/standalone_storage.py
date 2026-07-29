"""Standalone storage asset implementation.

This module provides the StandaloneStorage class for modeling stationary
energy storage devices in energy system optimization problems.
"""

from odys.domain.entities.storage import Storage


class StandaloneStorage(Storage):
    """Standalone (stationary) storage system in the energy system.

    Represents fixed battery storage assets with charge/discharge capabilities,
    efficiency losses, and state-of-charge dynamics.
    """

    def asset_type(self) -> str:
        """Return the type of storage asset."""
        return "standalone_storage"
