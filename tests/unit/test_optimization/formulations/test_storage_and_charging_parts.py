"""Unit tests for the shared battery model, the EV trip drop, and charging's coupling to electric vehicles."""

from datetime import timedelta

import linopy
import pytest
import xarray as xr
from linopy.testing import assert_linequal

from odys.domain.entities.battery import Battery
from odys.domain.entities.charger import Charger
from odys.domain.entities.electric_vehicle import ElectricVehicle
from odys.domain.entities.fixed_load import FixedLoad
from odys.domain.entities.generator import Generator
from odys.domain.entities.portfolio import AssetPortfolio
from odys.domain.entities.trip import Trip
from odys.domain.exceptions import OdysError
from odys.domain.profiles import LoadProfile
from odys.domain.scenario import Scenario
from odys.energy_system import EnergySystem
from odys.optimization.formulations.base import Formulation, FormulationInputs
from odys.optimization.formulations.charging import ChargingFormulation
from odys.optimization.formulations.electric_vehicle import ElectricVehicleFormulation
from odys.optimization.model.model_builder import build_model
from odys.optimization.problem import OptimizationProblem

NUMBER_OF_STEPS = 3
HOURS_PER_STEP = 1.0
EV_CAPACITY = 50.0
TRIP_ENERGY = 5.0
TRIP_SOC_DROP = TRIP_ENERGY / EV_CAPACITY
DEGRADATION_COST = 2.0
DEMAND = [10.0, 10.0, 10.0]

EV = ElectricVehicle(
    name="ev1",
    battery=Battery(
        capacity=EV_CAPACITY,
        max_charge_power=22.0,
        max_discharge_power=11.0,
        soc_start=0.5,
        degradation_cost=DEGRADATION_COST,
    ),
    trips=(Trip(name="trip1", start_time=1, end_time=2, energy_consumption=TRIP_ENERGY),),
)
EV_LEAVING_AT_T0 = ElectricVehicle(
    name="ev_early",
    battery=Battery(capacity=EV_CAPACITY, max_charge_power=22.0, max_discharge_power=11.0, soc_start=0.5),
    trips=(Trip(name="early", start_time=0, end_time=1, energy_consumption=TRIP_ENERGY),),
)
CHARGER = Charger(name="charger1", max_power=22.0)
GENERATOR = Generator(name="gen", nominal_power=100.0, variable_cost=10.0)
LOAD = FixedLoad(name="load")


@pytest.fixture
def optimization_problem() -> OptimizationProblem:
    return EnergySystem(
        portfolio=AssetPortfolio([GENERATOR, LOAD, EV, CHARGER]),
        timestep=timedelta(hours=HOURS_PER_STEP),
        number_of_steps=NUMBER_OF_STEPS,
        scenarios=Scenario(profiles=(LoadProfile(load=LOAD, values=DEMAND),)),
    ).build_problem()


@pytest.fixture
def linopy_model(optimization_problem: OptimizationProblem) -> linopy.Model:
    return build_model(optimization_problem).linopy_model


@pytest.fixture
def electric_vehicles(
    optimization_problem: OptimizationProblem,
    linopy_model: linopy.Model,
) -> ElectricVehicleFormulation:
    assert linopy_model is not None
    formulation = optimization_problem.formulation_of(ElectricVehicleFormulation)
    assert formulation is not None
    return formulation


def test_ev_variable_names_carry_the_dimension_prefix(electric_vehicles: ElectricVehicleFormulation) -> None:
    variables = electric_vehicles.variables
    assert variables.power_in.name == ElectricVehicleFormulation.power_in_name
    assert variables.net_power.name == ElectricVehicleFormulation.net_power_name
    assert variables.soc.name == ElectricVehicleFormulation.soc_name
    assert variables.charge_mode.name == ElectricVehicleFormulation.charge_mode_name
    assert variables.power_out.name == "ev_power_out"


def test_ev_power_injection_is_discharge_minus_charge(
    electric_vehicles: ElectricVehicleFormulation,
    linopy_model: linopy.Model,
) -> None:
    variables = linopy_model.variables
    expected = variables["ev_power_out"].sum("ev") - variables["ev_power_in"].sum("ev")
    assert_linequal(electric_vehicles.power_injection(), expected)


def test_ev_profit_is_minus_the_degradation_cost(
    electric_vehicles: ElectricVehicleFormulation,
    linopy_model: linopy.Model,
) -> None:
    variables = linopy_model.variables
    cost = xr.DataArray([DEGRADATION_COST], coords={"ev": [EV.name]})
    expected = -(((variables["ev_power_in"] + variables["ev_power_out"]) * HOURS_PER_STEP) * cost).sum(["time", "ev"])
    assert_linequal(electric_vehicles.profit(), expected)


def test_ev_trip_energy_lowers_the_soc_during_the_trip(linopy_model: linopy.Model) -> None:
    dynamics = linopy_model.constraints["ev_soc_dynamics_constraint"]

    assert float(dynamics.rhs.sel(scenario="base", ev="ev1", time="1")) == pytest.approx(-TRIP_SOC_DROP)
    assert float(dynamics.rhs.sel(scenario="base", ev="ev1", time="2")) == pytest.approx(0.0)


def test_charging_is_outside_the_power_balance(
    optimization_problem: OptimizationProblem,
    linopy_model: linopy.Model,
) -> None:
    charging: Formulation | None = optimization_problem.formulation_of(ChargingFormulation)
    assert charging is not None
    assert charging.power_injection() is None

    balance_variables = set(linopy_model.constraints["power_balance_constraint"].vars.values.ravel())
    assignment_labels = set(linopy_model.variables[ChargingFormulation.assignment_name].labels.values.ravel())
    assert not balance_variables & assignment_labels


def test_charging_uses_the_electric_vehicle_formulation(
    optimization_problem: OptimizationProblem,
    electric_vehicles: ElectricVehicleFormulation,
) -> None:
    charging = optimization_problem.formulation_of(ChargingFormulation)
    assert charging is not None
    assert charging.electric_vehicles is electric_vehicles


def test_charging_without_an_electric_vehicle_formulation_raises(optimization_problem: OptimizationProblem) -> None:
    inputs = FormulationInputs(entities=(CHARGER,), context=optimization_problem.context)
    with pytest.raises(OdysError, match="must be built after an ElectricVehicleFormulation"):
        ChargingFormulation.build(inputs)


def test_formulation_inputs_select_entities_and_built_formulations(
    optimization_problem: OptimizationProblem,
    electric_vehicles: ElectricVehicleFormulation,
) -> None:
    inputs = FormulationInputs(
        entities=(GENERATOR, EV, CHARGER),
        context=optimization_problem.context,
        built=(electric_vehicles,),
    )

    assert inputs.of_type(ElectricVehicle) == [EV]
    assert inputs.formulation_of(ElectricVehicleFormulation) is electric_vehicles
    assert inputs.formulation_of(ChargingFormulation) is None


def test_soc_start_draws_the_energy_of_a_trip_departing_at_t0() -> None:
    model = build_model(
        EnergySystem(
            portfolio=AssetPortfolio([GENERATOR, LOAD, EV, EV_LEAVING_AT_T0, CHARGER]),
            timestep=timedelta(hours=HOURS_PER_STEP),
            number_of_steps=NUMBER_OF_STEPS,
            scenarios=Scenario(profiles=(LoadProfile(load=LOAD, values=DEMAND),)),
        ).build_problem(),
    ).linopy_model
    soc_start = model.constraints["ev_soc_start_constraint"]

    leaving_at_t0 = soc_start.rhs.sel(scenario="base", ev=EV_LEAVING_AT_T0.name)
    no_trip_at_t0 = soc_start.rhs.sel(scenario="base", ev=EV.name)
    assert float(leaving_at_t0) == pytest.approx(EV_LEAVING_AT_T0.battery.soc_start - TRIP_SOC_DROP)
    assert float(no_trip_at_t0) == pytest.approx(EV.battery.soc_start)
