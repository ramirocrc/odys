"""Load asset definitions for energy system models."""

from enum import StrEnum
from typing import Annotated, Self

from pydantic import Field, model_validator

from optimes.energy_system_models.assets.base import EnergyAsset


class LoadType(StrEnum):
    """Load type enumeration."""

    Fixed = "fixed"
    Flexible = "flexible"


class Load(EnergyAsset, frozen=True):
    """Represents a load asset in the energy system."""

    type: Annotated[
        LoadType,
        Field(strict=True, description="Type of load"),
    ] = LoadType.Fixed

    variable_cost_to_increase: Annotated[
        float | None,
        Field(strict=True, description="Variable cost of changing the load currency per MWh."),
    ] = None

    variable_cost_to_decrease: Annotated[
        float | None,
        Field(strict=True, description="Variable cost of changing the load currency per MWh."),
    ] = None

    @model_validator(mode="after")
    def _validate_type_and_variable_cost(self) -> Self:
        if self.type == LoadType.Fixed and (self.variable_cost_to_decrease or self.variable_cost_to_increase):
            msg = "`variable_cost_to_decrease` and `variable_cost_to_incrase` are fields valid only for Flexible loads."
            raise ValueError(msg)
        if self.type == LoadType.Flexible and not (self.variable_cost_to_decrease and self.variable_cost_to_increase):
            msg = "`variable_cost_to_decrease` and `variable_cost_to_incrase` must be specified for Flexible load"
            raise ValueError(msg)
        return self
