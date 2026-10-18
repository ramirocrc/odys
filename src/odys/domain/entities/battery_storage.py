"""Battery storage asset implementation.

This module provides the BatteryStorage class for modeling grid-connected
energy storage devices in energy system optimization problems.
"""

from odys.domain.entities.base import Asset
from odys.domain.entities.battery import Battery
from odys.domain.horizon import OperatingConditions


class BatteryStorage(Asset):
    """Battery storage (BESS): a battery at a fixed, grid-connected site.

    The asset is what you own and name. The battery describes the
    physics (capacity, power limits, efficiencies, state of charge).
    """

    battery: Battery

    def max_supply(self, conditions: OperatingConditions) -> tuple[float, ...]:
        """Return the battery's maximum discharge power at each timestep, in MW."""
        return (self.battery.max_discharge_power,) * conditions.horizon.number_of_steps

    def max_energy_supply(self, conditions: OperatingConditions) -> float:
        """Return the energy the battery can discharge over the horizon, in MWh.

        A full battery is emptied at most once, at no more than its maximum discharge power.
        """
        return min(self.battery.capacity, super().max_energy_supply(conditions))
