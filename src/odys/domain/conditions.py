"""Initial and final conditions of one optimization run.

An initial condition is the state of an asset just before the first timestep,
such as the output of a generator or the state of charge of a battery. A final
condition is a state the asset must reach at the last timestep. Conditions
belong to one run, not to the asset or to a scenario: they are the same in
every scenario and are passed to `EnergySystem`.

Each condition type references the kind of asset it belongs to, so it cannot
be attached to the wrong kind of asset. An initial condition is required
whenever the asset's results depend on it (`required_for`), so odys never
guesses a starting state.
"""

import math
from abc import ABC, abstractmethod
from collections import Counter
from datetime import timedelta
from functools import cached_property
from typing import ClassVar, Self, TypeVar

from pydantic import BaseModel, ConfigDict, Field, model_validator

from odys.domain.entities.base import Asset
from odys.domain.entities.battery import Battery
from odys.domain.entities.battery_storage import BatteryStorage
from odys.domain.entities.commitment import Commitment
from odys.domain.entities.electric_vehicle import ElectricVehicle
from odys.domain.entities.generator import Generator
from odys.domain.exceptions import OdysValidationError
from odys.domain.horizon import Horizon, OperatingConditions

ConditionT = TypeVar("ConditionT", bound="Condition")


class Condition(BaseModel, ABC):
    """A state of one asset at the boundary of the optimization horizon.

    Each condition type declares the asset types it applies to. Like entities,
    a condition is checked against the run through `validate_horizon` and
    `validate_operating_conditions`, which accept anything by default.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    entity_types: ClassVar[tuple[type[Asset], ...]]

    @property
    @abstractmethod
    def entity(self) -> Asset:
        """Return the asset this condition belongs to."""

    def validate_horizon(self, horizon: Horizon) -> None:
        """Check that this condition fits the optimization horizon. The default accepts any horizon.

        Args:
            horizon: The time grid of the optimization.

        Raises:
            OdysValidationError: If the condition does not fit the horizon.
        """

    def validate_operating_conditions(self, conditions: OperatingConditions) -> None:
        """Check that this condition fits what its asset faces in one scenario. The default accepts anything.

        Args:
            conditions: The horizon and the asset's profile values in one scenario.

        Raises:
            OdysValidationError: If the condition cannot be met in that scenario.
        """


class InitialCondition(Condition, ABC):
    """The state of an asset just before the first timestep."""

    @classmethod
    @abstractmethod
    def required_for(cls, entity: Asset) -> str | None:
        """Return why the asset needs this initial condition, or None if it is optional.

        Args:
            entity: An asset of one of this condition's `entity_types`.

        Returns:
            The reason, completing "needs a <condition> because ...", or None.
        """


class FinalCondition(Condition, ABC):
    """The state an asset must reach at the last timestep."""


def _validate_generator_power(generator: Generator, power: float, condition: str) -> None:
    if power == 0 or generator.min_power <= power <= generator.nominal_power:
        return
    msg = (
        f"{condition} for generator '{generator.name}' has power={power}, but a generator is either off (0) "
        f"or between min_power ({generator.min_power}) and nominal_power ({generator.nominal_power})."
    )
    raise OdysValidationError(msg)


def _validate_time_in_state_given_with_min_time(
    commitment: Commitment,
    *,
    is_on: bool,
    time_in_state: timedelta | None,
    subject: str,
    entity_kind: str,
) -> None:
    min_time = commitment.min_up_time if is_on else commitment.min_down_time
    if time_in_state is None and min_time is not None:
        min_time_field = "min_up_time" if is_on else "min_down_time"
        state = "on" if is_on else "off"
        msg = f"{subject} starts {state} and the {entity_kind} has {min_time_field} set, so time_in_state is required."
        raise OdysValidationError(msg)


def _time_coupling_reason(ramp_up: float | None, ramp_down: float | None, commitment: Commitment | None) -> str | None:
    ramps = {"ramp_up": ramp_up is not None, "ramp_down": ramp_down is not None}
    set_fields = [field for field, is_set in ramps.items() if is_set]
    if commitment is not None:
        set_fields.extend(commitment.time_coupled_fields())
    if not set_fields:
        return None
    return f"it has {', '.join(set_fields)} set"


def _validate_soc_within_battery_limits(battery: Battery, soc: float, condition: str, asset_name: str) -> None:
    if battery.soc_min <= soc <= battery.soc_max:
        return
    msg = (
        f"{condition} for '{asset_name}' has soc={soc}, "
        f"outside the battery's limits [soc_min={battery.soc_min}, soc_max={battery.soc_max}]."
    )
    raise OdysValidationError(msg)


class GeneratorInitialState(InitialCondition):
    """Output of a generator just before the first timestep, and how long it has been on or off.

    The generator is on if `power` is above 0 and off if it is 0. `time_in_state`
    is how long it has been in that state; it carries the minimum up or down
    time over from before the horizon, and is required when the matching
    minimum time is set.
    """

    entity_types: ClassVar[tuple[type[Asset], ...]] = (Generator,)

    generator: Generator
    power: float = Field(strict=True, ge=0, description="Output just before the first timestep, in MW.")
    time_in_state: timedelta | None = Field(
        default=None,
        strict=True,
        gt=timedelta(0),
        description="How long the generator has been on (power > 0) or off (power = 0).",
    )

    @model_validator(mode="after")
    def _validate_power(self) -> Self:
        _validate_generator_power(self.generator, self.power, type(self).__name__)
        return self

    @model_validator(mode="after")
    def _validate_time_in_state_given_with_min_time(self) -> Self:
        _validate_time_in_state_given_with_min_time(
            self.generator.commitment,
            is_on=self.is_on,
            time_in_state=self.time_in_state,
            subject=f"{type(self).__name__} for generator '{self.generator.name}'",
            entity_kind="generator",
        )
        return self

    def validate_horizon(self, horizon: Horizon) -> None:
        """Check that the time in state spans a whole number of timesteps.

        Args:
            horizon: The time grid of the optimization.

        Raises:
            OdysValidationError: If the time in state is not a whole number of timesteps.
        """
        if self.time_in_state is not None and not horizon.is_whole_steps(self.time_in_state):
            msg = (
                f"GeneratorInitialState for generator '{self.generator.name}' has "
                f"time_in_state={self.time_in_state}, which is not a whole number of timesteps "
                f"({horizon.timestep})."
            )
            raise OdysValidationError(msg)

    @classmethod
    def required_for(cls, entity: Asset) -> str | None:
        """Return why a generator needs an initial state: a parameter linking one timestep to the next is set."""
        if not isinstance(entity, Generator):
            return None
        return _time_coupling_reason(entity.ramp_up, entity.ramp_down, entity.commitment)

    @property
    def is_on(self) -> bool:
        """Return whether the generator is on just before the first timestep."""
        return self.power > 0

    @property
    def entity(self) -> Generator:
        """Return the generator this state belongs to."""
        return self.generator


class GeneratorFinalState(FinalCondition):
    """Output a generator must have at the last timestep. A power of 0 means it is off."""

    entity_types: ClassVar[tuple[type[Asset], ...]] = (Generator,)

    generator: Generator
    power: float = Field(strict=True, ge=0, description="Output at the last timestep, in MW.")

    @model_validator(mode="after")
    def _validate_power(self) -> Self:
        _validate_generator_power(self.generator, self.power, type(self).__name__)
        return self

    def validate_operating_conditions(self, conditions: OperatingConditions) -> None:
        """Check that the final power fits the generator's available capacity at the last timestep.

        Args:
            conditions: The horizon and the generator's available capacity in one scenario.

        Raises:
            OdysValidationError: If the final power exceeds the available capacity at the last timestep.
        """
        last_capacity = self.generator.max_supply(conditions)[-1]
        if self.power > last_capacity:
            msg = (
                f"GeneratorFinalState for generator '{self.generator.name}' has power={self.power}, "
                f"above its available capacity ({last_capacity}) at the last timestep."
            )
            raise OdysValidationError(msg)

    @property
    def entity(self) -> Generator:
        """Return the generator this state belongs to."""
        return self.generator


class StorageInitialState(InitialCondition):
    """State of charge of a battery storage just before the first timestep. Always required."""

    entity_types: ClassVar[tuple[type[Asset], ...]] = (BatteryStorage,)

    storage: BatteryStorage
    soc: float = Field(strict=True, ge=0, le=1, description="State of charge as a fraction of capacity (0-1).")

    @model_validator(mode="after")
    def _validate_soc(self) -> Self:
        _validate_soc_within_battery_limits(self.storage.battery, self.soc, type(self).__name__, self.storage.name)
        return self

    @classmethod
    def required_for(cls, entity: Asset) -> str | None:
        """Return why a battery storage needs an initial state: its charge carries over between timesteps."""
        if not isinstance(entity, BatteryStorage):
            return None
        return "its state of charge carries over from one timestep to the next"

    @property
    def entity(self) -> BatteryStorage:
        """Return the battery storage this state belongs to."""
        return self.storage


class StorageFinalState(FinalCondition):
    """State of charge a battery storage must have at the last timestep."""

    entity_types: ClassVar[tuple[type[Asset], ...]] = (BatteryStorage,)

    storage: BatteryStorage
    soc: float = Field(strict=True, ge=0, le=1, description="State of charge as a fraction of capacity (0-1).")

    @model_validator(mode="after")
    def _validate_soc(self) -> Self:
        _validate_soc_within_battery_limits(self.storage.battery, self.soc, type(self).__name__, self.storage.name)
        return self

    @property
    def entity(self) -> BatteryStorage:
        """Return the battery storage this state belongs to."""
        return self.storage


class ElectricVehicleInitialState(InitialCondition):
    """State of charge of an electric vehicle just before the first timestep. Always required.

    A trip departing at t=0 must not require more state of charge than `soc`,
    and its energy must fit in the starting charge above `soc_min`, since the
    vehicle cannot charge before or during it.
    """

    entity_types: ClassVar[tuple[type[Asset], ...]] = (ElectricVehicle,)

    vehicle: ElectricVehicle
    soc: float = Field(strict=True, ge=0, le=1, description="State of charge as a fraction of capacity (0-1).")

    @model_validator(mode="after")
    def _validate_soc(self) -> Self:
        _validate_soc_within_battery_limits(self.vehicle.battery, self.soc, type(self).__name__, self.vehicle.name)
        return self

    @model_validator(mode="after")
    def _validate_min_soc_at_departure_feasible(self) -> Self:
        for trip in self.vehicle.trips:
            if trip.start_time == timedelta(0) and trip.min_soc_at_departure > self.soc:
                msg = (
                    f"Trip '{trip.name}' for vehicle '{self.vehicle.name}' departs at t=0 with "
                    f"min_soc_at_departure={trip.min_soc_at_departure} > initial soc={self.soc}"
                )
                raise OdysValidationError(msg)
        return self

    @model_validator(mode="after")
    def _validate_starting_charge_covers_trip_at_t0(self) -> Self:
        battery = self.vehicle.battery
        available_energy = (self.soc - battery.soc_min) * battery.capacity
        for trip in self.vehicle.trips:
            if trip.start_time != timedelta(0):
                continue
            if trip.energy_consumption > available_energy and not math.isclose(
                trip.energy_consumption,
                available_energy,
            ):
                msg = (
                    f"Trip '{trip.name}' for vehicle '{self.vehicle.name}' departs at t=0 and consumes "
                    f"{trip.energy_consumption:.6g} MWh, but the battery holds only {available_energy:.6g} MWh "
                    f"above soc_min at the start (initial soc={self.soc}, soc_min={battery.soc_min}, "
                    f"capacity={battery.capacity} MWh); it cannot charge before or during the trip."
                )
                raise OdysValidationError(msg)
        return self

    @classmethod
    def required_for(cls, entity: Asset) -> str | None:
        """Return why an electric vehicle needs an initial state: its charge carries over between timesteps."""
        if not isinstance(entity, ElectricVehicle):
            return None
        return "its state of charge carries over from one timestep to the next"

    @property
    def entity(self) -> ElectricVehicle:
        """Return the electric vehicle this state belongs to."""
        return self.vehicle


class ElectricVehicleFinalState(FinalCondition):
    """State of charge an electric vehicle must have at the last timestep."""

    entity_types: ClassVar[tuple[type[Asset], ...]] = (ElectricVehicle,)

    vehicle: ElectricVehicle
    soc: float = Field(strict=True, ge=0, le=1, description="State of charge as a fraction of capacity (0-1).")

    @model_validator(mode="after")
    def _validate_soc(self) -> Self:
        _validate_soc_within_battery_limits(self.vehicle.battery, self.soc, type(self).__name__, self.vehicle.name)
        return self

    @property
    def entity(self) -> ElectricVehicle:
        """Return the electric vehicle this state belongs to."""
        return self.vehicle


AnyInitialCondition = GeneratorInitialState | StorageInitialState | ElectricVehicleInitialState
AnyFinalCondition = GeneratorFinalState | StorageFinalState | ElectricVehicleFinalState
INITIAL_CONDITION_TYPES: tuple[type[InitialCondition], ...] = (
    GeneratorInitialState,
    StorageInitialState,
    ElectricVehicleInitialState,
)


class ConditionSet(BaseModel):
    """The initial and final conditions of one optimization run.

    Owns the rule that spans conditions: each asset has at most one condition
    of each type.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    initial: tuple[AnyInitialCondition, ...] = ()
    final: tuple[AnyFinalCondition, ...] = ()

    @model_validator(mode="after")
    def _validate_one_condition_per_asset_and_type(self) -> Self:
        counts = Counter((type(condition).__name__, condition.entity.name) for condition in self.conditions)
        duplicates = sorted(f"{kind} for '{name}'" for (kind, name), count in counts.items() if count > 1)
        if duplicates:
            msg = f"There is more than one condition: {', '.join(duplicates)}."
            raise OdysValidationError(msg)
        return self

    @property
    def conditions(self) -> tuple[Condition, ...]:
        """Return every initial condition, then every final condition."""
        return (*self.initial, *self.final)

    def get(self, kind: type[ConditionT], entity: Asset) -> ConditionT | None:
        """Return the condition of the given type for the asset, if there is one.

        Args:
            kind: The condition type, such as `GeneratorInitialState`.
            entity: The asset to look up.

        Returns:
            The asset's condition of that type, or None.
        """
        condition = self._by_type_and_asset_name.get((kind, entity.name))
        if not isinstance(condition, kind) or condition.entity != entity:
            return None
        return condition

    @cached_property
    def _by_type_and_asset_name(self) -> dict[tuple[type[Condition], str], Condition]:
        return {(type(condition), condition.entity.name): condition for condition in self.conditions}
