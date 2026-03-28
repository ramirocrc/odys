"""Asset portfolio management for energy systems.

This module provides the AssetPortfolio class for managing collections
of energy system assets including generators, storages, and other components.
"""

from collections import Counter
from collections.abc import Iterable
from types import MappingProxyType
from typing import TypeVar

from odys.energy_system_models.assets.base import EnergyAsset
from odys.energy_system_models.assets.generator import Generator
from odys.energy_system_models.assets.load import Load
from odys.energy_system_models.assets.storage import Storage
from odys.exceptions import OdysValidationError

T = TypeVar("T", bound=EnergyAsset)


class AssetPortfolio:
    """A collection of energy system assets.

    This class manages a portfolio of energy assets including generators,
    storages, and other energy system components. It provides methods
    to add, retrieve, and filter assets by type.
    """

    def __init__(self, assets: Iterable[EnergyAsset] | None = None) -> None:
        """Initialize an empty asset portfolio."""
        self._assets: dict[str, EnergyAsset] = {}
        if assets:
            self.add_assets(assets)

    def add_assets(self, assets: EnergyAsset | Iterable[EnergyAsset]) -> None:
        """Add a energy assets to the portfolio.

        Args:
            assets: The energy assets to add to the portfolio.

        Raises:
            OdysValidationError: If an asset with the same name already exists.

        """
        if isinstance(assets, EnergyAsset):
            self._add_single_asset(assets)
            return

        self._validate_unique_asset_names(assets)

        for asset in assets:
            self._add_single_asset(asset)

    def _add_single_asset(self, asset: EnergyAsset) -> None:
        if asset.name in self._assets:
            msg = f"Asset with name '{asset.name}' already exists."
            raise OdysValidationError(msg)
        self._assets[asset.name] = asset

    def get_asset(self, name: str) -> EnergyAsset:
        """Retrieve an asset from the portfolio by name.

        Args:
            name: The name of the asset to retrieve.

        Returns:
            The energy asset with the specified name.

        Raises:
            KeyError: If no asset with the specified name exists.

        """
        if name not in self._assets:
            msg = f"Asset with name '{name}' does not exist."
            raise OdysValidationError(msg)
        return self._assets[name]

    def _get_assets_by_type(self, asset_type: type[T]) -> tuple[T, ...]:
        return tuple(asset for asset in self._assets.values() if isinstance(asset, asset_type))

    def _validate_unique_asset_names(self, assets: Iterable[EnergyAsset]) -> None:
        names_count = Counter(asset.name for asset in assets)
        duplicates = [name for name, count in names_count.items() if count > 1]
        if duplicates:
            msg = f"Duplicate asset names in input: {duplicates}"
            raise OdysValidationError(msg)

    @property
    def assets(self) -> MappingProxyType[str, EnergyAsset]:
        """Get a read-only view of all assets in the portfolio.

        Returns:
            A mapping proxy containing all assets indexed by name.

        """
        return MappingProxyType(self._assets)

    @property
    def generators(self) -> tuple[Generator, ...]:
        """Get all generators in the portfolio.

        Returns:
            A tuple containing all Generator assets.

        """
        return self._get_assets_by_type(Generator)

    @property
    def storages(self) -> tuple[Storage, ...]:
        """Get all storages in the portfolio.

        Returns:
            A tuple containing all Storage assets.

        """
        return self._get_assets_by_type(Storage)

    @property
    def loads(self) -> tuple[Load, ...]:
        """Get all the loads in the portfolio.

        Returns:
            A tuple containing all Load assets.

        """
        return self._get_assets_by_type(Load)
