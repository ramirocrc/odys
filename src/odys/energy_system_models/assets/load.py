"""Load asset definitions for energy system models."""

from enum import StrEnum
from typing import Self

from pydantic import Field, model_validator

from odys.energy_system_models.assets.base import EnergyAsset
from odys.exceptions import OdysValidationError


class LoadType(StrEnum):
    """Load type enumeration."""

    Fixed = "fixed"
    Flexible = "flexible"


class Load(EnergyAsset):
    """Represents a load asset in the energy system."""

    type: LoadType = Field(
        default=LoadType.Fixed,
        strict=True,
        description="Type of load",
    )

    variable_cost_to_increase: float | None = Field(
        default=None,
        strict=True,
        description="Variable cost of changing the load currency per MWh.",
    )

    variable_cost_to_decrease: float | None = Field(
        default=None,
        strict=True,
        description="Variable cost of changing the load currency per MWh.",
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
