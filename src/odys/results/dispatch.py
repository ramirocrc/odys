"""Typed dispatch results for assets and markets."""

from collections.abc import Iterator
from typing import ClassVar, Self

import pandas as pd
import xarray as xr


class Dispatch:
    """Dispatch results of every entity of one type, indexed along that type's dimension.

    Wraps one dataset holding the type's series. `dispatch[name]` selects one entity,
    iterating yields one dispatch per entity, and subclasses expose each series as a
    typed property.
    """

    __slots__ = ("_data", "_dimension")

    label: ClassVar[str]

    def __init__(self, data: xr.Dataset, dimension: str) -> None:
        """Initialize from the series of the entities and the dimension they are indexed along.

        Args:
            data: One data variable per series, indexed along `dimension`.
            dimension: The entity axis, such as "generator".
        """
        self._data = data
        self._dimension = dimension

    @property
    def dimension(self) -> str:
        """Return the dimension the entities are indexed along."""
        return self._dimension

    @property
    def _names(self) -> xr.DataArray:
        return self._data.coords[self._dimension]

    def __getitem__(self, key: str) -> Self:
        """Return the dispatch of one entity."""
        return type(self)(self._data.sel({self._dimension: key}), self._dimension)

    def __iter__(self) -> Iterator[Self]:
        """Iterate over the dispatch of each entity."""
        for name in self._names.to_numpy():
            yield self[str(name)]

    def __len__(self) -> int:
        """Return the number of entities."""
        return len(self._names)

    def __contains__(self, key: str) -> bool:
        """Check whether an entity exists by name."""
        return key in self._names

    def _series(self, name: str) -> pd.Series:
        return self._data[name].to_series()

    def to_dataset(self) -> xr.Dataset:
        """Return the dispatch results as an xarray Dataset (a copy, so editing it leaves the results unchanged)."""
        data: xr.Dataset = self._data.copy(deep=True)
        return data

    def to_dataframe(self) -> pd.DataFrame:
        """Return the dispatch results as a pandas DataFrame."""
        return self._data.to_dataframe()

    def __repr__(self) -> str:
        """Return the type and the entity names."""
        return f"{type(self).__name__}(names={self._names!r})"


class GeneratorDispatch(Dispatch):
    """Dispatch results for generators in the portfolio."""

    __slots__ = ()
    label = "generator"

    @property
    def power(self) -> pd.Series:
        """Power output (MW)."""
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


class BatteryDispatch(Dispatch):
    """Dispatch results of battery-bearing entities: net power, state of charge and charge mode."""

    __slots__ = ()

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


class StationaryStorageDispatch(BatteryDispatch):
    """Dispatch results for stationary storages in the portfolio."""

    __slots__ = ()
    label = "stationary storage"


class ElectricVehicleDispatch(BatteryDispatch):
    """Dispatch results for electric vehicles in the portfolio."""

    __slots__ = ()
    label = "electric vehicle"


class ChargerDispatch(Dispatch):
    """Dispatch results for chargers in the portfolio."""

    __slots__ = ()
    label = "charger"

    @property
    def assignment(self) -> pd.Series:
        """Binary assignment of each electric vehicle (1=connected)."""
        return self._series("assignment")

    @property
    def power(self) -> pd.Series:
        """Power delivered by each charger (MW)."""
        return self._series("power")


class MarketDispatch(Dispatch):
    """Dispatch results for markets in the portfolio."""

    __slots__ = ()
    label = "market"

    @property
    def sell_volume(self) -> pd.Series:
        """Sell volume (MW)."""
        return self._series("sell_volume")

    @property
    def buy_volume(self) -> pd.Series:
        """Buy volume (MW)."""
        return self._series("buy_volume")

    @property
    def net_volume(self) -> pd.Series:
        """Net volume (sell - buy)."""
        return self._series("net_volume")


class FlexibleLoadDispatch(Dispatch):
    """Dispatch results for flexible loads in the portfolio."""

    __slots__ = ()
    label = "flexible load"

    @property
    def load_adjustment(self) -> pd.Series:
        """Load adjustment from base profile (MW)."""
        return self._series("load_adjustment")

    @property
    def actual_load(self) -> pd.Series:
        """Actual consumption = base profile + adjustment (MW)."""
        return self._series("actual_load")
