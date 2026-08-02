"""Asset registry for the optimization model.

This module provides the AssetRegistry enum that centralizes all
registered asset types and their specifications.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Any, Protocol, TypeAlias, runtime_checkable

from odys.domain.entities.charger import Charger
from odys.domain.entities.electric_vehicle import ElectricVehicle
from odys.domain.entities.flexible_load import FlexibleLoad
from odys.domain.entities.generator import Generator
from odys.domain.entities.market import EnergyMarket
from odys.domain.entities.standalone_storage import StandaloneStorage
from odys.optimization.constraints.charger_constraints import ChargerConstraints
from odys.optimization.constraints.constraints_group import ConstraintGroup
from odys.optimization.constraints.electric_vehicle_constraints import ElectricVehicleConstraints
from odys.optimization.constraints.flexible_load_constraints import FlexibleLoadConstraints
from odys.optimization.constraints.generator_constraints import GeneratorConstraints
from odys.optimization.constraints.market_constraints import MarketConstraints
from odys.optimization.constraints.standalone_storage_constraints import StandaloneStorageConstraints
from odys.optimization.model.contributions.electric_vehicle import (
    electric_vehicle_power_balance_terms,
    electric_vehicle_profit_terms,
)
from odys.optimization.model.contributions.flexible_load import (
    flexible_load_power_balance_terms,
    flexible_load_profit_terms,
)
from odys.optimization.model.contributions.generator import (
    generator_power_balance_terms,
    generator_profit_terms,
)
from odys.optimization.model.contributions.market import (
    market_power_balance_terms,
    market_profit_terms,
)
from odys.optimization.model.contributions.standalone_storage import (
    standalone_storage_power_balance_terms,
    standalone_storage_profit_terms,
)
from odys.optimization.model.sets import ModelDimension
from odys.optimization.model.variables import (
    CHARGER_VARIABLES,
    EV_VARIABLES,
    FLEXIBLE_LOAD_VARIABLES,
    GENERATOR_VARIABLES,
    MARKET_VARIABLES,
    STANDALONE_STORAGE_VARIABLES,
    ModelVariable,
    VariableSpec,
)
from odys.optimization.parameters.charger_parameters import ChargerParameters
from odys.optimization.parameters.electric_vehicle_parameters import ElectricVehicleParameters
from odys.optimization.parameters.flexible_load_parameters import FlexibleLoadParameters
from odys.optimization.parameters.generator_parameters import GeneratorParameters
from odys.optimization.parameters.market_parameters import MarketParameters
from odys.optimization.parameters.standalone_storage_parameters import StandaloneStorageParameters

if TYPE_CHECKING:
    from odys.domain.entities.base import EnergyEntity
    from odys.optimization.model.sets import ModelIndex
    from odys.optimization.parameters.build_context import ParamBuildContext
    from odys.optimization.parameters.parameters import EnergySystemParameters

# Callables take (EnergyMILPModel, EnergySystemParameters); Any avoids importing milp_model here.
ConstraintGroupFactory: TypeAlias = Callable[..., ConstraintGroup]
PowerBalanceContributor: TypeAlias = Callable[..., Any]
ProfitContributor: TypeAlias = Callable[..., Any]


@runtime_checkable
class AssetParametersBlock(Protocol):
    """Minimal interface the builder needs from an asset parameter block."""

    @property
    def is_empty(self) -> bool:
        """Return True when this asset type is absent from the system."""
        ...

    @property
    def index(self) -> ModelIndex:
        """Return the model index for this asset type."""
        ...


@dataclass(frozen=True)
class AssetSpec:
    """Specification for a first-party registered asset type."""

    entity_class: type[EnergyEntity]
    parameter_class: type[Any]
    parameters_attr: str
    dimension: ModelDimension
    variables: tuple[ModelVariable | VariableSpec, ...]
    constraint_group: ConstraintGroupFactory
    power_balance_terms: PowerBalanceContributor | None = None
    profit_terms: ProfitContributor | None = None

    def parameters_of(self, system_parameters: EnergySystemParameters) -> AssetParametersBlock:
        """Return this asset's parameter block from system parameters."""
        return getattr(system_parameters, self.parameters_attr)

    def is_present(self, system_parameters: EnergySystemParameters) -> bool:
        """Return True when this asset should contribute variables/constraints/terms."""
        return not self.parameters_of(system_parameters).is_empty


class AssetRegistry(Enum):
    """Registry of all supported asset types."""

    GENERATOR = AssetSpec(
        entity_class=Generator,
        parameter_class=GeneratorParameters,
        parameters_attr="generators",
        dimension=ModelDimension.Generators,
        variables=tuple(GENERATOR_VARIABLES),
        constraint_group=GeneratorConstraints,
        power_balance_terms=generator_power_balance_terms,
        profit_terms=generator_profit_terms,
    )

    STANDALONE_STORAGE = AssetSpec(
        entity_class=StandaloneStorage,
        parameter_class=StandaloneStorageParameters,
        parameters_attr="standalone_storages",
        dimension=ModelDimension.StandaloneStorages,
        variables=tuple(STANDALONE_STORAGE_VARIABLES),
        constraint_group=StandaloneStorageConstraints,
        power_balance_terms=standalone_storage_power_balance_terms,
        profit_terms=standalone_storage_profit_terms,
    )

    MARKET = AssetSpec(
        entity_class=EnergyMarket,
        parameter_class=MarketParameters,
        parameters_attr="markets",
        dimension=ModelDimension.Markets,
        variables=tuple(MARKET_VARIABLES),
        constraint_group=MarketConstraints,
        power_balance_terms=market_power_balance_terms,
        profit_terms=market_profit_terms,
    )

    FLEXIBLE_LOAD = AssetSpec(
        entity_class=FlexibleLoad,
        parameter_class=FlexibleLoadParameters,
        parameters_attr="flexible_loads",
        dimension=ModelDimension.FlexibleLoads,
        variables=tuple(FLEXIBLE_LOAD_VARIABLES),
        constraint_group=FlexibleLoadConstraints,
        power_balance_terms=flexible_load_power_balance_terms,
        profit_terms=flexible_load_profit_terms,
    )

    CHARGER = AssetSpec(
        entity_class=Charger,
        parameter_class=ChargerParameters,
        parameters_attr="chargers",
        dimension=ModelDimension.Chargers,
        variables=tuple(CHARGER_VARIABLES),
        constraint_group=ChargerConstraints,
        # Coupling infrastructure only — no bus injection or direct economics.
        power_balance_terms=None,
        profit_terms=None,
    )

    ELECTRIC_VEHICLE = AssetSpec(
        entity_class=ElectricVehicle,
        parameter_class=ElectricVehicleParameters,
        parameters_attr="electric_vehicles",
        dimension=ModelDimension.EVs,
        variables=tuple(EV_VARIABLES),
        constraint_group=ElectricVehicleConstraints,
        power_balance_terms=electric_vehicle_power_balance_terms,
        profit_terms=electric_vehicle_profit_terms,
    )

    @property
    def spec(self) -> AssetSpec:
        """Get the asset specification for this registry member."""
        return self.value

    @classmethod
    def all_variables(cls) -> list[ModelVariable | VariableSpec]:
        """Get all variables from all registered asset types."""
        variables: list[ModelVariable | VariableSpec] = []
        for member in cls:
            variables.extend(member.spec.variables)
        return variables

    @classmethod
    def all_parameter_classes(cls) -> list[type[Any]]:
        """Get all parameter classes from registered asset types."""
        return [member.spec.parameter_class for member in cls]

    @classmethod
    def build_asset_parameter_blocks(cls, ctx: ParamBuildContext) -> dict[str, AssetParametersBlock]:
        """Build parameter blocks for every registered asset from a build context."""
        return {member.spec.parameters_attr: member.spec.parameter_class.build(ctx) for member in cls}

    @classmethod
    def get_by_dimension(cls, dimension: ModelDimension) -> AssetRegistry | None:
        """Get an asset registry member by its model dimension."""
        for member in cls:
            if member.spec.dimension == dimension:
                return member
        return None
