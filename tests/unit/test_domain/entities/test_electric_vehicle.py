"""Unit tests for the ElectricVehicle entity."""

from types import MappingProxyType
from typing import Any

import pytest
from pydantic import ValidationError

from odys.domain.entities.electric_vehicle import ElectricVehicle
from odys.domain.entities.storage import Storage
from odys.domain.entities.trip import Trip
from odys.domain.exceptions import OdysValidationError

EV_CAPACITY = 75.0
EV_MAX_CHARGE_POWER = 22.0
EV_MAX_DISCHARGE_POWER = 11.0
EV_SOC_START = 0.8
NUM_TRIPS = 2
NUM_STEPS = 24


@pytest.fixture
def ev_base_params() -> MappingProxyType[str, Any]:
    return MappingProxyType({
        "name": "ev_1",
        "capacity": EV_CAPACITY,
        "max_charge_power": EV_MAX_CHARGE_POWER,
        "max_discharge_power": EV_MAX_DISCHARGE_POWER,
        "soc_start": EV_SOC_START,
        "trips": (),
    })


def test_ev_creation_with_valid_parameters(ev_base_params: MappingProxyType[str, Any]) -> None:
    ev = ElectricVehicle(**dict(ev_base_params))
    assert ev.name == "ev_1"
    assert ev.capacity == EV_CAPACITY
    assert ev.max_charge_power == EV_MAX_CHARGE_POWER
    assert ev.max_discharge_power == EV_MAX_DISCHARGE_POWER
    assert ev.soc_start == EV_SOC_START
    assert ev.trips == ()


def test_ev_is_storage(ev_base_params: MappingProxyType[str, Any]) -> None:
    ev = ElectricVehicle(**dict(ev_base_params))
    assert isinstance(ev, Storage)
    assert isinstance(ev, ElectricVehicle)


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
    base_params["max_discharge_power"] = 0.0
    ev = ElectricVehicle(**base_params)
    assert ev.max_discharge_power == 0.0


def test_ev_inherits_storage_validation(ev_base_params: MappingProxyType[str, Any]) -> None:
    base_params = dict(ev_base_params)
    base_params["capacity"] = 0.0
    with pytest.raises(ValidationError, match="Input should be greater than 0"):
        ElectricVehicle(**base_params)


def test_ev_soc_validation(ev_base_params: MappingProxyType[str, Any]) -> None:
    base_params = dict(ev_base_params)
    base_params["soc_start"] = 0.2
    base_params["soc_min"] = 0.3
    with pytest.raises(Exception, match="soc_start"):
        ElectricVehicle(**base_params)


def test_ev_validate_no_overlapping_trips(ev_base_params: MappingProxyType[str, Any]) -> None:
    trip1 = Trip(name="morning", start_time=8, end_time=10, energy_consumption=5.0)
    trip2 = Trip(name="evening", start_time=17, end_time=19, energy_consumption=5.0)
    params = dict(ev_base_params)
    params["trips"] = (trip1, trip2)
    ev = ElectricVehicle(**params)
    ev.validate_no_overlapping_trips()


def test_ev_validate_overlapping_trips_raises(ev_base_params: MappingProxyType[str, Any]) -> None:
    trip1 = Trip(name="morning", start_time=8, end_time=10, energy_consumption=5.0)
    trip2 = Trip(name="overlapping", start_time=9, end_time=11, energy_consumption=5.0)
    params = dict(ev_base_params)
    params["trips"] = (trip1, trip2)
    ev = ElectricVehicle(**params)
    with pytest.raises(OdysValidationError, match="overlap"):
        ev.validate_no_overlapping_trips()


def test_ev_validate_trips_within_horizon(ev_base_params: MappingProxyType[str, Any]) -> None:
    trip1 = Trip(name="morning", start_time=8, end_time=10, energy_consumption=5.0)
    params = dict(ev_base_params)
    params["trips"] = (trip1,)
    ev = ElectricVehicle(**params)
    ev.validate_trips_within_horizon(NUM_STEPS)


def test_ev_validate_trips_beyond_horizon_raises(ev_base_params: MappingProxyType[str, Any]) -> None:
    trip1 = Trip(name="late_trip", start_time=20, end_time=30, energy_consumption=5.0)
    params = dict(ev_base_params)
    params["trips"] = (trip1,)
    ev = ElectricVehicle(**params)
    with pytest.raises(OdysValidationError, match="beyond"):
        ev.validate_trips_within_horizon(NUM_STEPS)
