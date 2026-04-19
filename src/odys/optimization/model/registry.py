"""Asset registry for the optimization model.

This module provides the AssetRegistry enum that centralizes all
registered asset types and their specifications.
"""

from dataclasses import dataclass
from enum import Enum

from odys.domain.entities.base import EnergyEntity
from odys.domain.entities.generator import Generator
from odys.domain.entities.load import Load
from odys.domain.entities.market import EnergyMarket
from odys.domain.entities.storage import Storage
from odys.optimization.model.sets import ModelDimension
from odys.optimization.model.variables import (
    GENERATOR_VARIABLES,
    MARKET_VARIABLES,
    STORAGE_VARIABLES,
    ModelVariable,
)
from odys.optimization.parameters.generator_parameters import GeneratorParameters
from odys.optimization.parameters.load_parameters import LoadParameters
from odys.optimization.parameters.market_parameters import MarketParameters
from odys.optimization.parameters.storage_parameters import StorageParameters


@dataclass(frozen=True)
class AssetSpec:
    """Specification for a registered asset type."""

    entity_class: type[EnergyEntity]
    parameter_class: type[GeneratorParameters | StorageParameters | MarketParameters | LoadParameters]
    dimension: ModelDimension
    variables: tuple[ModelVariable, ...]


class AssetRegistry(Enum):
    """Registry of all supported asset types."""

    GENERATOR = AssetSpec(
        entity_class=Generator,
        parameter_class=GeneratorParameters,
        dimension=ModelDimension.Generators,
        variables=tuple(GENERATOR_VARIABLES),
    )

    STORAGE = AssetSpec(
        entity_class=Storage,
        parameter_class=StorageParameters,
        dimension=ModelDimension.Storages,
        variables=tuple(STORAGE_VARIABLES),
    )

    MARKET = AssetSpec(
        entity_class=EnergyMarket,
        parameter_class=MarketParameters,
        dimension=ModelDimension.Markets,
        variables=tuple(MARKET_VARIABLES),
    )

    LOAD = AssetSpec(
        entity_class=Load,
        parameter_class=LoadParameters,
        dimension=ModelDimension.Loads,
        variables=(),
    )

    @property
    def spec(self) -> AssetSpec:
        """Get the asset specification for this registry member."""
        return self.value

    @classmethod
    def all_variables(cls) -> list[ModelVariable]:
        """Get all variables from all registered asset types."""
        variables: list[ModelVariable] = []
        for member in cls:
            variables.extend(member.spec.variables)
        return variables

    @classmethod
    def all_parameter_classes(
        cls,
    ) -> list[type[GeneratorParameters | StorageParameters | MarketParameters | LoadParameters]]:
        """Get all parameter classes from registered asset types."""
        return [member.spec.parameter_class for member in cls]

    @classmethod
    def get_by_dimension(cls, dimension: ModelDimension) -> "AssetRegistry | None":
        """Get an asset registry member by its model dimension."""
        for member in cls:
            if member.spec.dimension == dimension:
                return member
        return None
