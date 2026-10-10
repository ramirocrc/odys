"""Model formulations, one per entity type."""

from collections.abc import Sequence

from odys.domain.entities.base import EnergyEntity
from odys.domain.exceptions import OdysValidationError
from odys.optimization.formulations.base import Formulation
from odys.optimization.formulations.charging import ChargingFormulation
from odys.optimization.formulations.electric_vehicle import ElectricVehicleFormulation
from odys.optimization.formulations.energy_market import EnergyMarketFormulation
from odys.optimization.formulations.fixed_load import FixedLoadFormulation
from odys.optimization.formulations.flexible_load import FlexibleLoadFormulation
from odys.optimization.formulations.generator import GeneratorFormulation
from odys.optimization.formulations.stationary_storage import StationaryStorageFormulation

FORMULATIONS: tuple[type[Formulation], ...] = (
    GeneratorFormulation,
    EnergyMarketFormulation,
    FixedLoadFormulation,
    FlexibleLoadFormulation,
    StationaryStorageFormulation,
    ElectricVehicleFormulation,
    ChargingFormulation,
)
"""Every entity type's formulation, in build and power-balance order (charging after electric vehicles).

The only per-type list in the model layer.
"""


def validate_entities_supported(entities: Sequence[EnergyEntity]) -> None:
    """Validate that a formulation models every entity's type.

    A bare `Asset` or a user-defined `Asset` subclass would otherwise be
    accepted and then silently left out of the model.

    Args:
        entities: Every asset and market of the system.

    Raises:
        OdysValidationError: If no formulation models an entity's type.

    """
    supported = tuple(formulation_type.entity_type for formulation_type in FORMULATIONS)
    for entity in entities:
        if not isinstance(entity, supported):
            names = ", ".join(entity_type.__name__ for entity_type in supported)
            msg = (
                f"Asset type {type(entity).__name__} is not supported by the optimizer: '{entity.name}'. "
                f"Supported types: {names}."
            )
            raise OdysValidationError(msg)
