"""Typed dispatch results for assets and markets."""

import pandas as pd
import xarray as xr

from odys.optimization.model.variables import ModelVariable


class GeneratorDispatch:
    """Dispatch results for a single generator asset."""

    def __init__(
        self,
        power: xr.DataArray,
        status: xr.DataArray,
        startup: xr.DataArray,
        shutdown: xr.DataArray,
    ) -> None:
        """Initialize generator dispatch results."""
        self._power = power
        self._status = status
        self._startup = startup
        self._shutdown = shutdown

    @property
    def power(self) -> xr.DataArray:
        """Power output (MWh)."""
        return self._power

    @property
    def status(self) -> xr.DataArray:
        """Binary on/off status."""
        return self._status

    @property
    def startup(self) -> xr.DataArray:
        """Binary startup event."""
        return self._startup

    @property
    def shutdown(self) -> xr.DataArray:
        """Binary shutdown event."""
        return self._shutdown

    def to_dataset(self) -> xr.Dataset:
        """Return dispatch results as an xarray Dataset."""
        return xr.Dataset(
            data_vars={
                ModelVariable.GENERATOR_POWER.var_name: self._power,
                ModelVariable.GENERATOR_STATUS.var_name: self._status,
                ModelVariable.GENERATOR_STARTUP.var_name: self._startup,
                ModelVariable.GENERATOR_SHUTDOWN.var_name: self._shutdown,
            },
        )

    def to_dataframe(self) -> pd.DataFrame:
        """Return dispatch results as a pandas DataFrame."""
        return self.to_dataset().to_dataframe()


class StorageDispatch:
    """Dispatch results for a single storage asset."""

    def __init__(
        self,
        net_power: xr.DataArray,
        soc: xr.DataArray,
        charge_mode: xr.DataArray,
    ) -> None:
        """Initialize storage dispatch results."""
        self._net_power = net_power
        self._soc = soc
        self._charge_mode = charge_mode

    @property
    def net_power(self) -> xr.DataArray:
        """Net power (discharging - charging)."""
        return self._net_power

    @property
    def soc(self) -> xr.DataArray:
        """State of charge (MWh)."""
        return self._soc

    @property
    def charge_mode(self) -> xr.DataArray:
        """Binary charge mode (1=charging, 0=discharging)."""
        return self._charge_mode

    def to_dataset(self) -> xr.Dataset:
        """Return dispatch results as an xarray Dataset."""
        return xr.Dataset(
            data_vars={
                "net_power": self._net_power,
                "soc": self._soc,
                "is_charging": self._charge_mode,
            },
        )

    def to_dataframe(self) -> pd.DataFrame:
        """Return dispatch results as a pandas DataFrame."""
        return self.to_dataset().to_dataframe()


class MarketDispatch:
    """Dispatch results for a single market."""

    def __init__(self, sell_volume: xr.DataArray, buy_volume: xr.DataArray) -> None:
        """Initialize market dispatch results."""
        self._sell_volume = sell_volume
        self._buy_volume = buy_volume

    @property
    def sell_volume(self) -> xr.DataArray:
        """Sell volume (MWh)."""
        return self._sell_volume

    @property
    def buy_volume(self) -> xr.DataArray:
        """Buy volume (MWh)."""
        return self._buy_volume

    @property
    def net_volume(self) -> xr.DataArray:
        """Net volume (sell - buy)."""
        return self._sell_volume - self._buy_volume

    def to_dataset(self) -> xr.Dataset:
        """Return dispatch results as an xarray Dataset."""
        return xr.Dataset(
            data_vars={
                "sell_volume": self._sell_volume,
                "buy_volume": self._buy_volume,
                "net_volume": self.net_volume,
            },
        )

    def to_dataframe(self) -> pd.DataFrame:
        """Return dispatch results as a pandas DataFrame."""
        return self.to_dataset().to_dataframe()
