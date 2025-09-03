from abc import ABC, abstractmethod
from typing import ClassVar, Self

import numpy as np
from pydantic import BaseModel, field_validator, model_validator

from optimes._math_model.model_components.sets import EnergyModelDimension, EnergyModelSet
from optimes._math_model.model_components.variable_names import EnergyModelVariableName


class SystemVariable(ABC, BaseModel, arbitrary_types_allowed=True, extra="forbid"):
    name: ClassVar[EnergyModelVariableName]
    asset_dimension: ClassVar[EnergyModelDimension]
    time_set: EnergyModelSet
    asset_set: EnergyModelSet
    binary: ClassVar[bool]

    @field_validator("time_set", mode="before")
    @classmethod
    def validate_time_dimension(cls, v: EnergyModelSet) -> EnergyModelSet:
        if v.dimension != EnergyModelDimension.Time:
            msg = f"time_set should have time dimension, got {v.dimension}"
            raise ValueError(msg)
        return v

    @model_validator(mode="after")
    def validate_asset_dimension(self) -> Self:
        if self.asset_set.dimension != self.asset_dimension:
            msg = f"asset_set should have dimension {self.asset_dimension}, got {self.asset_set.dimension}"
            raise ValueError(msg)
        return self

    @property
    def coords(self) -> dict:
        return self.time_set.coordinates | self.asset_set.coordinates

    @property
    def dims(self) -> list[str]:
        return [self.time_set.dimension.value, self.asset_set.dimension.value]

    @property
    def _shape(self) -> tuple[int, int]:
        """Return the shape (time_steps, assets) for this variable."""
        return len(self.time_set.values), len(self.asset_set.values)

    def _create_zero_bounds(self) -> np.ndarray:
        """Create a zero bounds matrix."""
        return np.zeros(self._shape, dtype=float)

    def _create_infinite_lower_bound(self) -> np.ndarray:
        """Create unbounded bounds matrix."""
        return np.full(self._shape, -np.inf, dtype=float)

    @property
    @abstractmethod
    def lower(self) -> np.ndarray | float:
        """Return lower bounds as 2D numpy array or scalar for binary variables."""
