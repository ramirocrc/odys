"""Load asset definitions for energy system models."""

from enum import StrEnum
from typing import Self

from pydantic import Field, model_validator

from odys.domain.entities.base import EnergyEntity
from odys.domain.exceptions import OdysValidationError


class LoadType(StrEnum):
    """Enumeration of supported load types.

    Load types determine how a load behaves during optimization.
    Fixed loads remain constant, while flexible loads can be adjusted
    within the constraints defined by the model.
    """

    Fixed = "fixed"
    Flexible = "flexible"


class Load(EnergyEntity):
    """Represents a load asset in the energy system.

    A load is an energy asset that consumes power. Depending on its type, a load
    may be fixed (inelastic demand, cannot be adjusted by the optimizer) or
    flexible (demand can be adjusted within constraints). Flexible loads have
    variable costs for increasing or decreasing demand.

    Attributes:
        type: Specifies whether the load is fixed or flexible.
        variable_cost_to_increase: Cost per MWh for increasing load demand
            (required for flexible loads).
        variable_cost_to_decrease: Cost per MWh for decreasing load demand
            (required for flexible loads).
    """

    type: LoadType = Field(
        default=LoadType.Fixed,
        strict=True,
        description="Type of load",
    )

    variable_cost_to_increase: float | None = Field(
        default=None,
        strict=True,
        description="Variable cost per MWh for increasing load demand.",
    )

    variable_cost_to_decrease: float | None = Field(
        default=None,
        strict=True,
        description="Variable cost per MWh for decreasing load demand.",
    )

    @model_validator(mode="after")
    def _validate_type_and_variable_cost(self) -> Self:
        if self.type == LoadType.Fixed and (
            self.variable_cost_to_decrease is not None or self.variable_cost_to_increase is not None
        ):
            msg = (
                "`variable_cost_to_decrease` and `variable_cost_to_increase` are fields valid only for Flexible loads."
            )
            raise OdysValidationError(msg)
        if self.type == LoadType.Flexible and (
            self.variable_cost_to_decrease is None or self.variable_cost_to_increase is None
        ):
            msg = "`variable_cost_to_decrease` and `variable_cost_to_increase` must be specified for Flexible loads."
            raise OdysValidationError(msg)
        return self
