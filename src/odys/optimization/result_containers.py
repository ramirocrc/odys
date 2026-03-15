"""Containers for storing per-asset optimization results."""

import pandas as pd
from pydantic import BaseModel, ConfigDict, Field


class GeneratorResults(BaseModel):
    """Class to store generator results."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    power: pd.DataFrame
    status: pd.DataFrame
    startup: pd.DataFrame
    shutdown: pd.DataFrame


class StorageResults(BaseModel):
    """Class to store storage results."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    net_power: pd.DataFrame
    state_of_charge: pd.DataFrame


class MarketResults(BaseModel):
    """Class to store market results."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    sell_volume: pd.DataFrame
    buy_volume: pd.DataFrame


class CVaRResults(BaseModel):
    """CVaR optimization results: value at risk, CVaR value, and per-scenario shortfalls."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    value_at_risk: float = Field(description="The VaR threshold η.")
    cvar: float = Field(description="The CVaR value: η - 1/(1-alpha) * Σ_s p_s * z_s.")
    shortfall_per_scenario: pd.Series = Field(description="Per-scenario revenue shortfall z_s.")
