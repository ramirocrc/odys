"""Context for building asset parameter blocks from domain entities."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence
    from datetime import timedelta

    from odys.domain.entities.charger import Charger
    from odys.domain.entities.electric_vehicle import ElectricVehicle
    from odys.domain.entities.flexible_load import FlexibleLoad
    from odys.domain.entities.generator import Generator
    from odys.domain.entities.market import EnergyMarket
    from odys.domain.entities.standalone_storage import StandaloneStorage
    from odys.domain.objective import Objective
    from odys.domain.scenarios import StochasticScenario


@dataclass(frozen=True, slots=True)
class ParamBuildContext:
    """Entity sequences and horizon data for parameter construction.

    Entity-source policy (portfolio vs markets) is resolved when this context
    is created; asset parameter classes only read typed fields.
    """

    number_of_steps: int
    timestep: timedelta
    generators: Sequence[Generator]
    standalone_storages: Sequence[StandaloneStorage]
    flexible_loads: Sequence[FlexibleLoad]
    chargers: Sequence[Charger]
    electric_vehicles: Sequence[ElectricVehicle]
    markets: Sequence[EnergyMarket]
    scenarios: Sequence[StochasticScenario]
    objective: Objective
