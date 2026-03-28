"""Frozen snapshot of solved model data for result extraction."""

from collections.abc import Hashable

import pandas as pd
import xarray as xr
from pydantic import BaseModel, ConfigDict

from odys.optimization.objective import CVaRTerm


class SolvedModelData(BaseModel):
    """Frozen snapshot of data extracted from a solved EnergyMILPModel.

    Captures only what OptimizationResults needs, allowing the full
    linopy model to be garbage-collected after solving.
    """

    model_config = ConfigDict(frozen=True, extra="forbid", arbitrary_types_allowed=True)

    solution: xr.Dataset
    variable_names: frozenset[Hashable]
    has_generators: bool
    has_storages: bool
    has_markets: bool
    cvar_term: CVaRTerm | None
    scenario_probabilities: pd.Series | None
