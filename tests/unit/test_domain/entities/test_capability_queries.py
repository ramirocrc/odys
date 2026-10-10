"""Tests for the capability queries every entity answers (supply, demand, energy, horizon)."""

from datetime import timedelta

import pytest

from odys.domain.entities.base import EnergyEntity
from odys.domain.entities.battery import Battery
from odys.domain.entities.charger import Charger
from odys.domain.entities.electric_vehicle import ElectricVehicle
from odys.domain.entities.fixed_load import FixedLoad
from odys.domain.entities.flexible_load import FlexibleLoad
from odys.domain.entities.generator import Generator
from odys.domain.entities.market import EnergyMarket
from odys.domain.entities.stationary_storage import StationaryStorage
from odys.domain.horizon import Horizon, OperatingConditions

NUMBER_OF_STEPS = 3
HALF_HOUR = Horizon(timestep=timedelta(minutes=30), number_of_steps=NUMBER_OF_STEPS)
NO_PROFILE = OperatingConditions(horizon=HALF_HOUR)
NOMINAL_POWER = 100.0
AVAILABLE_CAPACITY = (40.0, 60.0, 80.0)
BATTERY_CAPACITY = 20.0
MAX_DISCHARGE_POWER = 10.0
MAX_TRADING_VOLUME = 50.0
LOAD_VALUES = (30.0, 50.0, 70.0)
MAX_DECREASE = 20.0
ZEROS = (0.0,) * NUMBER_OF_STEPS


def _battery() -> Battery:
    return Battery(
        capacity=BATTERY_CAPACITY,
        max_charge_power=MAX_DISCHARGE_POWER,
        max_discharge_power=MAX_DISCHARGE_POWER,
        soc_start=0.5,
    )


GENERATOR = Generator(name="gen", nominal_power=NOMINAL_POWER, variable_cost=10.0)
STORAGE = StationaryStorage(name="storage", battery=_battery())
ELECTRIC_VEHICLE = ElectricVehicle(name="ev", battery=_battery(), trips=())
MARKET = EnergyMarket(name="market", max_trading_volume_per_step=MAX_TRADING_VOLUME)
FIXED_LOAD = FixedLoad(name="load")
FLEXIBLE_LOAD = FlexibleLoad(name="flex", max_increase=10.0, max_decrease=MAX_DECREASE, value_of_consumption=50.0)
CHARGER = Charger(name="charger", max_power=10.0)


@pytest.mark.parametrize(
    ("entity", "expected"),
    [
        (GENERATOR, (NOMINAL_POWER,) * NUMBER_OF_STEPS),
        (STORAGE, (MAX_DISCHARGE_POWER,) * NUMBER_OF_STEPS),
        (ELECTRIC_VEHICLE, (MAX_DISCHARGE_POWER,) * NUMBER_OF_STEPS),
        (MARKET, (MAX_TRADING_VOLUME,) * NUMBER_OF_STEPS),
        (FIXED_LOAD, ZEROS),
        (FLEXIBLE_LOAD, ZEROS),
        (CHARGER, ZEROS),
    ],
    ids=["generator", "storage", "electric_vehicle", "market", "fixed_load", "flexible_load", "charger"],
)
def test_max_supply_without_profile(entity: EnergyEntity, expected: tuple[float, ...]) -> None:
    assert entity.max_supply(NO_PROFILE) == pytest.approx(expected)


def test_max_supply_of_generator_follows_its_available_capacity_profile() -> None:
    conditions = OperatingConditions(horizon=HALF_HOUR, profile_values=AVAILABLE_CAPACITY)

    assert GENERATOR.max_supply(conditions) == pytest.approx(AVAILABLE_CAPACITY)


@pytest.mark.parametrize(
    ("entity", "expected"),
    [
        (FIXED_LOAD, LOAD_VALUES),
        (FLEXIBLE_LOAD, (10.0, 30.0, 50.0)),
        (GENERATOR, ZEROS),
        (STORAGE, ZEROS),
        (MARKET, ZEROS),
    ],
    ids=["fixed_load", "flexible_load_reduced_by_max_decrease", "generator", "storage", "market"],
)
def test_min_demand_with_profile(entity: EnergyEntity, expected: tuple[float, ...]) -> None:
    conditions = OperatingConditions(horizon=HALF_HOUR, profile_values=LOAD_VALUES)

    assert entity.min_demand(conditions) == pytest.approx(expected)


@pytest.mark.parametrize("entity", [FIXED_LOAD, FLEXIBLE_LOAD], ids=["fixed_load", "flexible_load"])
def test_min_demand_of_load_without_profile_is_zero(entity: EnergyEntity) -> None:
    assert entity.min_demand(NO_PROFILE) == pytest.approx(ZEROS)


@pytest.mark.parametrize(
    ("entity", "expected"),
    [
        (GENERATOR, NOMINAL_POWER * NUMBER_OF_STEPS * HALF_HOUR.hours_per_step),
        (MARKET, MAX_TRADING_VOLUME * NUMBER_OF_STEPS * HALF_HOUR.hours_per_step),
        (STORAGE, MAX_DISCHARGE_POWER * NUMBER_OF_STEPS * HALF_HOUR.hours_per_step),
        (ELECTRIC_VEHICLE, MAX_DISCHARGE_POWER * NUMBER_OF_STEPS * HALF_HOUR.hours_per_step),
        (FIXED_LOAD, 0.0),
    ],
    ids=["generator", "market", "storage_limited_by_power", "electric_vehicle_limited_by_power", "fixed_load"],
)
def test_max_energy_supply_over_the_horizon(entity: EnergyEntity, expected: float) -> None:
    assert entity.max_energy_supply(NO_PROFILE) == pytest.approx(expected)


@pytest.mark.parametrize("entity", [STORAGE, ELECTRIC_VEHICLE], ids=["storage", "electric_vehicle"])
def test_max_energy_supply_of_battery_is_limited_by_its_capacity(entity: EnergyEntity) -> None:
    long_horizon = OperatingConditions(horizon=Horizon(timestep=timedelta(hours=1), number_of_steps=24))

    assert entity.max_energy_supply(long_horizon) == pytest.approx(BATTERY_CAPACITY)


@pytest.mark.parametrize(
    "entity",
    [GENERATOR, STORAGE, MARKET, FIXED_LOAD, FLEXIBLE_LOAD, CHARGER],
    ids=["generator", "storage", "market", "fixed_load", "flexible_load", "charger"],
)
def test_validate_horizon_accepts_any_horizon_by_default(entity: EnergyEntity) -> None:
    entity.validate_horizon(Horizon(timestep=timedelta(hours=1), number_of_steps=1))
