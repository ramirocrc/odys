"""Unit tests for the ElectricVehicle entity."""

from datetime import timedelta
from types import MappingProxyType
from typing import Any

import pytest
from pydantic import ValidationError

from odys.domain.entities.base import Asset
from odys.domain.entities.battery import Battery
from odys.domain.entities.electric_vehicle import ElectricVehicle
from odys.domain.entities.trip import Trip
from odys.domain.exceptions import OdysValidationError
from odys.domain.horizon import Horizon

EV_CAPACITY = 75.0
EV_MAX_CHARGE_POWER = 22.0
EV_MAX_DISCHARGE_POWER = 11.0
EV_SOC_START = 0.8
NUM_TRIPS = 2
NUM_STEPS = 24
TRIP_BEYOND_STARTING_CHARGE = 70.0
TRIP_WITHIN_STARTING_CHARGE = 59.0
RAISED_SOC_MIN = 0.2

EV_BATTERY_PARAMS = MappingProxyType({
    "capacity": EV_CAPACITY,
    "max_charge_power": EV_MAX_CHARGE_POWER,
    "max_discharge_power": EV_MAX_DISCHARGE_POWER,
    "soc_start": EV_SOC_START,
})


@pytest.fixture
def ev_base_params() -> MappingProxyType[str, Any]:
    return MappingProxyType({
        "name": "ev_1",
        "battery": Battery(**EV_BATTERY_PARAMS),
        "trips": (),
    })


def test_ev_creation_with_valid_parameters(ev_base_params: MappingProxyType[str, Any]) -> None:
    ev = ElectricVehicle(**dict(ev_base_params))
    assert ev.name == "ev_1"
    assert ev.battery.capacity == EV_CAPACITY
    assert ev.battery.max_charge_power == EV_MAX_CHARGE_POWER
    assert ev.battery.max_discharge_power == EV_MAX_DISCHARGE_POWER
    assert ev.battery.soc_start == EV_SOC_START
    assert ev.trips == ()


def test_ev_is_an_asset_that_has_a_battery(ev_base_params: MappingProxyType[str, Any]) -> None:
    ev = ElectricVehicle(**dict(ev_base_params))
    assert isinstance(ev, Asset)
    assert isinstance(ev.battery, Battery)


def test_ev_creation_with_trips(ev_base_params: MappingProxyType[str, Any]) -> None:
    trip1 = Trip(name="morning", start_time=8, end_time=9, energy_consumption=5.0)
    trip2 = Trip(name="evening", start_time=17, end_time=18, energy_consumption=5.0, min_soc_at_departure=0.3)
    params = dict(ev_base_params)
    params["trips"] = (trip1, trip2)
    ev = ElectricVehicle(**params)
    assert len(ev.trips) == NUM_TRIPS
    assert ev.trips[0].name == "morning"
    assert ev.trips[1].name == "evening"


def test_ev_charge_only(ev_base_params: MappingProxyType[str, Any]) -> None:
    base_params = dict(ev_base_params)
    base_params["battery"] = Battery(**(dict(EV_BATTERY_PARAMS) | {"max_discharge_power": 0.0}))
    ev = ElectricVehicle(**base_params)
    assert ev.battery.max_discharge_power == 0.0


def test_ev_validates_its_battery(ev_base_params: MappingProxyType[str, Any]) -> None:
    base_params = dict(ev_base_params)
    base_params["battery"] = dict(EV_BATTERY_PARAMS) | {"capacity": 0.0}
    with pytest.raises(ValidationError, match="Input should be greater than 0"):
        ElectricVehicle.model_validate(base_params)


def test_ev_soc_validation(ev_base_params: MappingProxyType[str, Any]) -> None:
    base_params = dict(ev_base_params)
    base_params["battery"] = dict(EV_BATTERY_PARAMS) | {"soc_start": 0.2, "soc_min": 0.3}
    with pytest.raises(OdysValidationError, match="soc_start"):
        ElectricVehicle.model_validate(base_params)


def test_ev_accepts_non_overlapping_trips(ev_base_params: MappingProxyType[str, Any]) -> None:
    trip1 = Trip(name="morning", start_time=8, end_time=10, energy_consumption=5.0)
    trip2 = Trip(name="evening", start_time=17, end_time=19, energy_consumption=5.0)
    params = dict(ev_base_params)
    params["trips"] = (trip1, trip2)
    ev = ElectricVehicle(**params)
    assert ev.trips == (trip1, trip2)


def test_ev_rejects_overlapping_trips_at_construction(ev_base_params: MappingProxyType[str, Any]) -> None:
    trip1 = Trip(name="morning", start_time=8, end_time=10, energy_consumption=5.0)
    trip2 = Trip(name="overlapping", start_time=9, end_time=11, energy_consumption=5.0)
    params = dict(ev_base_params)
    params["trips"] = (trip2, trip1)
    with pytest.raises(OdysValidationError, match="Trips 'morning' and 'overlapping' overlap for vehicle 'ev_1'"):
        ElectricVehicle(**params)


def test_ev_accepts_back_to_back_trips(ev_base_params: MappingProxyType[str, Any]) -> None:
    trip1 = Trip(name="out", start_time=8, end_time=10, energy_consumption=5.0)
    trip2 = Trip(name="back", start_time=10, end_time=12, energy_consumption=5.0)
    params = dict(ev_base_params)
    params["trips"] = (trip1, trip2)
    assert ElectricVehicle(**params).trips == (trip1, trip2)


def test_ev_rejects_departure_soc_above_soc_start_at_t0(ev_base_params: MappingProxyType[str, Any]) -> None:
    trip = Trip(name="early", start_time=0, end_time=2, energy_consumption=5.0, min_soc_at_departure=0.9)
    params = dict(ev_base_params)
    params["trips"] = (trip,)
    with pytest.raises(OdysValidationError, match=r"departs at t=0 with min_soc_at_departure=0.9 > soc_start=0.8"):
        ElectricVehicle(**params)


def test_ev_accepts_departure_soc_up_to_soc_start_at_t0(ev_base_params: MappingProxyType[str, Any]) -> None:
    trip = Trip(name="early", start_time=0, end_time=2, energy_consumption=5.0, min_soc_at_departure=EV_SOC_START)
    params = dict(ev_base_params)
    params["trips"] = (trip,)
    assert ElectricVehicle(**params).trips == (trip,)


def test_ev_accepts_high_departure_soc_after_t0(ev_base_params: MappingProxyType[str, Any]) -> None:
    trip = Trip(name="later", start_time=1, end_time=3, energy_consumption=5.0, min_soc_at_departure=0.9)
    params = dict(ev_base_params)
    params["trips"] = (trip,)
    assert ElectricVehicle(**params).trips == (trip,)


def test_ev_rejects_trip_at_t0_needing_more_than_the_starting_charge(
    ev_base_params: MappingProxyType[str, Any],
) -> None:
    trip = Trip(name="early", start_time=0, end_time=2, energy_consumption=TRIP_BEYOND_STARTING_CHARGE)
    params = dict(ev_base_params)
    params["trips"] = (trip,)
    with pytest.raises(
        OdysValidationError,
        match=r"Trip 'early' for vehicle 'ev_1' departs at t=0 and consumes 70 MWh, "
        r"but the battery holds only 60 MWh above soc_min at the start",
    ):
        ElectricVehicle(**params)


def test_ev_accepts_trip_at_t0_within_the_starting_charge(ev_base_params: MappingProxyType[str, Any]) -> None:
    trip = Trip(name="early", start_time=0, end_time=2, energy_consumption=TRIP_WITHIN_STARTING_CHARGE)
    params = dict(ev_base_params)
    params["trips"] = (trip,)
    assert ElectricVehicle(**params).trips == (trip,)


def test_ev_starting_charge_for_a_trip_at_t0_excludes_the_soc_min_reserve(
    ev_base_params: MappingProxyType[str, Any],
) -> None:
    trip = Trip(name="early", start_time=0, end_time=2, energy_consumption=TRIP_WITHIN_STARTING_CHARGE)
    params = dict(ev_base_params)
    params["battery"] = Battery(**EV_BATTERY_PARAMS, soc_min=RAISED_SOC_MIN)
    params["trips"] = (trip,)
    with pytest.raises(OdysValidationError, match=r"holds only 45 MWh above soc_min"):
        ElectricVehicle(**params)


def test_ev_accepts_a_long_trip_after_t0(ev_base_params: MappingProxyType[str, Any]) -> None:
    """A vehicle can charge before a later trip, so the starting charge does not bound it."""
    trip = Trip(name="later", start_time=1, end_time=3, energy_consumption=TRIP_BEYOND_STARTING_CHARGE)
    params = dict(ev_base_params)
    params["trips"] = (trip,)
    assert ElectricVehicle(**params).trips == (trip,)


def test_ev_validate_horizon_accepts_trips_within_horizon(ev_base_params: MappingProxyType[str, Any]) -> None:
    trip = Trip(name="last", start_time=20, end_time=NUM_STEPS, energy_consumption=5.0)
    params = dict(ev_base_params)
    params["trips"] = (trip,)
    ElectricVehicle(**params).validate_horizon(Horizon(timestep=timedelta(hours=1), number_of_steps=NUM_STEPS))


def test_ev_validate_horizon_rejects_trips_beyond_horizon(ev_base_params: MappingProxyType[str, Any]) -> None:
    trip = Trip(name="late_trip", start_time=20, end_time=30, energy_consumption=5.0)
    params = dict(ev_base_params)
    params["trips"] = (trip,)
    ev = ElectricVehicle(**params)
    with pytest.raises(OdysValidationError, match=r"Trip 'late_trip' for vehicle 'ev_1' extends beyond.*horizon=24"):
        ev.validate_horizon(Horizon(timestep=timedelta(hours=1), number_of_steps=NUM_STEPS))
