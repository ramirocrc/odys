"""Integration tests for EV fleet optimization."""

from datetime import timedelta

import numpy as np
import pytest

from odys import (
    AssetPortfolio,
    Charger,
    ElectricVehicle,
    EnergyMarket,
    EnergySystem,
    FixedLoad,
    Generator,
    Scenario,
    StandaloneStorage,
    TradeDirection,
    Trip,
)

EV_CAPACITY = 50.0
EV_MAX_CHARGE_POWER = 22.0
EV_MAX_DISCHARGE_POWER = 11.0
CHARGER_MAX_POWER = 50.0
STORAGE_CAPACITY = 100.0
GENERATOR_POWER = 200.0
MIN_SOC_AT_DEPARTURE = 0.3
MIN_FINAL_SOC = 0.2


def _create_ev(  # noqa: PLR0913
    name: str,
    capacity: float = EV_CAPACITY,
    max_charge_power: float = EV_MAX_CHARGE_POWER,
    max_discharge_power: float = 0.0,
    soc_start: float = 0.5,
    trips: tuple[Trip, ...] = (),
) -> ElectricVehicle:
    return ElectricVehicle(
        name=name,
        capacity=capacity,
        max_charge_power=max_charge_power,
        max_discharge_power=max_discharge_power,
        soc_start=soc_start,
        trips=trips,
    )


def _create_charger(name: str, max_power: float = CHARGER_MAX_POWER) -> Charger:
    return Charger(name=name, max_power=max_power)


class TestSingleEvSingleCharger:
    def test_basic_charging_no_trips(self) -> None:
        ev = _create_ev("ev1")
        charger = _create_charger("charger1")
        gen = Generator(name="gen1", nominal_power=GENERATOR_POWER, variable_cost=20.0)
        load = FixedLoad(name="load1")
        load_profile = [50.0, 50.0, 100.0, 100.0, 50.0]

        portfolio = AssetPortfolio(assets=[ev, charger, gen, load])
        system = EnergySystem(
            portfolio=portfolio,
            number_of_steps=len(load_profile),
            timestep=timedelta(hours=1),
            scenarios=Scenario(fixed_load_profiles={"load1": load_profile}),
        )
        result = system.optimize()

        assert result.solver_status == "ok"
        ev_results = result.electric_vehicles
        assert len(ev_results) == 1

        charger_results = result.chargers
        assert len(charger_results) == 1

        ev_soc = ev_results.soc.unstack()
        assert (ev_soc >= 0).all().all()
        assert (ev_soc <= 1).all().all()

    def test_ev_with_trips(self) -> None:
        trip = Trip(name="commute", start_time=2, end_time=3, energy_consumption=5.0, min_soc_at_departure=0.3)
        ev = _create_ev("ev1", soc_start=0.5, trips=(trip,))
        charger = _create_charger("charger1")
        gen = Generator(name="gen1", nominal_power=GENERATOR_POWER, variable_cost=20.0)
        load = FixedLoad(name="load1")
        load_profile = [50.0, 50.0, 50.0, 50.0, 50.0]

        portfolio = AssetPortfolio(assets=[ev, charger, gen, load])
        system = EnergySystem(
            portfolio=portfolio,
            number_of_steps=len(load_profile),
            timestep=timedelta(hours=1),
            scenarios=Scenario(fixed_load_profiles={"load1": load_profile}),
        )
        result = system.optimize()

        assert result.solver_status == "ok"
        ev_soc = result.electric_vehicles.soc.unstack()

        assert ev_soc.iloc[1, 0] >= MIN_SOC_AT_DEPARTURE  # type: ignore[operator]

        ev_net_power = result.electric_vehicles.net_power.unstack()
        assert ev_net_power.iloc[2, 0] == pytest.approx(0.0, abs=1e-4)


class TestMultipleEvsMultipleChargers:
    def test_assignment_optimization(self) -> None:
        ev1 = _create_ev("ev1", soc_start=0.3)
        ev2 = _create_ev("ev2", soc_start=0.7)
        charger1 = _create_charger("charger1", max_power=22.0)
        charger2 = _create_charger("charger2", max_power=50.0)
        gen = Generator(name="gen1", nominal_power=GENERATOR_POWER, variable_cost=20.0)
        load = FixedLoad(name="load1")
        load_profile = [50.0, 50.0, 100.0, 100.0, 50.0]

        portfolio = AssetPortfolio(assets=[ev1, ev2, charger1, charger2, gen, load])
        system = EnergySystem(
            portfolio=portfolio,
            number_of_steps=len(load_profile),
            timestep=timedelta(hours=1),
            scenarios=Scenario(fixed_load_profiles={"load1": load_profile}),
        )
        result = system.optimize()

        assert result.solver_status == "ok"

        assignment = result.chargers.assignment
        assert len(assignment) > 0

        assignment_array = np.array(assignment.values)
        assignment_values = assignment_array.reshape(len(load_profile), -1)
        for t in range(len(load_profile)):
            assert assignment_values[t].sum() <= 2.0 + 1e-6


class TestMixedFleet:
    def test_standalone_storage_independent_of_chargers(self) -> None:
        ev = _create_ev("ev1")
        charger = _create_charger("charger1")
        storage = StandaloneStorage(
            name="battery",
            capacity=STORAGE_CAPACITY,
            max_charge_power=50.0,
            max_discharge_power=50.0,
            soc_start=0.5,
        )
        gen = Generator(name="gen1", nominal_power=GENERATOR_POWER, variable_cost=20.0)
        load = FixedLoad(name="load1")
        load_profile = [50.0, 50.0, 150.0, 150.0, 50.0]

        portfolio = AssetPortfolio(assets=[ev, charger, storage, gen, load])
        system = EnergySystem(
            portfolio=portfolio,
            number_of_steps=len(load_profile),
            timestep=timedelta(hours=1),
            scenarios=Scenario(fixed_load_profiles={"load1": load_profile}),
        )
        result = system.optimize()

        assert result.solver_status == "ok"

        storage_soc = result.standalone_storages.soc.unstack()
        assert (storage_soc >= 0).all().all()
        assert (storage_soc <= 1).all().all()

        ev_soc = result.electric_vehicles.soc.unstack()
        assert (ev_soc >= 0).all().all()
        assert (ev_soc <= 1).all().all()


class TestEvFleetWithMarket:
    def test_arbitrage_with_v2g(self) -> None:
        ev = _create_ev("ev1", max_discharge_power=EV_MAX_DISCHARGE_POWER, soc_start=0.8)
        charger = _create_charger("charger1")
        gen = Generator(name="gen1", nominal_power=GENERATOR_POWER, variable_cost=30.0)
        load = FixedLoad(name="load1")
        market = EnergyMarket(
            name="grid",
            trade_direction=TradeDirection.BUY_AND_SELL,
            max_trading_volume_per_step=100.0,
        )
        load_profile = [50.0, 50.0, 50.0, 50.0, 50.0]
        market_prices = {"grid": [20.0, 20.0, 50.0, 50.0, 20.0]}

        portfolio = AssetPortfolio(assets=[ev, charger, gen, load, market])
        system = EnergySystem(
            portfolio=portfolio,
            markets=[market],
            number_of_steps=len(load_profile),
            timestep=timedelta(hours=1),
            scenarios=Scenario(
                fixed_load_profiles={"load1": load_profile},
                market_prices=market_prices,
            ),
        )
        result = system.optimize()

        assert result.solver_status == "ok"

        ev_net_power = result.electric_vehicles.net_power.unstack()
        assert ev_net_power.shape[1] == 1

    def test_trip_constraints_bind_under_price_incentive(self) -> None:
        trip = Trip(name="commute", start_time=2, end_time=4, energy_consumption=5.0, min_soc_at_departure=0.6)
        ev = _create_ev("ev1", max_discharge_power=EV_MAX_DISCHARGE_POWER, soc_start=0.5, trips=(trip,))
        charger = _create_charger("charger1")
        market = EnergyMarket(
            name="grid",
            trade_direction=TradeDirection.BUY_AND_SELL,
            max_trading_volume_per_step=100.0,
        )
        market_prices = {"grid": [5.0, 5.0, 200.0, 200.0, 5.0]}

        portfolio = AssetPortfolio(assets=[ev, charger, market])
        system = EnergySystem(
            portfolio=portfolio,
            markets=[market],
            number_of_steps=5,
            timestep=timedelta(hours=1),
            scenarios=Scenario(market_prices=market_prices),
        )
        result = system.optimize()

        assert result.solver_status == "ok"

        ev_net_power = result.electric_vehicles.net_power.unstack()
        assert ev_net_power.iloc[2, 0] == pytest.approx(0.0, abs=1e-6)
        assert ev_net_power.iloc[3, 0] == pytest.approx(0.0, abs=1e-6)

        ev_soc = result.electric_vehicles.soc.unstack()
        assert ev_soc.iloc[1, 0] >= trip.min_soc_at_departure - 1e-6  # type: ignore[operator]


class TestEvFleetWithSolar:
    def test_maximize_self_consumption(self) -> None:
        ev = _create_ev("ev1", soc_start=0.2)
        charger = _create_charger("charger1")
        solar = Generator(name="solar", nominal_power=100.0, variable_cost=0.0)
        gen = Generator(name="gen_backup", nominal_power=GENERATOR_POWER, variable_cost=40.0)
        load = FixedLoad(name="load1")
        load_profile = [30.0, 30.0, 30.0, 30.0, 30.0]
        solar_profile = {"solar": [0.0, 50.0, 100.0, 50.0, 0.0]}

        portfolio = AssetPortfolio(assets=[ev, charger, solar, gen, load])
        system = EnergySystem(
            portfolio=portfolio,
            number_of_steps=len(load_profile),
            timestep=timedelta(hours=1),
            scenarios=Scenario(
                fixed_load_profiles={"load1": load_profile},
                available_capacity_profiles=solar_profile,
            ),
        )
        result = system.optimize()

        assert result.solver_status == "ok"

        ev_soc = result.electric_vehicles.soc.unstack()
        final_soc: float = ev_soc.iloc[-1, 0]  # type: ignore[assignment]
        assert final_soc > MIN_FINAL_SOC
