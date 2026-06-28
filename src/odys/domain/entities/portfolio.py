"""Asset portfolio management for energy systems.

This module provides the AssetPortfolio class for managing collections
of energy system assets including generators, storages, and other components.
"""

from collections import Counter
from collections.abc import Iterable
from types import MappingProxyType
from typing import TypeVar

from odys.domain.entities.base import EnergyEntity
from odys.domain.entities.generator import Generator
from odys.domain.entities.load import Load
from odys.domain.entities.storage import Storage
from odys.domain.exceptions import OdysValidationError
from odys.optimization.model.registry import AssetRegistry

T = TypeVar("T", bound=EnergyEntity)


class AssetPortfolio:
    """A collection of energy system assets.

    This class manages a portfolio of energy assets including generators,
    storages, and other energy system components. It provides methods
    to add, retrieve, and filter assets by type.
    """

    def __init__(self, assets: Iterable[EnergyEntity] | None = None) -> None:
        """Initialize an asset portfolio.

        Args:
            assets: Iterable of energy assets to add to the portfolio.

        Raises:
            OdysValidationError: If an asset with the same name already exists
                or if there are duplicate names in the input.
        """
        self._assets: dict[str, EnergyEntity] = {}
        if assets:
            self._validate_unique_asset_names(assets)
            for asset in assets:
                self._add_single_asset(asset)

    def _add_single_asset(self, asset: EnergyEntity) -> None:
        if asset.name in self._assets:
            msg = f"Asset with name '{asset.name}' already exists."
            raise OdysValidationError(msg)
        self._assets[asset.name] = asset

    def get_asset(self, name: str) -> EnergyEntity:
        """Retrieve an asset from the portfolio by name.

        Args:
            name: The name of the asset to retrieve.

        Returns:
            The energy asset with the specified name.

        Raises:
            OdysValidationError: If no asset with the specified name exists.

        """
        if name not in self._assets:
            msg = f"Asset with name '{name}' does not exist."
            raise OdysValidationError(msg)
        return self._assets[name]

    def _get_assets_by_type(self, asset_type: type[T]) -> tuple[T, ...]:
        return tuple(asset for asset in self._assets.values() if isinstance(asset, asset_type))

    def _validate_unique_asset_names(self, assets: Iterable[EnergyEntity]) -> None:
        names_count = Counter(asset.name for asset in assets)
        duplicates = [name for name, count in names_count.items() if count > 1]
        if duplicates:
            msg = f"Duplicate asset names in input: {duplicates}"
            raise OdysValidationError(msg)

    @property
    def assets(self) -> MappingProxyType[str, EnergyEntity]:
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

    def assets_by_type(self, asset_type: AssetRegistry) -> tuple[EnergyEntity, ...]:
        """Get all assets of a specific type from the portfolio.

        Args:
            asset_type: The asset registry member specifying the asset type.

        Returns:
            A tuple containing all assets of the specified type.

        """
        return self._get_assets_by_type(asset_type.spec.entity_class)
