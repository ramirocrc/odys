"""Typed time-series profiles that scenarios attach to entities.

A profile is the exogenous time series of one entity in one scenario.
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
    """The exogenous time series of one entity, with one value per timestep in each series.

    Each profile type declares the entity types it applies to and whether
    every such entity needs one in every scenario.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    entity_types: ClassVar[tuple[type[EnergyEntity], ...]]
    required: ClassVar[bool]

    @property
    @abstractmethod
    def entity(self) -> EnergyEntity:
        """Return the entity this profile belongs to."""

    @property
    @abstractmethod
    def number_of_steps(self) -> int:
        """Return the number of timesteps the profile covers."""

    @property
    @abstractmethod
    def operating_values(self) -> tuple[float, ...]:
        """Return the values the entity's capability queries read, one per timestep."""


class SeriesProfile(Profile, ABC):
    """A profile with a single time series, `values`."""

    values: Sequence[float] = Field(
        min_length=1,
        description="One value per optimization timestep. Stored as a tuple.",
    )

    @field_validator("values", mode="after")
    @staticmethod
    def _store_values_as_tuple(values: Sequence[float]) -> tuple[float, ...]:
        return tuple(values)

    @property
    def number_of_steps(self) -> int:
        """Return the number of values."""
        return len(self.values)

    @property
    def operating_values(self) -> tuple[float, ...]:
        """Return the values."""
        return tuple(self.values)


class LoadProfile(SeriesProfile):
    """Power demand of a fixed load, in MW per timestep: the demand that must be met."""

    entity_types: ClassVar[tuple[type[EnergyEntity], ...]] = (FixedLoad,)
    required: ClassVar[bool] = True

    load: FixedLoad

    @property
    def entity(self) -> FixedLoad:
        """Return the load this demand belongs to."""
        return self.load


class FlexibleLoadProfile(Profile):
    """The range a flexible load may consume in, in MW per timestep.

    At every step the optimizer chooses the load's consumption between
    `lower_bound` and `upper_bound`. Both bounds are at least 0, the lower
    one is at most the upper one, and they lie within the load's `min_load`
    and `max_load` when those are set.
    """

    entity_types: ClassVar[tuple[type[EnergyEntity], ...]] = (FlexibleLoad,)
    required: ClassVar[bool] = True

    load: FlexibleLoad
    lower_bound: Sequence[float] = Field(
        min_length=1,
        description="Least the load consumes at each timestep, in MW. Stored as a tuple.",
    )
    upper_bound: Sequence[float] = Field(
        min_length=1,
        description="Most the load consumes at each timestep, in MW. Stored as a tuple.",
    )

    @field_validator("lower_bound", "upper_bound", mode="after")
    @staticmethod
    def _store_bounds_as_tuples(bound: Sequence[float]) -> tuple[float, ...]:
        return tuple(bound)

    @model_validator(mode="after")
    def _validate_bounds_have_the_same_length(self) -> Self:
        if len(self.lower_bound) != len(self.upper_bound):
            msg = (
                f"Flexible load '{self.load.name}' has {len(self.lower_bound)} lower bound values "
                f"and {len(self.upper_bound)} upper bound values."
            )
            raise OdysValidationError(msg)
        return self

    @model_validator(mode="after")
    def _validate_bounds_form_a_range(self) -> Self:
        for t, (lower_t, upper_t) in enumerate(zip(self.lower_bound, self.upper_bound, strict=True)):
            if lower_t < 0:
                msg = f"Flexible load '{self.load.name}' has a negative lower bound ({lower_t}) at time index {t}."
                raise OdysValidationError(msg)
            if lower_t > upper_t:
                msg = (
                    f"Flexible load '{self.load.name}' has a lower bound ({lower_t}) "
                    f"above its upper bound ({upper_t}) at time index {t}."
                )
                raise OdysValidationError(msg)
        return self

    @model_validator(mode="after")
    def _validate_bounds_within_load_limits(self) -> Self:
        min_load, max_load = self.load.min_load, self.load.max_load
        for t, (lower_t, upper_t) in enumerate(zip(self.lower_bound, self.upper_bound, strict=True)):
            if min_load is not None and lower_t < min_load:
                msg = (
                    f"Flexible load '{self.load.name}' has a lower bound ({lower_t}) "
                    f"below min_load ({min_load}) at time index {t}."
                )
                raise OdysValidationError(msg)
            if max_load is not None and upper_t > max_load:
                msg = (
                    f"Flexible load '{self.load.name}' has an upper bound ({upper_t}) "
                    f"above max_load ({max_load}) at time index {t}."
                )
                raise OdysValidationError(msg)
        return self

    @property
    def entity(self) -> FlexibleLoad:
        """Return the load this range belongs to."""
        return self.load

    @property
    def number_of_steps(self) -> int:
        """Return the number of values in each bound."""
        return len(self.lower_bound)

    @property
    def operating_values(self) -> tuple[float, ...]:
        """Return the lower bound: the least the load must consume at each timestep."""
        return tuple(self.lower_bound)


class AvailableCapacityProfile(SeriesProfile):
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


class PriceProfile(SeriesProfile):
    """Energy price of a market, in currency per MWh per timestep."""

    entity_types: ClassVar[tuple[type[EnergyEntity], ...]] = (EnergyMarket,)
    required: ClassVar[bool] = True

    market: EnergyMarket

    @property
    def entity(self) -> EnergyMarket:
        """Return the market this price belongs to."""
        return self.market


AnyProfile = LoadProfile | FlexibleLoadProfile | AvailableCapacityProfile | PriceProfile
PROFILE_TYPES: tuple[type[Profile], ...] = (LoadProfile, FlexibleLoadProfile, AvailableCapacityProfile, PriceProfile)
