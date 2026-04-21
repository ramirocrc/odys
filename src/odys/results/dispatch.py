"""Typed dispatch results for assets and markets."""

from __future__ import annotations

from collections.abc import Iterator

import pandas as pd
import xarray as xr

from odys.optimization.model.sets import ModelDimension


class GeneratorDispatch:
    """Dispatch results for a single generator asset."""

    __slots__ = ("_name", "_power", "_shutdown", "_startup", "_status")

    def __init__(
        self,
        name: str,
        power: xr.DataArray,
        status: xr.DataArray,
        startup: xr.DataArray,
        shutdown: xr.DataArray,
    ) -> None:
        """Initialize generator dispatch results."""
        self._name = name
        self._power = power
        self._status = status
        self._startup = startup
        self._shutdown = shutdown

    @property
    def name(self) -> str:
        """Generator name."""
        return self._name

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
        return f"GeneratorDispatch(name={self._name!r})"


class GeneratorsDispatch:
    """Dispatch results for all generators in the portfolio."""

    __slots__ = ("_generator_names", "_power", "_shutdown", "_startup", "_status")

    def __init__(
        self,
        power: xr.DataArray,
        status: xr.DataArray,
        startup: xr.DataArray,
        shutdown: xr.DataArray,
    ) -> None:
        """Initialize generators dispatch."""
        self._power = power
        self._status = status
        self._startup = startup
        self._shutdown = shutdown
        self._generator_names = list(power.coords[ModelDimension.Generators].to_numpy())

    def __getitem__(self, key: str | int) -> GeneratorDispatch:
        """Get dispatch for a specific generator by name or index."""
        if isinstance(key, int):
            key = self._generator_names[key]
        return GeneratorDispatch(
            name=key,
            power=self._power.sel(generator=key, drop=True),
            status=self._status.sel(generator=key, drop=True),
            startup=self._startup.sel(generator=key, drop=True),
            shutdown=self._shutdown.sel(generator=key, drop=True),
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

    def __repr__(self) -> str:
        """String representation."""
        return f"GeneratorsDispatch(names={self._generator_names!r})"

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


class StorageDispatch:
    """Dispatch results for a single storage asset."""

    __slots__ = ("_charge_mode", "_name", "_net_power", "_soc")

    def __init__(
        self,
        name: str,
        net_power: xr.DataArray,
        soc: xr.DataArray,
        charge_mode: xr.DataArray,
    ) -> None:
        """Initialize storage dispatch results."""
        self._name = name
        self._net_power = net_power
        self._soc = soc
        self._charge_mode = charge_mode

    @property
    def name(self) -> str:
        """Storage name."""
        return self._name

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
        return f"StorageDispatch(name={self._name!r})"


class StoragesDispatch:
    """Dispatch results for all storages in the portfolio."""

    __slots__ = ("_charge_mode", "_net_power", "_soc", "_storage_names")

    def __init__(
        self,
        net_power: xr.DataArray,
        soc: xr.DataArray,
        charge_mode: xr.DataArray,
    ) -> None:
        """Initialize storages dispatch."""
        self._net_power = net_power
        self._soc = soc
        self._charge_mode = charge_mode
        self._storage_names = list(net_power.coords[ModelDimension.Storages].to_numpy())

    def __getitem__(self, key: str | int) -> StorageDispatch:
        """Get dispatch for a specific storage by name or index."""
        if isinstance(key, int):
            key = self._storage_names[key]
        return StorageDispatch(
            name=key,
            net_power=self._net_power.sel(storage=key, drop=True),
            soc=self._soc.sel(storage=key, drop=True),
            charge_mode=self._charge_mode.sel(storage=key, drop=True),
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

    def __repr__(self) -> str:
        """String representation."""
        return f"StoragesDispatch(names={self._storage_names!r})"

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


class MarketDispatch:
    """Dispatch results for a single market."""

    __slots__ = ("_buy_volume", "_name", "_sell_volume")

    def __init__(
        self,
        name: str,
        sell_volume: xr.DataArray,
        buy_volume: xr.DataArray,
    ) -> None:
        """Initialize market dispatch results."""
        self._name = name
        self._sell_volume = sell_volume
        self._buy_volume = buy_volume

    @property
    def name(self) -> str:
        """Market name."""
        return self._name

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
        return f"MarketDispatch(name={self._name!r})"


class MarketsDispatch:
    """Dispatch results for all markets."""

    __slots__ = ("_buy_volume", "_market_names", "_sell_volume")

    def __init__(self, sell_volume: xr.DataArray, buy_volume: xr.DataArray) -> None:
        """Initialize markets dispatch."""
        self._sell_volume = sell_volume
        self._buy_volume = buy_volume
        self._market_names = list(sell_volume.coords[ModelDimension.Markets].to_numpy())

    def __getitem__(self, key: str | int) -> MarketDispatch:
        """Get dispatch for a specific market by name or index."""
        if isinstance(key, int):
            key = self._market_names[key]
        return MarketDispatch(
            name=key,
            sell_volume=self._sell_volume.sel(market=key, drop=True),
            buy_volume=self._buy_volume.sel(market=key, drop=True),
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

    def __repr__(self) -> str:
        """String representation."""
        return f"MarketsDispatch(names={self._market_names!r})"

    def to_dataset(self) -> xr.Dataset:
        """Return dispatch results as an xarray Dataset."""
        return xr.Dataset(
            data_vars={
                "sell_volume": self._sell_volume,
                "buy_volume": self._buy_volume,
                "net_volume": self._sell_volume - self._buy_volume,
            },
        )

    def to_dataframe(self) -> pd.DataFrame:
        """Return dispatch results as a pandas DataFrame."""
        return self.to_dataset().to_dataframe()
