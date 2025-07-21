from typing import TypeVar

from optimes.energy_system.assets.base import EnergyAsset
from optimes.energy_system.assets.generator import PowerGenerator
from optimes.energy_system.assets.storage import Battery

T = TypeVar("T", bound=EnergyAsset)


class AssetPortfolio:
    def __init__(self) -> None:
        self._assets: dict[str, EnergyAsset] = {}

    def add_asset(self, asset: EnergyAsset) -> None:
        if asset.name in self._assets:
            msg = f"Asset with name '{asset.name}' already exists."
            raise ValueError(msg)
        if not isinstance(asset, EnergyAsset):
            msg = f"Expected an instance of EnergyAsset, got {type(asset)}."
            raise TypeError(msg)
        self._assets[asset.name] = asset

    def get_asset(self, name: str) -> EnergyAsset:
        if name not in self._assets:
            msg = f"Asset with name '{name}' does not exist."
            raise KeyError(msg)
        return self._assets[name]

    def get_assets_by_type(self, asset_type: type[T]) -> list[T]:
        return [asset for asset in self._assets.values() if isinstance(asset, asset_type)]

    @property
    def assets(self) -> list[EnergyAsset]:
        return list(self._assets.values())

    @property
    def generators(self) -> list[PowerGenerator]:
        return self.get_assets_by_type(PowerGenerator)

    @property
    def batteries(self) -> list[Battery]:
        return self.get_assets_by_type(Battery)
