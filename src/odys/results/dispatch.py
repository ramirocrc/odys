"""Typed dispatch results for assets and markets."""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from typing import Any, Self, cast

import pandas as pd
import xarray as xr

from odys.results.schema import DIM_CHARGER, DIM_EV


class _DispatchBase:
    """Shared indexing / conversion helpers for asset dispatch views."""

    __slots__ = ("_arrays", "_dim", "_names")

    def __init__(self, arrays: Mapping[str, xr.DataArray], *, dim: str) -> None:
        self._arrays = dict(arrays)
        self._dim = dim
        first = next(iter(self._arrays.values()))
        self._names = first.coords[dim]

    def _select(self, key: str) -> dict[str, xr.DataArray]:
        return {name: array.sel({self._dim: key}) for name, array in self._arrays.items()}

    def __getitem__(self, key: str) -> Self:
        # Subclass __init__ takes named DataArray kwargs, not the base signature.
        ctor: Any = type(self)
        return cast("Self", ctor(**self._select(key)))

    def __iter__(self) -> Iterator[Self]:
        for name in self._names:
            yield self[cast("Any", name)]

    def __len__(self) -> int:
        return len(self._names)

    def __contains__(self, key: object) -> bool:
        return key in self._names

    def _series(self, name: str) -> pd.Series:
        return self._arrays[name].to_series()

    def to_dataset(self) -> xr.Dataset:
        """Return dispatch results as an xarray Dataset."""
        return xr.Dataset(data_vars=dict(self._arrays))

    def to_dataframe(self) -> pd.DataFrame:
        """Return dispatch results as a pandas DataFrame."""
        return self.to_dataset().to_dataframe()

    def __repr__(self) -> str:
        return f"{type(self).__name__}(names={self._names!r})"


class GeneratorDispatch(_DispatchBase):
    """Dispatch results for generators in the portfolio."""

    __slots__ = ()

    def __init__(
        self,
        power: xr.DataArray,
        status: xr.DataArray,
        startup: xr.DataArray,
        shutdown: xr.DataArray,
    ) -> None:
        """Initialize generator dispatch results."""
        super().__init__(
            {"power": power, "status": status, "startup": startup, "shutdown": shutdown},
            dim="generator",
        )

    @property
    def power(self) -> pd.Series:
        """Power output (MWh)."""
        return self._series("power")

    @property
    def status(self) -> pd.Series:
        """Binary on/off status."""
        return self._series("status")

    @property
    def startup(self) -> pd.Series:
        """Binary startup event."""
        return self._series("startup")

    @property
    def shutdown(self) -> pd.Series:
        """Binary shutdown event."""
        return self._series("shutdown")


class StandaloneStorageDispatch(_DispatchBase):
    """Dispatch results for standalone storages in the portfolio."""

    __slots__ = ()

    def __init__(
        self,
        net_power: xr.DataArray,
        soc: xr.DataArray,
        charge_mode: xr.DataArray,
    ) -> None:
        """Initialize standalone storage dispatch results."""
        super().__init__(
            {"net_power": net_power, "soc": soc, "charge_mode": charge_mode},
            dim="standalone_storage",
        )

    @property
    def net_power(self) -> pd.Series:
        """Net power (discharging - charging)."""
        return self._series("net_power")

    @property
    def soc(self) -> pd.Series:
        """State of charge (MWh)."""
        return self._series("soc")

    @property
    def charge_mode(self) -> pd.Series:
        """Binary charge mode (1=charging, 0=discharging)."""
        return self._series("charge_mode")


class ElectricVehicleDispatch(_DispatchBase):
    """Dispatch results for electric vehicles in the portfolio."""

    __slots__ = ()

    def __init__(
        self,
        net_power: xr.DataArray,
        soc: xr.DataArray,
        charge_mode: xr.DataArray,
    ) -> None:
        """Initialize electric vehicle dispatch results."""
        super().__init__(
            {"net_power": net_power, "soc": soc, "charge_mode": charge_mode},
            dim="ev",
        )

    @property
    def net_power(self) -> pd.Series:
        """Net power (discharging - charging)."""
        return self._series("net_power")

    @property
    def soc(self) -> pd.Series:
        """State of charge (MWh)."""
        return self._series("soc")

    @property
    def charge_mode(self) -> pd.Series:
        """Binary charge mode (1=charging, 0=discharging)."""
        return self._series("charge_mode")


class ChargerDispatch:
    """Dispatch results for chargers in the portfolio."""

    __slots__ = (
        "_assignment",
        "_charger_names",
        "_ev_names",
        "_power_in",
    )

    def __init__(
        self,
        assignment: xr.DataArray,
        power_in: xr.DataArray,
    ) -> None:
        """Initialize charger dispatch results."""
        self._assignment = assignment
        self._power_in = power_in
        self._charger_names = assignment.coords[DIM_CHARGER]
        self._ev_names = assignment.coords[DIM_EV]

    def __getitem__(self, key: str) -> ChargerDispatch:
        """Return new instance for a specific charger."""
        return ChargerDispatch(
            assignment=self._assignment.sel(charger=key),
            power_in=self._power_in.sel(ev=self._ev_names),
        )

    def __iter__(self) -> Iterator[ChargerDispatch]:
        """Iterate over dispatch instances."""
        for name in self._charger_names:
            yield self[name]

    def __len__(self) -> int:
        """Number of chargers."""
        return len(self._charger_names)

    def __contains__(self, key: object) -> bool:
        """Check if charger exists by name."""
        return key in self._charger_names

    @property
    def assignment(self) -> pd.Series:
        """Binary assignment (1=connected)."""
        return self._assignment.to_series()

    @property
    def power(self) -> pd.Series:
        """Power delivered by each charger (MWh)."""
        return (self._assignment * self._power_in).sum(DIM_EV).to_series()

    def to_dataset(self) -> xr.Dataset:
        """Return dispatch results as an xarray Dataset."""
        return xr.Dataset(
            data_vars={
                "assignment": self._assignment,
                "power": (self._assignment * self._power_in).sum(DIM_EV),
            },
        )

    def to_dataframe(self) -> pd.DataFrame:
        """Return dispatch results as a pandas DataFrame."""
        return self.to_dataset().to_dataframe()

    def __repr__(self) -> str:
        """String representation."""
        return f"ChargerDispatch(names={self._charger_names!r})"


class MarketDispatch(_DispatchBase):
    """Dispatch results for markets in the portfolio."""

    __slots__ = ()

    def __init__(
        self,
        sell_volume: xr.DataArray,
        buy_volume: xr.DataArray,
    ) -> None:
        """Initialize market dispatch results."""
        super().__init__(
            {"sell_volume": sell_volume, "buy_volume": buy_volume},
            dim="market",
        )

    @property
    def sell_volume(self) -> pd.Series:
        """Sell volume (MWh)."""
        return self._series("sell_volume")

    @property
    def buy_volume(self) -> pd.Series:
        """Buy volume (MWh)."""
        return self._series("buy_volume")

    @property
    def net_volume(self) -> xr.DataArray:
        """Net volume (sell - buy)."""
        return self._arrays["sell_volume"] - self._arrays["buy_volume"]

    def to_dataset(self) -> xr.Dataset:
        """Return dispatch results as an xarray Dataset."""
        return xr.Dataset(
            data_vars={
                "sell_volume": self._arrays["sell_volume"],
                "buy_volume": self._arrays["buy_volume"],
                "net_volume": self.net_volume,
            },
        )


class FlexibleLoadDispatch(_DispatchBase):
    """Dispatch results for flexible loads in the portfolio."""

    __slots__ = ("_base_profiles",)

    def __init__(
        self,
        load_adjustment: xr.DataArray,
        base_profiles: xr.DataArray,
    ) -> None:
        """Initialize flexible load dispatch results."""
        super().__init__({"load_adjustment": load_adjustment}, dim="flexible_load")
        self._base_profiles = base_profiles

    def __getitem__(self, key: str) -> FlexibleLoadDispatch:
        """Return new instance for a specific flexible load."""
        return FlexibleLoadDispatch(
            load_adjustment=self._arrays["load_adjustment"].sel(flexible_load=key),
            base_profiles=self._base_profiles.sel(flexible_load=key),
        )

    @property
    def load_adjustment(self) -> pd.Series:
        """Load adjustment from base profile (MW)."""
        return self._series("load_adjustment")

    @property
    def actual_load(self) -> pd.Series:
        """Actual consumption = base profile + adjustment (MW)."""
        return (self._base_profiles + self._arrays["load_adjustment"]).to_series()

    def to_dataset(self) -> xr.Dataset:
        """Return dispatch results as an xarray Dataset."""
        return xr.Dataset(
            data_vars={
                "load_adjustment": self._arrays["load_adjustment"],
                "actual_load": self._base_profiles + self._arrays["load_adjustment"],
            },
        )
