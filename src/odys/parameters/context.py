"""The shared indexing of one optimization problem."""

from collections.abc import Sequence
from functools import cached_property
from typing import Self

import xarray as xr
from pydantic import BaseModel, ConfigDict, model_validator

from odys.domain.entities.base import EnergyEntity
from odys.domain.exceptions import OdysError
from odys.domain.horizon import Horizon
from odys.domain.profiles import Profile
from odys.domain.scenario import Scenario, ScenarioSet
from odys.parameters.coordinates import Coordinates
from odys.parameters.dimensions import ModelDimension


class ModelContext(BaseModel):
    """Shared indexing of one optimization problem.

    Holds the time and scenario coordinates, the step length, the scenario
    probabilities and the coordinates of every entity dimension, and turns
    scenario profiles into arrays. It is the only producer of time labels,
    which are strings ("0", "1", ...): arrays with integer time coordinates
    would align with nothing and silently mask every constraint using them.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    horizon: Horizon
    scenario_set: ScenarioSet
    entity_coordinates: tuple[Coordinates, ...] = ()

    @model_validator(mode="after")
    def _validate_one_coordinates_per_entity_dimension(self) -> Self:
        dimensions = [coordinates.dimension for coordinates in self.entity_coordinates]
        reserved = {ModelDimension.Time, ModelDimension.Scenarios}
        if len(dimensions) != len(set(dimensions)) or reserved & set(dimensions):
            msg = f"Entity coordinates need one entry per entity dimension, without time or scenario: {dimensions}."
            raise OdysError(msg)
        return self

    @cached_property
    def time(self) -> Coordinates:
        """Return the time coordinates, one string label per step."""
        return Coordinates(
            dimension=ModelDimension.Time,
            labels=tuple(str(step) for step in range(self.horizon.number_of_steps)),
        )

    @cached_property
    def scenarios(self) -> Coordinates:
        """Return the scenario coordinates, labelled by scenario name."""
        return Coordinates(dimension=ModelDimension.Scenarios, labels=self.scenario_set.names)

    @property
    def timestep_hours(self) -> float:
        """Return the length of one step in hours."""
        return self.horizon.hours_per_step

    @cached_property
    def probabilities(self) -> xr.DataArray:
        """Return the scenario probabilities along the scenario dimension."""
        return xr.DataArray(
            data=[scenario.probability for scenario in self.scenario_set.scenarios],
            coords=self.scenarios.dimension_coordinates_map,
        )

    def coordinates_of(self, dimension: ModelDimension) -> Coordinates:
        """Return the coordinates of a dimension.

        Args:
            dimension: The dimension to look up.

        Returns:
            The coordinates of that dimension.

        Raises:
            OdysError: If the problem has no coordinates for that dimension (no entity of that type).

        """
        if dimension not in self._coordinates_by_dimension:
            msg = f"The problem has no coordinates for dimension '{dimension}'."
            raise OdysError(msg)
        return self._coordinates_by_dimension[dimension]

    @cached_property
    def _coordinates_by_dimension(self) -> dict[ModelDimension, Coordinates]:
        all_coordinates = (self.time, self.scenarios, *self.entity_coordinates)
        return {coordinates.dimension: coordinates for coordinates in all_coordinates}

    def variable_coords(self, *entity_coordinates: Coordinates) -> dict[str, list[str]]:
        """Return the coordinates of a decision variable over scenario, time and the given entity dimensions.

        Args:
            entity_coordinates: The entity dimensions of the variable, in order.

        Returns:
            The xarray coordinate mapping, scenario first, then time, then the entity dimensions.

        """
        coords = self.scenarios.dimension_coordinates_map | self.time.dimension_coordinates_map
        for coordinates in entity_coordinates:
            coords |= coordinates.dimension_coordinates_map
        return coords

    def profiles(
        self,
        kind: type[Profile],
        entities: Sequence[EnergyEntity],
        dimension: ModelDimension,
        *,
        default: float | None = None,
    ) -> xr.DataArray:
        """Return the profiles of the given kind for the given entities, over scenario, entity and time.

        Args:
            kind: The profile type to read, such as `PriceProfile`.
            entities: The entities, in the order of their coordinates.
            dimension: The dimension the entities are indexed along.
            default: The value at every step for an entity without a profile in a scenario.

        Returns:
            An array with dimensions (scenario, `dimension`, time).

        Raises:
            OdysError: If an entity has no profile in a scenario and there is no default.

        """
        data = [
            [self._profile_values(scenario, kind, entity, default) for entity in entities]
            for scenario in self.scenario_set.scenarios
        ]
        return xr.DataArray(
            data=data,
            coords=(
                self.scenarios.dimension_coordinates_map
                | Coordinates.of_entities(dimension, entities).dimension_coordinates_map
                | self.time.dimension_coordinates_map
            ),
        )

    def _profile_values(
        self,
        scenario: Scenario,
        kind: type[Profile],
        entity: EnergyEntity,
        default: float | None,
    ) -> tuple[float, ...]:
        profile = next((profile for profile in scenario.profiles_of(kind) if profile.entity == entity), None)
        if profile is not None:
            return tuple(profile.values)
        if default is None:
            msg = f"Scenario '{scenario.name}' has no {kind.__name__} for '{entity.name}'."
            raise OdysError(msg)
        return (default,) * self.horizon.number_of_steps
