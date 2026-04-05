from collections.abc import Sequence
from datetime import timedelta

from odys.energy_system_models.assets.portfolio import AssetPortfolio
from odys.energy_system_models.markets import EnergyMarket
from odys.energy_system_models.scenarios import StochasticScenario
from odys.math_model.model_components.parameters.generator_parameters import GeneratorParameters
from odys.math_model.model_components.parameters.load_parameters import LoadParameters
from odys.math_model.model_components.parameters.market_parameters import MarketParameters
from odys.math_model.model_components.parameters.parameters import EnergySystemParameters
from odys.math_model.model_components.parameters.scenario_parameters import ScenarioParameters
from odys.math_model.model_components.parameters.storage_parameters import StorageParameters
from odys.optimization.objective import Objective


def build_parameters(
    portfolio: AssetPortfolio,
    markets: Sequence[EnergyMarket],
    timestep: timedelta,
    number_of_steps: int,
    scenarios: Sequence[StochasticScenario],
    objective: Objective,
) -> EnergySystemParameters:
    """Build parameters suitable for the optimization model.

    Args:
        portfolio: The asset portfolio containing generators, storages, and loads.
        markets: Sequence of energy markets.
        timestep: Duration of each time period.
        number_of_steps: Number of time steps in the optimization horizon.
        scenarios: Sequence of stochastic scenarios.
        objective: Objective function configuration.

    Returns:
        EnergySystemParameters suitable for building an optimization model.

    """
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
