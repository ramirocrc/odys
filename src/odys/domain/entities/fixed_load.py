"""Fixed load asset implementation.

This module provides the FixedLoad class for modeling fixed energy consumption
in energy system optimization problems.
"""

from odys.domain.entities.base import Asset
from odys.domain.horizon import OperatingConditions


class FixedLoad(Asset):
    """Represents a fixed load asset in the energy system.

    A fixed load is an energy asset that consumes power at a predetermined rate.
    The load profile is specified in the scenario and cannot be adjusted by the optimizer.
    Fixed loads represent inelastic demand that must be met.
    """

    def min_demand(self, conditions: OperatingConditions) -> tuple[float, ...]:
        """Return the load profile, in MW, which must be met in full."""
        if conditions.profile_values is not None:
            return conditions.profile_values
        return super().min_demand(conditions)
