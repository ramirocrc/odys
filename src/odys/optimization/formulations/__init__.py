"""Model formulations, one per entity type."""

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
