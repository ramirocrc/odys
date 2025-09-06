"""This module provide the containers for storing asset results."""

import pandas as pd
from pydantic import BaseModel


class GeneratorResults(BaseModel, arbitrary_types_allowed=True):
    """Class to store generator results."""

    power: pd.DataFrame
    status: pd.DataFrame
    startup: pd.DataFrame
    shutdown: pd.DataFrame


class BatteryResults(BaseModel, arbitrary_types_allowed=True):
    """Class to store battery results."""

    net_power: pd.DataFrame
    state_of_charge: pd.DataFrame
