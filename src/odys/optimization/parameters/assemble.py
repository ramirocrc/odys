"""Assemble EnergySystemParameters from a ParamBuildContext via the asset registry."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from odys.optimization.model.registry import AssetRegistry
from odys.optimization.parameters.parameters import EnergySystemParameters
from odys.optimization.parameters.scenario_parameters import ScenarioParameters

if TYPE_CHECKING:
    from odys.optimization.parameters.build_context import ParamBuildContext
    from odys.optimization.parameters.charger_parameters import ChargerParameters
    from odys.optimization.parameters.electric_vehicle_parameters import ElectricVehicleParameters
    from odys.optimization.parameters.flexible_load_parameters import FlexibleLoadParameters
    from odys.optimization.parameters.generator_parameters import GeneratorParameters
    from odys.optimization.parameters.market_parameters import MarketParameters
    from odys.optimization.parameters.standalone_storage_parameters import StandaloneStorageParameters


def build_energy_system_parameters(ctx: ParamBuildContext) -> EnergySystemParameters:
    """Build system parameters from context using registry asset factories."""
    blocks = AssetRegistry.build_asset_parameter_blocks(ctx)
    generators = cast("GeneratorParameters", blocks["generators"])
    standalone_storages = cast("StandaloneStorageParameters", blocks["standalone_storages"])
    flexible_loads = cast("FlexibleLoadParameters", blocks["flexible_loads"])
    markets = cast("MarketParameters", blocks["markets"])
    chargers = cast("ChargerParameters", blocks["chargers"])
    electric_vehicles = cast("ElectricVehicleParameters", blocks["electric_vehicles"])

    scenarios = ScenarioParameters(
        number_of_timesteps=ctx.number_of_steps,
        scenarios=ctx.scenarios,
        generators_index=generators.index,
        standalone_storages_index=standalone_storages.index,
        flexible_loads_index=flexible_loads.index,
        markets_index=markets.index,
    )
    return EnergySystemParameters(
        timestep=ctx.timestep,
        generators=generators,
        standalone_storages=standalone_storages,
        flexible_loads=flexible_loads,
        markets=markets,
        scenarios=scenarios,
        chargers=chargers,
        electric_vehicles=electric_vehicles,
        objective=ctx.objective,
    )
