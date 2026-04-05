from odys.energy_system_models.validated_energy_system import ValidatedEnergySystem
from odys.math_model.model_components.parameters.generator_parameters import GeneratorParameters
from odys.math_model.model_components.parameters.load_parameters import LoadParameters
from odys.math_model.model_components.parameters.market_parameters import MarketParameters
from odys.math_model.model_components.parameters.parameters import EnergySystemParameters
from odys.math_model.model_components.parameters.scenario_parameters import ScenarioParameters
from odys.math_model.model_components.parameters.storage_parameters import StorageParameters


def build_parameters(system: ValidatedEnergySystem) -> EnergySystemParameters:
    """Build parameters suitable for the optimization model.

    Args:
        system: The validated energy system configuration.

    Returns:
        EnergySystemParameters suitable for building an optimization model.

    """
    portfolio = system.portfolio
    markets = system.collection_of_markets
    timestep = system.timestep
    number_of_steps = system.number_of_steps
    scenarios = system.collection_of_scenarios
    objective = system.objective

    generator_params = GeneratorParameters.from_assets(portfolio.generators)
    storage_params = StorageParameters.from_assets(portfolio.storages)
    load_params = LoadParameters.from_assets(portfolio.loads)
    market_params = MarketParameters.from_assets(markets)

    scenario_params = ScenarioParameters(
        number_of_timesteps=number_of_steps,
        scenarios=scenarios,
        generators_index=generator_params.index if generator_params else None,
        storages_index=storage_params.index if storage_params else None,
        loads_index=load_params.index if load_params else None,
        markets_index=market_params.index if market_params else None,
    )

    return EnergySystemParameters(
        timestep=timestep,
        generators=generator_params,
        storages=storage_params,
        loads=load_params,
        markets=market_params,
        scenarios=scenario_params,
        objective=objective,
    )
