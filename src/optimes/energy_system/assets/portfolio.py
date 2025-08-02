from types import MappingProxyType
from typing import TypeVar

from optimes.energy_system.assets.base import EnergyAsset
from optimes.energy_system.assets.generator import PowerGenerator
from optimes.energy_system.assets.storage import Battery

T = TypeVar("T", bound=EnergyAsset)


class AssetPortfolio:
    """A collection of energy system assets.

    This class manages a portfolio of energy assets including generators,
    batteries, and other energy system components. It provides methods
    to add, retrieve, and filter assets by type.
    """

    def __init__(self) -> None:
        """Initialize an empty asset portfolio."""
        self._assets: dict[str, EnergyAsset] = {}

    def add_asset(self, asset: EnergyAsset) -> None:
        """Add an energy asset to the portfolio.

        Args:
            asset: The energy asset to add to the portfolio.

        Raises:
            ValueError: If an asset with the same name already exists.
            TypeError: If the asset is not an instance of EnergyAsset.
        """
        if asset.name in self._assets:
            msg = f"Asset with name '{asset.name}' already exists."
            raise ValueError(msg)
        if not isinstance(asset, EnergyAsset):
            msg = f"Expected an instance of EnergyAsset, got {type(asset)}."
            raise TypeError(msg)
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
            raise KeyError(msg)
        return self._assets[name]

    def get_assets_by_type(self, asset_type: type[T]) -> tuple[T, ...]:
        """Get all assets of a specific type.

        Args:
            asset_type: The type of assets to retrieve.

        Returns:
            A tuple containing all assets of the specified type.
        """
        return tuple(asset for asset in self._assets.values() if isinstance(asset, asset_type))

    @property
    def assets(self) -> MappingProxyType:
        """Get a read-only view of all assets in the portfolio.

        Returns:
            A mapping proxy containing all assets indexed by name.
        """
        return MappingProxyType(self._assets)

    @property
    def generators(self) -> tuple[PowerGenerator, ...]:
        """Get all power generators in the portfolio.

        Returns:
            A tuple containing all PowerGenerator assets.
        """
        return self.get_assets_by_type(PowerGenerator)

    @property
    def batteries(self) -> tuple[Battery, ...]:
        """Get all batteries in the portfolio.

        Returns:
            A tuple containing all Battery assets.
        """
        return self.get_assets_by_type(Battery)
