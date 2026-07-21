"""Flexible load asset implementation.

This module provides the FlexibleLoad class for modeling adjustable energy consumption
in energy system optimization problems.
"""

from pydantic import Field

from odys.domain.entities.base import EnergyEntity


class FlexibleLoad(EnergyEntity):
    """Represents a flexible load asset in the energy system.

    A flexible load is an energy asset that can adjust its consumption within
    specified bounds to optimize profit. The optimizer can increase or decrease
    the load from its base profile based on economic incentives.

    The decision to adjust load depends on the relationship between the
    value_of_consumption (economic value of consuming electricity) and the
    marginal cost of supply. The marginal cost is determined implicitly by
    the power balance constraint: when the optimizer increases load, it must
    procure more energy from the cheapest available source (generators or
    markets). When it decreases load, it frees up that supply for other uses
    (e.g., selling to markets).

    When value_of_consumption exceeds the marginal supply cost, increasing
    load is profitable. When the marginal supply cost exceeds
    value_of_consumption, decreasing load saves money.
    """

    max_increase: float = Field(
        strict=True,
        gt=0,
        description="Maximum amount the load can increase above base profile in MW.",
    )

    max_decrease: float = Field(
        strict=True,
        gt=0,
        description="Maximum amount the load can decrease below base profile in MW.",
    )

    value_of_consumption: float = Field(
        strict=True,
        ge=0,
        description="Economic value of consuming electricity in currency per MWh.",
    )
