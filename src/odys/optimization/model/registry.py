"""Asset registry for the optimization model.

This module provides the AssetRegistry enum that centralizes all
registered asset types and their specifications.
"""

from dataclasses import dataclass
from enum import Enum

from odys.domain.entities.base import EnergyEntity
from odys.domain.entities.charger import Charger
from odys.domain.entities.electric_vehicle import ElectricVehicle
from odys.domain.entities.flexible_load import FlexibleLoad
from odys.domain.entities.generator import Generator
from odys.domain.entities.market import EnergyMarket
from odys.domain.entities.standalone_storage import StandaloneStorage
from odys.optimization.model.sets import ModelDimension
from odys.optimization.model.variables import (
    CHARGER_VARIABLES,
    EV_VARIABLES,
    FLEXIBLE_LOAD_VARIABLES,
    GENERATOR_VARIABLES,
    MARKET_VARIABLES,
    STANDALONE_STORAGE_VARIABLES,
    ModelVariable,
)
from odys.optimization.parameters.charger_parameters import ChargerParameters
from odys.optimization.parameters.electric_vehicle_parameters import ElectricVehicleParameters
from odys.optimization.parameters.flexible_load_parameters import FlexibleLoadParameters
from odys.optimization.parameters.generator_parameters import GeneratorParameters
from odys.optimization.parameters.market_parameters import MarketParameters
from odys.optimization.parameters.standalone_storage_parameters import StandaloneStorageParameters


@dataclass(frozen=True)
class AssetSpec:
    """Specification for a registered asset type."""

    entity_class: type[EnergyEntity]
    parameter_class: type[
        GeneratorParameters
        | StandaloneStorageParameters
        | MarketParameters
        | FlexibleLoadParameters
        | ChargerParameters
        | ElectricVehicleParameters
    ]
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

    STANDALONE_STORAGE = AssetSpec(
        entity_class=StandaloneStorage,
        parameter_class=StandaloneStorageParameters,
        dimension=ModelDimension.StandaloneStorages,
        variables=tuple(STANDALONE_STORAGE_VARIABLES),
    )

    MARKET = AssetSpec(
        entity_class=EnergyMarket,
        parameter_class=MarketParameters,
        dimension=ModelDimension.Markets,
        variables=tuple(MARKET_VARIABLES),
    )

    FLEXIBLE_LOAD = AssetSpec(
        entity_class=FlexibleLoad,
        parameter_class=FlexibleLoadParameters,
        dimension=ModelDimension.FlexibleLoads,
        variables=tuple(FLEXIBLE_LOAD_VARIABLES),
    )

    CHARGER = AssetSpec(
        entity_class=Charger,
        parameter_class=ChargerParameters,
        dimension=ModelDimension.Chargers,
        variables=tuple(CHARGER_VARIABLES),
    )

    ELECTRIC_VEHICLE = AssetSpec(
        entity_class=ElectricVehicle,
        parameter_class=ElectricVehicleParameters,
        dimension=ModelDimension.EVs,
        variables=tuple(EV_VARIABLES),
    )

    @property
    def spec(self) -> AssetSpec:
        """Get the asset specification for this registry member."""
        return self.value
