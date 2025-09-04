import logging

import linopy
import xarray as xr
from linopy.testing import assert_conequal

from optimes.energy_system_models.assets.generator import PowerGenerator
from optimes.energy_system_models.assets.storage import Battery
from tests.utils.fixtures import (  # noqa: F401
    asset_portfolio_sample,
    battery1,
    demand_profile_sample,
    energy_system_sample,
    generator1,
    generator2,
    linopy_model,
    time_index,
)

logger = logging.getLogger(__name__)


def test_constraint_power_balance(
    linopy_model: linopy.Model,
    demand_profile_sample: list[float],
    time_index: list[int],
) -> None:
    actual_constraint = linopy_model.constraints["power_balance_constraint"]

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
    actual_constraint = linopy_model.constraints["generator_max_power_constraint"]

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
    actual_constraint = linopy_model.constraints["battery_max_charge_constraint"]

    battery_charge = linopy_model.variables["battery_power_in"]
    battery_charge_mode = linopy_model.variables["battery_charge_mode"]

    expected_expr = battery_charge <= battery_charge_mode * battery1.max_power

    assert_conequal(expected_expr, actual_constraint.lhs <= actual_constraint.rhs)


def test_constraint_battery_discharge_limit(
    linopy_model: linopy.Model,
    battery1: Battery,
) -> None:
    actual_constraint = linopy_model.constraints["battery_max_discharge_constraint"]

    battery_discharge = linopy_model.variables["battery_power_out"]
    battery_charge_mode = linopy_model.variables["battery_charge_mode"]

    expected_expr = battery_discharge + battery_charge_mode * battery1.max_power <= battery1.max_power

    assert_conequal(expected_expr, actual_constraint.lhs <= actual_constraint.rhs)


def test_constraint_battery_soc_dynamics(
    linopy_model: linopy.Model,
    battery1: Battery,
    time_index: list[int],
) -> None:
    actual_constraint = linopy_model.constraints["battery_soc_dynamics_constraint"]

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
    actual_constraint = linopy_model.constraints["battery_soc_bounds_constraint"]

    battery_soc = linopy_model.variables["battery_soc"]
    expected_expr = battery_soc <= battery1.capacity

    assert_conequal(expected_expr, actual_constraint.lhs <= actual_constraint.rhs)


def test_constraint_battery_soc_terminal(
    linopy_model: linopy.Model,
    battery1: Battery,
    time_index: list[int],
) -> None:
    actual_constraint = linopy_model.constraints["battery_soc_end_constraint"]

    battery_soc = linopy_model.variables["battery_soc"]
    final_soc = battery_soc.sel(time=str(time_index[-1]))
    expected_expr = final_soc == battery1.soc_end

    assert_conequal(expected_expr, actual_constraint.lhs == actual_constraint.rhs)
