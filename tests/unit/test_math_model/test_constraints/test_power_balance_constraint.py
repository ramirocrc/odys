import logging

import linopy
import xarray as xr
from linopy.testing import assert_conequal

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
