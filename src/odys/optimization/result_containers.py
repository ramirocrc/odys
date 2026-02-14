"""Containers for storing per-asset optimization results."""

import pandas as pd
from pydantic import BaseModel, ConfigDict


class GeneratorResults(BaseModel):
    """Class to store generator results."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    power: pd.DataFrame
    status: pd.DataFrame
    startup: pd.DataFrame
    shutdown: pd.DataFrame


class BatteryResults(BaseModel):
    """Class to store battery results."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    net_power: pd.DataFrame
    state_of_charge: pd.DataFrame


class MarketResults(BaseModel):
    """Class to store market results."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    sell_volume: pd.DataFrame
    buy_volume: pd.DataFrame
