"""Typed time-series profiles that scenarios attach to entities.

A profile is one exogenous time series for one entity in one scenario.
Each profile type references the kind of entity it belongs to, so a
profile cannot be attached to the wrong kind of asset or market.
"""

from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import ClassVar, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from odys.domain.entities.base import EnergyEntity
from odys.domain.entities.fixed_load import FixedLoad
from odys.domain.entities.flexible_load import FlexibleLoad
from odys.domain.entities.generator import Generator
from odys.domain.entities.market import EnergyMarket
from odys.domain.exceptions import OdysValidationError


class Profile(BaseModel, ABC):
    """One exogenous time series for one entity, with one value per timestep.

    Each profile type declares the entity types it applies to and whether
    every such entity needs one in every scenario.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    entity_types: ClassVar[tuple[type[EnergyEntity], ...]]
    required: ClassVar[bool]

    values: Sequence[float] = Field(
        min_length=1,
        description="One value per optimization timestep. Stored as a tuple.",
    )

    @field_validator("values", mode="after")
    @staticmethod
    def _store_values_as_tuple(values: Sequence[float]) -> tuple[float, ...]:
        return tuple(values)

    @property
    @abstractmethod
    def entity(self) -> EnergyEntity:
        """Return the entity this profile belongs to."""


class LoadProfile(Profile):
    """Power demand of a load, in MW per timestep.

    For a `FixedLoad` this is the demand that must be met. For a
    `FlexibleLoad` it is the base profile the optimizer can adjust.
    """

    entity_types: ClassVar[tuple[type[EnergyEntity], ...]] = (FixedLoad, FlexibleLoad)
    required: ClassVar[bool] = True

    load: FixedLoad | FlexibleLoad

    @model_validator(mode="after")
    def _validate_max_decrease_within_base_profile(self) -> Self:
        if not isinstance(self.load, FlexibleLoad):
            return self
        for t, base_t in enumerate(self.values):
            if self.load.max_decrease > base_t:
                msg = (
                    f"Flexible load '{self.load.name}' has max_decrease ({self.load.max_decrease}) "
                    f"greater than the base profile value ({base_t}) at time index {t}. "
                    "This would allow actual load to go negative."
                )
                raise OdysValidationError(msg)
        return self

    @property
    def entity(self) -> FixedLoad | FlexibleLoad:
        """Return the load this demand belongs to."""
        return self.load


class AvailableCapacityProfile(Profile):
    """Available capacity of a generator, in MW per timestep.

    Each value must lie between 0 and the generator's nominal power. A
    generator without this profile can produce up to its nominal power.
    """

    entity_types: ClassVar[tuple[type[EnergyEntity], ...]] = (Generator,)
    required: ClassVar[bool] = False

    generator: Generator

    @model_validator(mode="after")
    def _validate_values_within_nominal_power(self) -> Self:
        for capacity_t in self.values:
            if not 0 <= capacity_t <= self.generator.nominal_power:
                msg = (
                    f"Available capacity value {capacity_t} for asset '{self.generator.name}' is invalid. "
                    f"Values must be between 0 and the asset's nominal power ({self.generator.nominal_power})."
                )
                raise OdysValidationError(msg)
        return self

    @property
    def entity(self) -> Generator:
        """Return the generator this capacity belongs to."""
        return self.generator


class PriceProfile(Profile):
    """Energy price of a market, in currency per MWh per timestep."""

    entity_types: ClassVar[tuple[type[EnergyEntity], ...]] = (EnergyMarket,)
    required: ClassVar[bool] = True

    market: EnergyMarket

    @property
    def entity(self) -> EnergyMarket:
        """Return the market this price belongs to."""
        return self.market


AnyProfile = LoadProfile | AvailableCapacityProfile | PriceProfile
PROFILE_TYPES: tuple[type[Profile], ...] = (LoadProfile, AvailableCapacityProfile, PriceProfile)
