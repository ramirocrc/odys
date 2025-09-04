import logging
from datetime import timedelta

import linopy
import pytest
import xarray as xr
from linopy.testing import assert_conequal

from optimes._math_model.model_builder import EnergyAlgebraicModelBuilder
from optimes._math_model.model_components.constraints.constraint_names import ModelConstraintName as ConName
from optimes.energy_system_models.assets.generator import PowerGenerator
from optimes.energy_system_models.assets.portfolio import AssetPortfolio
from optimes.energy_system_models.assets.storage import Battery
from optimes.energy_system_models.units import PowerUnit
from optimes.energy_system_models.validated_energy_system import ValidatedEnergySystem

logger = logging.getLogger(__name__)


@pytest.fixture
def generator1() -> PowerGenerator:
    return PowerGenerator(
        name="gen1",
        nominal_power=100.0,
        variable_cost=20.0,
    )


@pytest.fixture
def generator2() -> PowerGenerator:
    return PowerGenerator(
        name="gen2",
        nominal_power=150.0,
        variable_cost=25.0,
    )


@pytest.fixture
def battery1() -> Battery:
    return Battery(
        name="batt1",
        max_power=200.0,
        capacity=100.0,
        efficiency_charging=0.9,
        efficiency_discharging=0.8,
        soc_start=25.0,
        soc_end=50.0,
    )


@pytest.fixture
def asset_portfolio_sample(
    generator1: PowerGenerator,
    generator2: PowerGenerator,
    battery1: Battery,
) -> AssetPortfolio:
    portfolio = AssetPortfolio()
    portfolio.add_asset(generator1)
    portfolio.add_asset(generator2)
    portfolio.add_asset(battery1)
    return portfolio


@pytest.fixture
def demand_profile_sample() -> list[float]:
    return [150, 200, 150]


@pytest.fixture
def time_index(demand_profile_sample: list[float]) -> list[int]:
    return list(range(len(demand_profile_sample)))


@pytest.fixture
def energy_system_sample(
    asset_portfolio_sample: AssetPortfolio,
    demand_profile_sample: list[float],
) -> ValidatedEnergySystem:
    return ValidatedEnergySystem(
        portfolio=asset_portfolio_sample,
        demand_profile=demand_profile_sample,
        timestep=timedelta(hours=1),
        power_unit=PowerUnit.MegaWatt,
    )


@pytest.fixture
def linopy_model(energy_system_sample: ValidatedEnergySystem) -> linopy.Model:
    model_builder = EnergyAlgebraicModelBuilder(energy_system_sample)
    return model_builder.build()


@pytest.fixture(params=["generator1", "generator2"])
def generator(request) -> PowerGenerator:  # noqa: ANN001
    return request.getfixturevalue(request.param)


def test_constraint_power_balance(
    linopy_model: linopy.Model,
    demand_profile_sample: list[float],
    time_index: list[int],
) -> None:
    actual_constraint = linopy_model.constraints[ConName.POWER_BALANCE.value]

    generation_total = linopy_model.variables["generator_power"].sum("generators")
    discharge_total = linopy_model.variables["battery_power_out"].sum("batteries")
    charge_total = linopy_model.variables["battery_power_in"].sum("batteries")

    demand_array = xr.DataArray(demand_profile_sample, coords=[time_index], dims=["time"])
    expected_expr = generation_total + discharge_total - charge_total == demand_array

    assert_conequal(expected_expr, actual_constraint.lhs == actual_constraint.rhs)


def test_constraint_generator_limit(
    linopy_model: linopy.Model,
    generator1: PowerGenerator,
    generator2: PowerGenerator,
    time_index: list[int],
) -> None:
    actual_constraint = linopy_model.constraints[ConName.GENERATOR_LIMIT.value]

    generator_power = linopy_model.variables["generator_power"]

    nominal_powers = [[generator1.nominal_power, generator2.nominal_power]] * len(time_index)
    nominal_power_array = xr.DataArray(
        nominal_powers,
        coords=[time_index, [generator1.name, generator2.name]],
        dims=["time", "generators"],
    )

    expected_expr = generator_power <= nominal_power_array
    assert_conequal(expected_expr, actual_constraint.lhs <= actual_constraint.rhs)


def test_constraint_battery_charge_limit(
    linopy_model: linopy.Model,
    battery1: Battery,
) -> None:
    actual_constraint = linopy_model.constraints[ConName.BATTERY_CHARGE_LIMIT.value]

    battery_charge = linopy_model.variables["battery_power_in"]
    battery_charge_mode = linopy_model.variables["battery_charge_mode"]

    expected_expr = battery_charge <= battery_charge_mode * battery1.max_power

    assert_conequal(expected_expr, actual_constraint.lhs <= actual_constraint.rhs)


def test_constraint_battery_discharge_limit(
    linopy_model: linopy.Model,
    battery1: Battery,
) -> None:
    actual_constraint = linopy_model.constraints[ConName.BATTERY_DISCHARGE_LIMIT.value]

    battery_discharge = linopy_model.variables["battery_power_out"]
    battery_charge_mode = linopy_model.variables["battery_charge_mode"]

    expected_expr = battery_discharge + battery_charge_mode * battery1.max_power <= battery1.max_power

    assert_conequal(expected_expr, actual_constraint.lhs <= actual_constraint.rhs)


def test_constraint_battery_soc_dynamics(
    linopy_model: linopy.Model,
    battery1: Battery,
    time_index: list[int],
) -> None:
    actual_constraint = linopy_model.constraints[ConName.BATTERY_SOC_DYNAMICS.value]

    battery_soc = linopy_model.variables["battery_soc"]
    battery_charge = linopy_model.variables["battery_power_in"]
    battery_discharge = linopy_model.variables["battery_power_out"]

    eff_ch = battery1.efficiency_charging
    eff_disch = battery1.efficiency_discharging

    for t in time_index[1:]:  # Skip t=0
        actual_t = actual_constraint.sel(time=str(t), batteries="batt1")

        bat_soc_t = battery_soc.sel(time=str(t), batteries="batt1")
        bat_soc_t_minus_1 = battery_soc.sel(time=str(t - 1), batteries="batt1")
        battery_charge_t = battery_charge.sel(time=str(t), batteries="batt1")
        battery_discharge_t = battery_discharge.sel(time=str(t), batteries="batt1")
        expected_expr = bat_soc_t == bat_soc_t_minus_1 + eff_ch * battery_charge_t - 1 / eff_disch * battery_discharge_t

        assert_conequal(expected_expr, actual_t.lhs == actual_t.rhs)


def test_constraint_battery_soc_bounds(
    linopy_model: linopy.Model,
    battery1: Battery,
) -> None:
    actual_constraint = linopy_model.constraints[ConName.BATTERY_SOC_BOUNDS.value]

    battery_soc = linopy_model.variables["battery_soc"]
    expected_expr = battery_soc <= battery1.capacity

    assert_conequal(expected_expr, actual_constraint.lhs <= actual_constraint.rhs)


def test_constraint_battery_soc_terminal(
    linopy_model: linopy.Model,
    battery1: Battery,
    time_index: list[int],
) -> None:
    actual_constraint = linopy_model.constraints[ConName.BATTERY_SOC_END.value]

    battery_soc = linopy_model.variables["battery_soc"]
    final_soc = battery_soc.sel(time=str(time_index[-1]))
    expected_expr = final_soc == battery1.soc_end

    assert_conequal(expected_expr, actual_constraint.lhs == actual_constraint.rhs)
