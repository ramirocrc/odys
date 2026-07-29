"""Unit tests for the Trip entity."""

from types import MappingProxyType
from typing import Any

import pytest
from pydantic import ValidationError

from odys.domain.entities.trip import Trip
from odys.domain.exceptions import OdysValidationError

TRIP_START_TIME = 8
TRIP_END_TIME = 9
TRIP_ENERGY_CONSUMPTION = 5.0
TRIP_MIN_SOC_AT_DEPARTURE = 0.3


@pytest.fixture
def trip_base_params() -> MappingProxyType[str, Any]:
    return MappingProxyType({
        "name": "morning_commute",
        "start_time": TRIP_START_TIME,
        "end_time": TRIP_END_TIME,
        "energy_consumption": TRIP_ENERGY_CONSUMPTION,
    })


def test_trip_creation_with_valid_parameters(trip_base_params: MappingProxyType[str, Any]) -> None:
    trip = Trip(**dict(trip_base_params))
    assert trip.name == "morning_commute"
    assert trip.start_time == TRIP_START_TIME
    assert trip.end_time == TRIP_END_TIME
    assert trip.energy_consumption == TRIP_ENERGY_CONSUMPTION
    assert trip.min_soc_at_departure == 0.0


def test_trip_creation_with_min_soc(trip_base_params: MappingProxyType[str, Any]) -> None:
    trip = Trip(**dict(trip_base_params), min_soc_at_departure=TRIP_MIN_SOC_AT_DEPARTURE)
    assert trip.min_soc_at_departure == TRIP_MIN_SOC_AT_DEPARTURE


@pytest.mark.parametrize(
    ("param_name", "invalid_value", "expected_match"),
    [
        ("start_time", -1, "Input should be greater than or equal to 0"),
        ("end_time", -1, "Input should be greater than or equal to 0"),
        ("energy_consumption", 0.0, "Input should be greater than 0"),
        ("energy_consumption", -1.0, "Input should be greater than 0"),
        ("min_soc_at_departure", -0.1, "Input should be greater than or equal to 0"),
        ("min_soc_at_departure", 1.1, "Input should be less than or equal to 1"),
    ],
)
def test_trip_creation_with_invalid_parameters_raises_error(
    param_name: str,
    invalid_value: float,
    expected_match: str,
    trip_base_params: MappingProxyType[str, Any],
) -> None:
    base_params = dict(trip_base_params)
    base_params[param_name] = invalid_value
    with pytest.raises(ValidationError, match=expected_match):
        Trip(**base_params)


def test_trip_end_time_must_be_greater_than_start_time(trip_base_params: MappingProxyType[str, Any]) -> None:
    base_params = dict(trip_base_params)
    base_params["end_time"] = 8
    base_params["start_time"] = 8
    with pytest.raises(OdysValidationError, match=r"end_time \(8\) must be > start_time \(8\)"):
        Trip(**base_params)


def test_trip_end_time_less_than_start_time_raises_error(trip_base_params: MappingProxyType[str, Any]) -> None:
    base_params = dict(trip_base_params)
    base_params["end_time"] = 7
    base_params["start_time"] = 8
    with pytest.raises(OdysValidationError, match=r"end_time \(7\) must be > start_time \(8\)"):
        Trip(**base_params)
