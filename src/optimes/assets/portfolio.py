from optimes.assets.base import EnergyAsset
from optimes.assets.generator import PowerGenerator
from optimes.assets.storage import Battery


class AssetPortfolio:
    def __init__(self, assets: list[EnergyAsset] | None = None) -> None:
        self._assets = assets if assets else []

    @property
    def assets(self) -> list[EnergyAsset]:
        return self._assets

    def add_asset(self, asset: EnergyAsset) -> None:
        self._assets.append(asset)

    @property
    def generators(self) -> list[PowerGenerator]:
        return [g for g in self._assets if isinstance(g, PowerGenerator)]

    @property
    def batteries(self) -> list[Battery]:
        return [b for b in self.assets if isinstance(b, Battery)]
