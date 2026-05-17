"""Typed dispatch results for assets and markets."""

from __future__ import annotations

from collections.abc import Iterator

import pandas as pd
import xarray as xr

from odys.optimization.model.sets import ModelDimension


class GeneratorDispatch:
    """Dispatch results for generators in the portfolio."""

    __slots__ = (
        "_generator_names",
        "_power",
        "_shutdown",
        "_startup",
        "_status",
    )

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
        self._generator_names = power.coords[ModelDimension.Generators]

    def __getitem__(self, key: str) -> GeneratorDispatch:
        """Return new instance for a specific generator."""
        return GeneratorDispatch(
            power=self._power.sel(generator=key),
            status=self._status.sel(generator=key),
            startup=self._startup.sel(generator=key),
            shutdown=self._shutdown.sel(generator=key),
        )

    def __iter__(self) -> Iterator[GeneratorDispatch]:
        """Iterate over dispatch instances."""
        for name in self._generator_names:
            yield self[name]

    def __len__(self) -> int:
        """Number of generators."""
        return len(self._generator_names)

    def __contains__(self, key: str) -> bool:
        """Check if generator exists by name."""
        return key in self._generator_names

    @property
    def power(self) -> pd.Series:
        """Power output (MWh)."""
        return self._power.to_series()

    @property
    def status(self) -> pd.Series:
        """Binary on/off status."""
        return self._status.to_series()

    @property
    def startup(self) -> pd.Series:
        """Binary startup event."""
        return self._startup.to_series()

    @property
    def shutdown(self) -> pd.Series:
        """Binary shutdown event."""
        return self._shutdown.to_series()

    def to_dataset(self) -> xr.Dataset:
        """Return dispatch results as an xarray Dataset."""
        return xr.Dataset(
            data_vars={
                "power": self._power,
                "status": self._status,
                "startup": self._startup,
                "shutdown": self._shutdown,
            },
        )

    def to_dataframe(self) -> pd.DataFrame:
        """Return dispatch results as a pandas DataFrame."""
        return self.to_dataset().to_dataframe()

    def __repr__(self) -> str:
        """String representation."""
        return f"GeneratorDispatch(names={self._generator_names!r})"


class StorageDispatch:
    """Dispatch results for storages in the portfolio."""

    __slots__ = (
        "_charge_mode",
        "_net_power",
        "_soc",
        "_storage_names",
    )

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
        self._storage_names = net_power.coords[ModelDimension.Storages]

    def __getitem__(self, key: str) -> StorageDispatch:
        """Return new instance for a specific storage."""
        return StorageDispatch(
            net_power=self._net_power.sel(storage=key),
            soc=self._soc.sel(storage=key),
            charge_mode=self._charge_mode.sel(storage=key),
        )

    def __iter__(self) -> Iterator[StorageDispatch]:
        """Iterate over dispatch instances."""
        for name in self._storage_names:
            yield self[name]

    def __len__(self) -> int:
        """Number of storages."""
        return len(self._storage_names)

    def __contains__(self, key: str) -> bool:
        """Check if storage exists by name."""
        return key in self._storage_names

    @property
    def net_power(self) -> pd.Series:
        """Net power (discharging - charging)."""
        return self._net_power.to_series()

    @property
    def soc(self) -> pd.Series:
        """State of charge (MWh)."""
        return self._soc.to_series()

    @property
    def charge_mode(self) -> pd.Series:
        """Binary charge mode (1=charging, 0=discharging)."""
        return self._charge_mode.to_series()

    def to_dataset(self) -> xr.Dataset:
        """Return dispatch results as an xarray Dataset."""
        return xr.Dataset(
            data_vars={
                "net_power": self._net_power,
                "soc": self._soc,
                "charge_mode": self._charge_mode,
            },
        )

    def to_dataframe(self) -> pd.DataFrame:
        """Return dispatch results as a pandas DataFrame."""
        return self.to_dataset().to_dataframe()

    def __repr__(self) -> str:
        """String representation."""
        return f"StorageDispatch(names={self._storage_names!r})"


class MarketDispatch:
    """Dispatch results for markets in the portfolio."""

    __slots__ = (
        "_buy_volume",
        "_market_names",
        "_sell_volume",
    )

    def __init__(
        self,
        sell_volume: xr.DataArray,
        buy_volume: xr.DataArray,
    ) -> None:
        """Initialize market dispatch results."""
        self._sell_volume = sell_volume
        self._buy_volume = buy_volume
        self._market_names = sell_volume.coords[ModelDimension.Markets]

    def __getitem__(self, key: str) -> MarketDispatch:
        """Return new instance for a specific market."""
        return MarketDispatch(
            sell_volume=self._sell_volume.sel(market=key),
            buy_volume=self._buy_volume.sel(market=key),
        )

    def __iter__(self) -> Iterator[MarketDispatch]:
        """Iterate over dispatch instances."""
        for name in self._market_names:
            yield self[name]

    def __len__(self) -> int:
        """Number of markets."""
        return len(self._market_names)

    def __contains__(self, key: str) -> bool:
        """Check if market exists by name."""
        return key in self._market_names

    @property
    def sell_volume(self) -> pd.Series:
        """Sell volume (MWh)."""
        return self._sell_volume.to_series()

    @property
    def buy_volume(self) -> pd.Series:
        """Buy volume (MWh)."""
        return self._buy_volume.to_series()

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

    def __repr__(self) -> str:
        """String representation."""
        return f"MarketDispatch(names={self._market_names!r})"
