"""Unit tests for ElectricVehicleParameters."""

import pytest

from odys.domain.entities.electric_vehicle import ElectricVehicle
from odys.domain.entities.trip import Trip
from odys.optimization.model.sets import ModelDimension
from odys.optimization.parameters.electric_vehicle_parameters import ElectricVehicleParameters

NUM_EVS = 2
TRIP1_ENERGY_PER_HOUR = 5.0
TRIP2_ENERGY_PER_HOUR = 7.5
TRIP1_MIN_SOC_AT_DEPARTURE = 0.3
TRIP2_MIN_SOC_AT_DEPARTURE = 0.4


@pytest.fixture
def trip1() -> Trip:
    return Trip(
        name="trip1",
        start_time=8,
        end_time=10,
        energy_consumption=10.0,
        min_soc_at_departure=TRIP1_MIN_SOC_AT_DEPARTURE,
    )


@pytest.fixture
def trip2() -> Trip:
    return Trip(
        name="trip2",
        start_time=17,
        end_time=19,
        energy_consumption=15.0,
        min_soc_at_departure=TRIP2_MIN_SOC_AT_DEPARTURE,
    )


@pytest.fixture
def ev1(trip1: Trip, trip2: Trip) -> ElectricVehicle:
    return ElectricVehicle(
        name="ev1",
        capacity=50.0,
        max_charge_power=22.0,
        max_discharge_power=0.0,
        soc_start=0.8,
        trips=(trip1, trip2),
    )


@pytest.fixture
def ev2() -> ElectricVehicle:
    return ElectricVehicle(
        name="ev2",
        capacity=75.0,
        max_charge_power=50.0,
        max_discharge_power=25.0,
        soc_start=0.5,
        trips=(),
    )


@pytest.fixture
def ev_parameters(ev1: ElectricVehicle, ev2: ElectricVehicle) -> ElectricVehicleParameters:
    return ElectricVehicleParameters(24, [ev1, ev2])


def test_ev_parameters_creation(ev_parameters: ElectricVehicleParameters) -> None:
    """Test that ElectricVehicleParameters can be created with EVs."""
    assert not ev_parameters.is_empty
    assert ev_parameters.index.dimension == ModelDimension.EVs
    assert len(ev_parameters.index.values) == NUM_EVS


def test_ev_parameters_empty() -> None:
    """Test that empty ElectricVehicleParameters can be created."""
    params = ElectricVehicleParameters(24)
    assert params.is_empty
    assert len(params.index.values) == 0


def test_ev_parameters_index(ev_parameters: ElectricVehicleParameters) -> None:
    """Test that index property returns correct index."""
    index = ev_parameters.index
    assert index.dimension == ModelDimension.EVs
    assert index.values == ("ev1", "ev2")


def test_ev_parameters_is_driving(ev_parameters: ElectricVehicleParameters) -> None:
    """Test that is_driving array is correctly built."""
    is_driving = ev_parameters.is_driving
    assert is_driving.dims == (ModelDimension.EVs.value, ModelDimension.Time.value)
    assert is_driving.shape == (2, 24)

    # ev1 is driving during trip1 (8-10) and trip2 (17-19)
    assert is_driving.sel(ev="ev1", time=8).values == 1
    assert is_driving.sel(ev="ev1", time=9).values == 1
    assert is_driving.sel(ev="ev1", time=10).values == 0
    assert is_driving.sel(ev="ev1", time=17).values == 1
    assert is_driving.sel(ev="ev1", time=18).values == 1
    assert is_driving.sel(ev="ev1", time=5).values == 0

    # ev2 has no trips, so never driving
    assert is_driving.sel(ev="ev2", time=8).values == 0
    assert is_driving.sel(ev="ev2", time=17).values == 0


def test_ev_parameters_trip_energy(ev_parameters: ElectricVehicleParameters) -> None:
    """Test that trip_energy array is correctly built."""
    trip_energy = ev_parameters.trip_energy
    assert trip_energy.dims == (ModelDimension.EVs.value, ModelDimension.Time.value)
    assert trip_energy.shape == (2, 24)

    # ev1 trip1: 10 MWh over 2 hours = 5 MWh/hour at t=8,9
    assert trip_energy.sel(ev="ev1", time=8).values == TRIP1_ENERGY_PER_HOUR
    assert trip_energy.sel(ev="ev1", time=9).values == TRIP1_ENERGY_PER_HOUR
    assert trip_energy.sel(ev="ev1", time=10).values == 0.0

    # ev1 trip2: 15 MWh over 2 hours = 7.5 MWh/hour at t=17,18
    assert trip_energy.sel(ev="ev1", time=17).values == TRIP2_ENERGY_PER_HOUR
    assert trip_energy.sel(ev="ev1", time=18).values == TRIP2_ENERGY_PER_HOUR

    # ev2 has no trips
    assert trip_energy.sel(ev="ev2", time=8).values == 0.0


def test_ev_parameters_min_soc_at_departure(ev_parameters: ElectricVehicleParameters) -> None:
    """Test that min_soc_at_departure array is correctly built."""
    min_soc = ev_parameters.min_soc_at_departure
    assert min_soc.dims == (ModelDimension.EVs.value, ModelDimension.Time.value)
    assert min_soc.shape == (2, 24)

    # ev1 trip1: min_soc_at_departure=0.3 at t=8
    assert min_soc.sel(ev="ev1", time=8).values == TRIP1_MIN_SOC_AT_DEPARTURE
    # ev1 trip2: min_soc_at_departure=0.4 at t=17
    assert min_soc.sel(ev="ev1", time=17).values == TRIP2_MIN_SOC_AT_DEPARTURE
    # Other times should be 0
    assert min_soc.sel(ev="ev1", time=5).values == 0.0
    assert min_soc.sel(ev="ev1", time=10).values == 0.0

    # ev2 has no trips
    assert min_soc.sel(ev="ev2", time=8).values == 0.0


def test_ev_parameters_empty_trips() -> None:
    """Test that ElectricVehicleParameters with no trips builds empty arrays."""
    ev = ElectricVehicle(
        name="ev_no_trips",
        capacity=50.0,
        max_charge_power=22.0,
        max_discharge_power=0.0,
        soc_start=0.8,
        trips=(),
    )
    params = ElectricVehicleParameters(24, [ev])

    assert not params.is_empty
    assert params.is_driving.shape == (1, 24)
    assert params.trip_energy.shape == (1, 24)
    assert params.min_soc_at_departure.shape == (1, 24)

    # All zeros since no trips
    assert params.is_driving.sel(ev="ev_no_trips", time=8).values == 0
    assert params.trip_energy.sel(ev="ev_no_trips", time=8).values == 0.0
    assert params.min_soc_at_departure.sel(ev="ev_no_trips", time=8).values == 0.0
