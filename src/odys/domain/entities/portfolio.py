"""Asset portfolio management for energy systems.

This module provides the AssetPortfolio class, the collection of assets the
user owns and operates.
"""

from collections import Counter
from collections.abc import Iterable
from types import MappingProxyType
from typing import TypeVar

from odys.domain.entities.base import Asset
from odys.domain.exceptions import OdysValidationError

AssetT = TypeVar("AssetT", bound=Asset)


class AssetPortfolio:
    """A collection of assets the user owns and operates.

    Assets are indexed by name, which must be unique. Markets are not assets
    and are rejected; pass them to `EnergySystem` instead.
    """

    def __init__(
        self,
        assets: Iterable[Asset] | None = None,
    ) -> None:
        """Initialize an asset portfolio.

        Args:
            assets: Iterable of assets to add to the portfolio.

        Raises:
            OdysValidationError: If an entity is not an asset, or if names are not unique.
        """
        asset_list = tuple(assets or ())
        self._validate_only_assets(asset_list)
        self._validate_unique_asset_names(asset_list)
        self._assets: dict[str, Asset] = {asset.name: asset for asset in asset_list}

    def get_asset(self, name: str) -> Asset:
        """Retrieve an asset from the portfolio by name.

        Args:
            name: The name of the asset to retrieve.

        Returns:
            The asset with the specified name.

        Raises:
            OdysValidationError: If no asset with the specified name exists.

        """
        if name not in self._assets:
            msg = f"Asset with name '{name}' does not exist."
            raise OdysValidationError(msg)
        return self._assets[name]

    def assets_of(self, asset_type: type[AssetT]) -> tuple[AssetT, ...]:
        """Return all assets of the given type, in insertion order.

        Args:
            asset_type: The asset class to filter by (subclasses included).

        Returns:
            A tuple with every asset that is an instance of `asset_type`.
        """
        return tuple(asset for asset in self._assets.values() if isinstance(asset, asset_type))

    @property
    def assets(self) -> MappingProxyType[str, Asset]:
        """Get a read-only view of all assets in the portfolio.

        Returns:
            A mapping proxy containing all assets indexed by name.

        """
        return MappingProxyType(self._assets)

    @staticmethod
    def _validate_only_assets(entities: tuple[object, ...]) -> None:
        """Reject non-assets from callers that bypass type checking (hence `object`, not `Asset`)."""
        for entity in entities:
            if not isinstance(entity, Asset):
                name = getattr(entity, "name", repr(entity))
                msg = (
                    f"AssetPortfolio only accepts assets; got '{name}' of type {type(entity).__name__}. "
                    "Pass markets to EnergySystem(markets=...) instead."
                )
                raise OdysValidationError(msg)

    @staticmethod
    def _validate_unique_asset_names(assets: tuple[Asset, ...]) -> None:
        names_count = Counter(asset.name for asset in assets)
        duplicates = [name for name, count in names_count.items() if count > 1]
        if duplicates:
            msg = f"Duplicate asset names in input: {duplicates}"
            raise OdysValidationError(msg)
