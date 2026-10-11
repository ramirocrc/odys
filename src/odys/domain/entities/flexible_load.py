"""Flexible load asset implementation.

This module provides the FlexibleLoad class for modeling adjustable energy consumption
in energy system optimization problems.
"""

from typing import Self

from pydantic import Field, model_validator

from odys.domain.entities.base import Asset
from odys.domain.exceptions import OdysValidationError
from odys.domain.horizon import OperatingConditions


class FlexibleLoad(Asset):
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

    Each side of the adjustment range can be bounded relative to the base
    profile (max_decrease, max_increase) or in absolute terms (min_load,
    max_load). At least one bound is required per side; when both are given,
    the absolute bound takes precedence.
    """

    max_increase: float | None = Field(
        default=None,
        strict=True,
        gt=0,
        description="Maximum amount the load can increase above base profile in MW.",
    )

    max_decrease: float | None = Field(
        default=None,
        strict=True,
        gt=0,
        description="Maximum amount the load can decrease below base profile in MW.",
    )

    min_load: float | None = Field(
        default=None,
        strict=True,
        ge=0,
        description="Absolute minimum consumption in MW. Overrides max_decrease when set.",
    )

    max_load: float | None = Field(
        default=None,
        strict=True,
        gt=0,
        description="Absolute maximum consumption in MW. Overrides max_increase when set.",
    )

    value_of_consumption: float = Field(
        strict=True,
        ge=0,
        description="Economic value of consuming electricity in currency per MWh.",
    )

    @model_validator(mode="after")
    def _validate_bounds(self) -> Self:
        if self.max_decrease is None and self.min_load is None:
            msg = f"Flexible load '{self.name}' needs a lower bound: set max_decrease or min_load."
            raise OdysValidationError(msg)
        if self.max_increase is None and self.max_load is None:
            msg = f"Flexible load '{self.name}' needs an upper bound: set max_increase or max_load."
            raise OdysValidationError(msg)
        if self.min_load is not None and self.max_load is not None and self.min_load > self.max_load:
            msg = f"min_load ({self.min_load}) must be ≤ max_load ({self.max_load})."
            raise OdysValidationError(msg)
        return self

    def min_demand(self, conditions: OperatingConditions) -> tuple[float, ...]:
        """Return `min_load` if set, else the base profile reduced by `max_decrease` (never below zero), in MW."""
        if conditions.profile_values is None:
            return super().min_demand(conditions)
        if self.min_load is not None:
            return (self.min_load,) * len(conditions.profile_values)
        max_decrease = self.max_decrease or 0.0  # set whenever min_load is not, by _validate_bounds
        return tuple(max(0.0, base - max_decrease) for base in conditions.profile_values)
