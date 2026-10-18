"""Checks on the example scripts whose results are plotted in the docs."""

import runpy
from pathlib import Path

import numpy as np

from odys import OptimalDispatchResults

EXAMPLES_DIR = Path(__file__).parents[2] / "examples"


def test_solar_storage_supply_meets_load_at_every_timestep() -> None:
    namespace = runpy.run_path(str(EXAMPLES_DIR / "solar_storage.py"))
    result = namespace["run_solar_storage"]()
    assert isinstance(result, OptimalDispatchResults)

    generation = result.generators.to_dataframe()["power"].unstack("generator").sum(axis=1).to_numpy()
    storage_net_power = result.battery_storages.to_dataframe()["net_power"].to_numpy()

    # net_power > 0 means the battery is charging, i.e. consuming power
    np.testing.assert_allclose(generation - storage_net_power, namespace["LOAD_PROFILE"], atol=1e-6)
