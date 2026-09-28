"""Model dimension coordinates for the optimization model."""

from abc import ABC

from pydantic import BaseModel, ConfigDict

from odys.optimization.model.dimensions import ModelDimension


class ModelCoordinates(BaseModel, ABC):
    """Coordinate labels along a single model dimension."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
    )

    dimension: ModelDimension
    values: tuple[str, ...]

    @property
    def dimension_coordinates_map(self) -> dict[str, list[str]]:
        """Return xarray coordinate mapping for this dimension."""
        return {f"{self.dimension}": list(self.values)}


class CoordinatesStore(BaseModel):
    """Collection of all dimension coordinates used in the optimization model.

    Time and scenario coordinates are always present. Asset coordinates are present
    only when the corresponding asset type exists in the portfolio.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    scenarios: ModelCoordinates
    time: ModelCoordinates
    generators: ModelCoordinates | None = None
    standalone_storages: ModelCoordinates | None = None
    flexible_loads: ModelCoordinates | None = None
    markets: ModelCoordinates | None = None
    chargers: ModelCoordinates | None = None
    electric_vehicles: ModelCoordinates | None = None

    def get_coordinates(self, dimension: ModelDimension) -> ModelCoordinates:
        """Return the coordinates for a given dimension.

        Raises:
            KeyError: If the dimension has no coordinates (asset type absent).
        """
        mapping: dict[ModelDimension, ModelCoordinates | None] = {
            ModelDimension.Scenarios: self.scenarios,
            ModelDimension.Time: self.time,
            ModelDimension.Generators: self.generators,
            ModelDimension.StandaloneStorages: self.standalone_storages,
            ModelDimension.FlexibleLoads: self.flexible_loads,
            ModelDimension.Markets: self.markets,
            ModelDimension.Chargers: self.chargers,
            ModelDimension.EVs: self.electric_vehicles,
        }
        coords = mapping[dimension]
        if coords is None:
            msg = f"No coordinates for dimension {dimension!r}"
            raise KeyError(msg)
        return coords
