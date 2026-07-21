"""Fixed load asset implementation.

This module provides the FixedLoad class for modeling fixed energy consumption
in energy system optimization problems.
"""

from odys.domain.entities.base import EnergyEntity


class FixedLoad(EnergyEntity):
    """Represents a fixed load asset in the energy system.

    A fixed load is an energy asset that consumes power at a predetermined rate.
    The load profile is specified in the scenario and cannot be adjusted by the optimizer.
    Fixed loads represent inelastic demand that must be met.
    """
