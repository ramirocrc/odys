"""Unit tests for the initial and final conditions of a run."""

from datetime import timedelta

import pytest
from pydantic import ValidationError

from odys.domain.conditions import (
    ConditionSet,
    ElectricVehicleFinalState,
    ElectricVehicleInitialState,
    GeneratorFinalState,
    GeneratorInitialState,
    StorageFinalState,
    StorageInitialState,
)
from odys.domain.entities.battery import Battery
from odys.domain.entities.battery_storage import BatteryStorage
from odys.domain.entities.commitment import Commitment
from odys.domain.entities.electric_vehicle import ElectricVehicle
from odys.domain.entities.generator import Generator
from odys.domain.entities.trip import Trip
from odys.domain.exceptions import OdysValidationError

NOMINAL_POWER = 100.0
MIN_POWER = 20.0
VARIABLE_COST = 10.0
POWER_WITHIN_LIMITS = 50.0
POWER_BELOW_MIN_POWER = 10.0
POWER_ABOVE_NOMINAL_POWER = 120.0
MIN_TIME = timedelta(hours=3)
TIME_IN_STATE = timedelta(hours=1)

CAPACITY = 75.0
SOC_MIN = 0.1
SOC_MAX = 0.9
SOC_WITHIN_LIMITS = 0.8
SOC_BELOW_MIN = 0.05
SOC_ABOVE_MAX = 0.95
TRIP_BEYOND_STARTING_CHARGE = 70.0
TRIP_WITHIN_STARTING_CHARGE = 52.0

PLAIN_GENERATOR = Generator(name="plain", nominal_power=NOMINAL_POWER, variable_cost=VARIABLE_COST)
GENERATOR = Generator(name="gen", nominal_power=NOMINAL_POWER, variable_cost=VARIABLE_COST, min_power=MIN_POWER)
BATTERY = Battery(capacity=CAPACITY, max_charge_power=22.0, max_discharge_power=11.0, soc_min=SOC_MIN, soc_max=SOC_MAX)
STORAGE = BatteryStorage(name="bess", battery=BATTERY)
VEHICLE = ElectricVehicle(name="ev", battery=BATTERY, trips=())


SocState = StorageInitialState | StorageFinalState | ElectricVehicleInitialState | ElectricVehicleFinalState


def _vehicle_with_trip(trip: Trip) -> ElectricVehicle:
    return VEHICLE.model_copy(update={"trips": (trip,)})


@pytest.mark.parametrize("power", [0.0, MIN_POWER, POWER_WITHIN_LIMITS, NOMINAL_POWER])
@pytest.mark.parametrize("condition_type", [GeneratorInitialState, GeneratorFinalState])
def test_generator_state_accepts_off_or_power_within_limits(
    condition_type: type[GeneratorInitialState | GeneratorFinalState],
    power: float,
) -> None:
    state = condition_type(generator=GENERATOR, power=power)

    assert state.power == pytest.approx(power)


@pytest.mark.parametrize(
    "power",
    [POWER_BELOW_MIN_POWER, POWER_ABOVE_NOMINAL_POWER],
    ids=["between_off_and_min_power", "above_nominal_power"],
)
@pytest.mark.parametrize("condition_type", [GeneratorInitialState, GeneratorFinalState])
def test_generator_state_rejects_power_outside_limits(
    condition_type: type[GeneratorInitialState | GeneratorFinalState],
    power: float,
) -> None:
    with pytest.raises(
        OdysValidationError,
        match=rf"{condition_type.__name__} for generator 'gen' has power={power}, but a generator is either off",
    ):
        condition_type(generator=GENERATOR, power=power)


@pytest.mark.parametrize("condition_type", [GeneratorInitialState, GeneratorFinalState])
def test_generator_state_rejects_negative_power(
    condition_type: type[GeneratorInitialState | GeneratorFinalState],
) -> None:
    with pytest.raises(ValidationError, match="Input should be greater than or equal to 0"):
        condition_type(generator=GENERATOR, power=-1.0)


@pytest.mark.parametrize(("power", "is_on"), [(0.0, False), (POWER_WITHIN_LIMITS, True)], ids=["off", "on"])
def test_generator_initial_state_is_on_when_power_is_above_zero(power: float, *, is_on: bool) -> None:
    assert GeneratorInitialState(generator=GENERATOR, power=power).is_on is is_on


@pytest.mark.parametrize(
    ("min_time_field", "power", "state"),
    [("min_up_time", POWER_WITHIN_LIMITS, "on"), ("min_down_time", 0.0, "off")],
    ids=["on_with_min_up_time", "off_with_min_down_time"],
)
def test_generator_initial_state_requires_time_in_state_with_the_matching_min_time(
    min_time_field: str,
    power: float,
    state: str,
) -> None:
    generator = GENERATOR.model_copy(update={"commitment": Commitment.model_validate({min_time_field: MIN_TIME})})

    with pytest.raises(
        OdysValidationError,
        match=rf"starts {state} and the generator has {min_time_field} set, so time_in_state is required",
    ):
        GeneratorInitialState(generator=generator, power=power)


@pytest.mark.parametrize(
    ("min_time_field", "power"),
    [("min_down_time", POWER_WITHIN_LIMITS), ("min_up_time", 0.0)],
    ids=["on_with_min_down_time", "off_with_min_up_time"],
)
def test_generator_initial_state_does_not_require_time_in_state_for_the_other_min_time(
    min_time_field: str,
    power: float,
) -> None:
    generator = GENERATOR.model_copy(update={"commitment": Commitment.model_validate({min_time_field: MIN_TIME})})

    assert GeneratorInitialState(generator=generator, power=power).time_in_state is None


def test_generator_initial_state_accepts_time_in_state() -> None:
    generator = GENERATOR.model_copy(update={"commitment": Commitment(min_up_time=MIN_TIME)})

    state = GeneratorInitialState(generator=generator, power=POWER_WITHIN_LIMITS, time_in_state=TIME_IN_STATE)

    assert state.time_in_state == TIME_IN_STATE


def test_generator_initial_state_rejects_non_positive_time_in_state() -> None:
    with pytest.raises(ValidationError, match="Input should be greater than 0"):
        GeneratorInitialState(generator=GENERATOR, power=0.0, time_in_state=timedelta(0))


def test_generator_initial_state_is_optional_for_a_generator_without_time_coupling() -> None:
    assert GeneratorInitialState.required_for(PLAIN_GENERATOR) is None


@pytest.mark.parametrize(
    ("field", "update"),
    [
        ("ramp_up", {"ramp_up": 10.0}),
        ("ramp_down", {"ramp_down": 0.0}),
        ("min_up_time", {"commitment": Commitment(min_up_time=MIN_TIME)}),
        ("min_down_time", {"commitment": Commitment(min_down_time=MIN_TIME)}),
        ("startup_cost", {"commitment": Commitment(startup_cost=5.0)}),
        ("shutdown_cost", {"commitment": Commitment(shutdown_cost=5.0)}),
    ],
    ids=["ramp_up", "ramp_down", "min_up_time", "min_down_time", "startup_cost", "shutdown_cost"],
)
def test_generator_initial_state_is_required_for_a_time_coupled_generator(
    field: str,
    update: dict[str, object],
) -> None:
    generator = PLAIN_GENERATOR.model_copy(update=update)

    assert GeneratorInitialState.required_for(generator) == f"it has {field} set"


def test_generator_initial_state_required_reason_lists_every_time_coupling_field() -> None:
    generator = PLAIN_GENERATOR.model_copy(update={"ramp_up": 10.0, "commitment": Commitment(startup_cost=5.0)})

    assert GeneratorInitialState.required_for(generator) == "it has ramp_up, startup_cost set"


@pytest.mark.parametrize(
    ("condition_type", "asset"),
    [
        (GeneratorInitialState, STORAGE),
        (StorageInitialState, GENERATOR),
        (ElectricVehicleInitialState, STORAGE),
    ],
    ids=["generator_state_for_storage", "storage_state_for_generator", "ev_state_for_storage"],
)
def test_initial_state_is_not_required_for_another_asset_type(
    condition_type: type[GeneratorInitialState | StorageInitialState | ElectricVehicleInitialState],
    asset: Generator | BatteryStorage,
) -> None:
    assert condition_type.required_for(asset) is None


@pytest.mark.parametrize(
    ("condition_type", "asset"),
    [(StorageInitialState, STORAGE), (ElectricVehicleInitialState, VEHICLE)],
    ids=["storage", "ev"],
)
def test_initial_state_of_charge_is_always_required(
    condition_type: type[StorageInitialState | ElectricVehicleInitialState],
    asset: BatteryStorage | ElectricVehicle,
) -> None:
    assert condition_type.required_for(asset) == "its state of charge carries over from one timestep to the next"


def _soc_state(
    condition_type: type[
        StorageInitialState | StorageFinalState | ElectricVehicleInitialState | ElectricVehicleFinalState
    ],
    soc: float,
) -> SocState:
    if condition_type in {StorageInitialState, StorageFinalState}:
        return condition_type.model_validate({"storage": STORAGE, "soc": soc})
    return condition_type.model_validate({"vehicle": VEHICLE, "soc": soc})


SOC_STATE_TYPES = [StorageInitialState, StorageFinalState, ElectricVehicleInitialState, ElectricVehicleFinalState]


@pytest.mark.parametrize("condition_type", SOC_STATE_TYPES)
def test_soc_state_accepts_soc_within_battery_limits(
    condition_type: type[
        StorageInitialState | StorageFinalState | ElectricVehicleInitialState | ElectricVehicleFinalState
    ],
) -> None:
    assert _soc_state(condition_type, SOC_WITHIN_LIMITS).soc == pytest.approx(SOC_WITHIN_LIMITS)


@pytest.mark.parametrize("soc", [SOC_BELOW_MIN, SOC_ABOVE_MAX], ids=["below_soc_min", "above_soc_max"])
@pytest.mark.parametrize("condition_type", SOC_STATE_TYPES)
def test_soc_state_rejects_soc_outside_battery_limits(
    condition_type: type[
        StorageInitialState | StorageFinalState | ElectricVehicleInitialState | ElectricVehicleFinalState
    ],
    soc: float,
) -> None:
    with pytest.raises(
        OdysValidationError,
        match=rf"{condition_type.__name__} for '\w+' has soc={soc}, outside the battery's limits "
        rf"\[soc_min={SOC_MIN}, soc_max={SOC_MAX}\]",
    ):
        _soc_state(condition_type, soc)


@pytest.mark.parametrize("soc", [-0.1, 1.1], ids=["negative", "above_one"])
@pytest.mark.parametrize("condition_type", SOC_STATE_TYPES)
def test_soc_state_rejects_soc_outside_zero_to_one(
    condition_type: type[
        StorageInitialState | StorageFinalState | ElectricVehicleInitialState | ElectricVehicleFinalState
    ],
    soc: float,
) -> None:
    with pytest.raises(ValidationError, match="Input should be"):
        _soc_state(condition_type, soc)


def test_ev_initial_state_rejects_departure_soc_above_initial_soc_at_t0() -> None:
    trip = Trip(
        name="early",
        start_time=timedelta(hours=0),
        end_time=timedelta(hours=2),
        energy_consumption=5.0,
        min_soc_at_departure=SOC_MAX,
    )

    with pytest.raises(
        OdysValidationError,
        match=r"Trip 'early' for vehicle 'ev' departs at t=0 with min_soc_at_departure=0.9 > initial soc=0.8",
    ):
        ElectricVehicleInitialState(vehicle=_vehicle_with_trip(trip), soc=SOC_WITHIN_LIMITS)


def test_ev_initial_state_accepts_departure_soc_up_to_initial_soc_at_t0() -> None:
    trip = Trip(
        name="early",
        start_time=timedelta(hours=0),
        end_time=timedelta(hours=2),
        energy_consumption=5.0,
        min_soc_at_departure=SOC_WITHIN_LIMITS,
    )

    state = ElectricVehicleInitialState(vehicle=_vehicle_with_trip(trip), soc=SOC_WITHIN_LIMITS)

    assert state.vehicle.trips == (trip,)


def test_ev_initial_state_accepts_high_departure_soc_after_t0() -> None:
    trip = Trip(
        name="later",
        start_time=timedelta(hours=1),
        end_time=timedelta(hours=3),
        energy_consumption=5.0,
        min_soc_at_departure=SOC_MAX,
    )

    state = ElectricVehicleInitialState(vehicle=_vehicle_with_trip(trip), soc=SOC_WITHIN_LIMITS)

    assert state.vehicle.trips == (trip,)


def test_ev_initial_state_rejects_trip_at_t0_needing_more_than_the_starting_charge() -> None:
    trip = Trip(
        name="early",
        start_time=timedelta(hours=0),
        end_time=timedelta(hours=2),
        energy_consumption=TRIP_BEYOND_STARTING_CHARGE,
    )

    with pytest.raises(
        OdysValidationError,
        match=r"Trip 'early' for vehicle 'ev' departs at t=0 and consumes 70 MWh, "
        r"but the battery holds only 52.5 MWh above soc_min at the start",
    ):
        ElectricVehicleInitialState(vehicle=_vehicle_with_trip(trip), soc=SOC_WITHIN_LIMITS)


def test_ev_initial_state_accepts_trip_at_t0_within_the_starting_charge() -> None:
    trip = Trip(
        name="early",
        start_time=timedelta(hours=0),
        end_time=timedelta(hours=2),
        energy_consumption=TRIP_WITHIN_STARTING_CHARGE,
    )

    state = ElectricVehicleInitialState(vehicle=_vehicle_with_trip(trip), soc=SOC_WITHIN_LIMITS)

    assert state.vehicle.trips == (trip,)


def test_ev_initial_state_accepts_a_long_trip_after_t0() -> None:
    """A vehicle can charge before a later trip, so the starting charge does not bound it."""
    trip = Trip(
        name="later",
        start_time=timedelta(hours=1),
        end_time=timedelta(hours=3),
        energy_consumption=TRIP_BEYOND_STARTING_CHARGE,
    )

    state = ElectricVehicleInitialState(vehicle=_vehicle_with_trip(trip), soc=SOC_WITHIN_LIMITS)

    assert state.vehicle.trips == (trip,)


@pytest.mark.parametrize(
    ("condition", "entity"),
    [
        (GeneratorInitialState(generator=GENERATOR, power=0.0), GENERATOR),
        (GeneratorFinalState(generator=GENERATOR, power=0.0), GENERATOR),
        (StorageInitialState(storage=STORAGE, soc=SOC_WITHIN_LIMITS), STORAGE),
        (StorageFinalState(storage=STORAGE, soc=SOC_WITHIN_LIMITS), STORAGE),
        (ElectricVehicleInitialState(vehicle=VEHICLE, soc=SOC_WITHIN_LIMITS), VEHICLE),
        (ElectricVehicleFinalState(vehicle=VEHICLE, soc=SOC_WITHIN_LIMITS), VEHICLE),
    ],
    ids=lambda value: type(value).__name__,
)
def test_condition_entity_is_its_asset(
    condition: GeneratorInitialState | GeneratorFinalState | StorageInitialState,
    entity: Generator | BatteryStorage | ElectricVehicle,
) -> None:
    assert condition.entity == entity


def test_condition_set_rejects_two_conditions_of_one_type_for_an_asset() -> None:
    with pytest.raises(OdysValidationError, match=r"There is more than one condition: GeneratorInitialState for 'gen'"):
        ConditionSet(
            initial=(
                GeneratorInitialState(generator=GENERATOR, power=0.0),
                GeneratorInitialState(generator=GENERATOR, power=POWER_WITHIN_LIMITS),
            ),
        )


def test_condition_set_accepts_an_initial_and_a_final_condition_for_an_asset() -> None:
    initial = GeneratorInitialState(generator=GENERATOR, power=0.0)
    final = GeneratorFinalState(generator=GENERATOR, power=POWER_WITHIN_LIMITS)

    condition_set = ConditionSet(initial=(initial,), final=(final,))

    assert condition_set.conditions == (initial, final)


def test_condition_set_rejects_a_final_condition_as_an_initial_one() -> None:
    with pytest.raises(
        ValidationError,
        match="Input should be a valid dictionary or instance of GeneratorInitialState",
    ):
        ConditionSet.model_validate({"initial": (GeneratorFinalState(generator=GENERATOR, power=0.0),)})


def test_condition_set_get_returns_the_asset_condition_of_that_type() -> None:
    initial = GeneratorInitialState(generator=GENERATOR, power=0.0)
    condition_set = ConditionSet(initial=(initial,), final=(StorageFinalState(storage=STORAGE, soc=SOC_MIN),))

    assert condition_set.get(GeneratorInitialState, GENERATOR) == initial
    assert condition_set.get(GeneratorFinalState, GENERATOR) is None
    assert condition_set.get(GeneratorInitialState, PLAIN_GENERATOR) is None


def test_generator_initial_state_rejects_a_number_as_time_in_state() -> None:
    """A bare number is not read as seconds: durations are always `timedelta`."""
    with pytest.raises(ValidationError, match="Input should be a valid timedelta"):
        GeneratorInitialState.model_validate({"generator": GENERATOR, "power": 0.0, "time_in_state": 3600})


def test_condition_set_rejects_two_final_conditions_of_one_type_for_an_asset() -> None:
    with pytest.raises(OdysValidationError, match=r"There is more than one condition: StorageFinalState for 'bess'"):
        ConditionSet(
            final=(
                StorageFinalState(storage=STORAGE, soc=SOC_MIN),
                StorageFinalState(storage=STORAGE, soc=SOC_WITHIN_LIMITS),
            ),
        )


def test_condition_set_get_ignores_a_different_asset_with_the_same_name() -> None:
    initial = GeneratorInitialState(generator=GENERATOR, power=0.0)
    copy_with_other_cost = GENERATOR.model_copy(update={"variable_cost": VARIABLE_COST + 1})

    assert ConditionSet(initial=(initial,)).get(GeneratorInitialState, copy_with_other_cost) is None
