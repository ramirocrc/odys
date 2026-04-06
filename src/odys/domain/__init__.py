"""Odys domain layer.

Contains pure domain logic with no external dependencies:
- Entities: Generator, Storage, Load, EnergyMarket
- Value objects: PowerUnit
- Domain services: Scenarios, Portfolio
- Exceptions: OdysError hierarchy
"""

from odys.domain.entities.base import EnergyAsset
from odys.domain.entities.generator import Generator
from odys.domain.entities.load import Load, LoadType
from odys.domain.entities.market import EnergyMarket, TradeDirection
from odys.domain.entities.portfolio import AssetPortfolio
from odys.domain.entities.storage import Storage
from odys.domain.exceptions import (
    OdysError,
    OdysNoResultsError,
    OdysSolverError,
    OdysValidationError,
)
from odys.domain.objective import CVaRTerm, Objective, ProfitTerm
from odys.domain.scenarios import Scenario, StochasticScenario
from odys.domain.units import PowerUnit

__all__ = [
    "AssetPortfolio",
    "CVaRTerm",
    "EnergyAsset",
    "EnergyMarket",
    "Generator",
    "Load",
    "LoadType",
    "Objective",
    "OdysError",
    "OdysNoResultsError",
    "OdysSolverError",
    "OdysValidationError",
    "PowerUnit",
    "ProfitTerm",
    "Scenario",
    "StochasticScenario",
    "Storage",
    "TradeDirection",
]
