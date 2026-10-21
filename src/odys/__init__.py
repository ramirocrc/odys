"""Odys - Python framework for optimizing multi-energy systems.

This package provides tools for modeling and optimizing energy systems with generators,
storages, and other energy assets using mathematical optimization techniques.

"""

from importlib.metadata import version

from odys.domain.conditions import (
    ElectricVehicleFinalState,
    ElectricVehicleInitialState,
    GeneratorFinalState,
    GeneratorInitialState,
    StorageFinalState,
    StorageInitialState,
)
from odys.domain.entities.base import Asset
from odys.domain.entities.battery import Battery
from odys.domain.entities.battery_storage import BatteryStorage
from odys.domain.entities.charger import Charger
from odys.domain.entities.electric_vehicle import ElectricVehicle
from odys.domain.entities.fixed_load import FixedLoad
from odys.domain.entities.flexible_load import FlexibleLoad
from odys.domain.entities.generator import Generator
from odys.domain.entities.market import AllowedTradeDirection, EnergyMarket
from odys.domain.entities.portfolio import AssetPortfolio
from odys.domain.entities.trip import Trip
from odys.domain.exceptions import OdysError, OdysNoResultsError, OdysSolverError, OdysValidationError
from odys.domain.objective import CVaRTerm, Objective, ProfitTerm
from odys.domain.profiles import AvailableCapacityProfile, FlexibleLoadProfile, LoadProfile, PriceProfile
from odys.domain.scenario import Scenario
from odys.energy_system import EnergySystem
from odys.results.optimization_results import OptimalDispatchResults
from odys.solvers.outcome import SolveStatus
from odys.solvers.solver_config import SolverConfig, SolverName

__version__ = version("odys")

__all__ = [
    "AllowedTradeDirection",
    "Asset",
    "AssetPortfolio",
    "AvailableCapacityProfile",
    "Battery",
    "BatteryStorage",
    "CVaRTerm",
    "Charger",
    "ElectricVehicle",
    "ElectricVehicleFinalState",
    "ElectricVehicleInitialState",
    "EnergyMarket",
    "EnergySystem",
    "FixedLoad",
    "FlexibleLoad",
    "FlexibleLoadProfile",
    "Generator",
    "GeneratorFinalState",
    "GeneratorInitialState",
    "LoadProfile",
    "Objective",
    "OdysError",
    "OdysNoResultsError",
    "OdysSolverError",
    "OdysValidationError",
    "OptimalDispatchResults",
    "PriceProfile",
    "ProfitTerm",
    "Scenario",
    "SolveStatus",
    "SolverConfig",
    "SolverName",
    "StorageFinalState",
    "StorageInitialState",
    "Trip",
]
