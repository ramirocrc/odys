"""Stationary storage asset implementation.

This module provides the StationaryStorage class for modeling stationary
energy storage devices in energy system optimization problems.
"""

from odys.domain.entities.base import Asset
from odys.domain.entities.battery import Battery


class StationaryStorage(Asset):
    """Stationary storage system in the energy system.

    A fixed site that stores energy in a battery. The battery describes the
    physics (capacity, power limits, efficiencies, state of charge).
    """

    battery: Battery
