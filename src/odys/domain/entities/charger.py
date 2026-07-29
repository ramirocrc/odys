"""Charger entity for electric vehicle charging stations.

This module provides the Charger class for modeling EV charging infrastructure
in energy system optimization problems.
"""

from pydantic import Field

from odys.domain.entities.base import EnergyEntity


class Charger(EnergyEntity):
    """Represents an EV charger in the energy system.

    Chargers are constraint entities that track which EV is connected
    and enforce power limits. They do not participate in the power balance.
    """

    max_power: float = Field(
        strict=True,
        gt=0,
        description="Maximum charging power in MW.",
    )
    efficiency: float = Field(
        default=1.0,
        strict=True,
        gt=0,
        le=1,
        description="Charger efficiency (0-1). Losses occur during charging/discharging.",
    )
