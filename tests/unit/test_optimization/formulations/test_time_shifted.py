"""Unit tests for moving a variable along time with a value from outside the horizon."""

import linopy
import pandas as pd
import pytest
import xarray as xr
from linopy.testing import assert_linequal

from odys.optimization.formulations.base import time_shifted

TIMES = ["0", "1", "2"]
GENERATORS = ["a", "b"]
OUTSIDE_VALUES = [1.0, 5.0]
FIRST_STEP_ONLY = xr.DataArray([1.0, 0.0, 0.0], coords={"time": TIMES})


@pytest.mark.parametrize(
    "dimension_order",
    [("scenario", "time", "generator"), ("scenario", "generator", "time")],
    ids=["entity_last", "time_last"],
)
def test_time_shifted_puts_an_entity_array_on_its_dimension_whatever_the_variable_order(
    dimension_order: tuple[str, ...],
) -> None:
    indexes = {"scenario": ["base"], "time": TIMES, "generator": GENERATORS}
    model = linopy.Model()
    variable = model.add_variables(
        coords=[pd.Index(indexes[dimension], name=dimension) for dimension in dimension_order],
        name="x",
    )
    outside_value = xr.DataArray(OUTSIDE_VALUES, coords={"generator": GENERATORS})

    shifted = time_shifted(variable, 1, outside_value=outside_value)

    expected = (1 * variable).shift(time=1).fillna(0) + FIRST_STEP_ONLY * outside_value
    assert_linequal(shifted, expected)
    assert shifted.const.sel(time="0", generator="b").item() == pytest.approx(OUTSIDE_VALUES[1])


def test_time_shifted_ahead_puts_the_outside_value_at_the_last_step() -> None:
    model = linopy.Model()
    variable = model.add_variables(coords=[pd.Index(TIMES, name="time")], name="x")

    shifted = time_shifted(variable, -1, outside_value=OUTSIDE_VALUES[0])

    assert shifted.const.to_numpy().tolist() == pytest.approx([0.0, 0.0, OUTSIDE_VALUES[0]])
