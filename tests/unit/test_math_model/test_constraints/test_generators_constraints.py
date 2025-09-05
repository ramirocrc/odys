import logging

import linopy
import xarray as xr
from linopy.testing import assert_conequal

from optimes.energy_system_models.assets.generator import PowerGenerator
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
