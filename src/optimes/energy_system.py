"""Model optimizer for energy system optimization.

This module provides the EnergySystemOptimizer class for solving
energy system optimization problems.
"""

from collections.abc import Sequence
from datetime import timedelta

from optimes._math_model.model_builder import EnergyAlgebraicModelBuilder
from optimes.energy_system_models.assets.portfolio import AssetPortfolio
from optimes.energy_system_models.markets import EnergyMarket
from optimes.energy_system_models.scenarios import Scenario, StochasticScenario
from optimes.energy_system_models.validated_energy_system import ValidatedEnergySystem
from optimes.optimization.optimization_results import OptimizationResults
from optimes.solvers.highs_solver import optimize_algebraic_model
from optimes.utils.logging import get_logger

logger = get_logger(__name__)


class EnergySystem:
    """Energy system configuration and optimization orchestrator.

    This class provides a high-level interface for configuring and optimizing
    energy systems. It handles system validation, model building, and
    optimization execution through external solvers.
    """

    def __init__(  # noqa: PLR0913
        self,
        portfolio: AssetPortfolio,
        timestep: timedelta,
        number_of_steps: int,
        power_unit: str,
        scenarios: Scenario | Sequence[StochasticScenario],
        markets: EnergyMarket | Sequence[EnergyMarket] | None = None,
    ) -> None:
        """Initialize the energy system configuration and optimizer.

        Args:
            portfolio: The portfolio of energy assets (generators, batteries, etc.).
            timestep: Duration of each time period.
            number_of_steps: Number of time steps.
            power_unit: Unit used for power quantities ('W', 'kW', or 'MW').
            scenarios: Sequence of stochastic scenarios. Probabilities must add up to 1.
            markets: Optional energy markets in which assets can participate.

        """
        self._validated_model = ValidatedEnergySystem(
            portfolio=portfolio,
            markets=markets,
            timestep=timestep,
            number_of_steps=number_of_steps,
            power_unit=power_unit,  # pyright: ignore reportArgumentType
            scenarios=scenarios,
        )

    def optimize(self) -> OptimizationResults:
        """Optimize the energy system.

        This method solves the pre-built algebraic model using HiGHS solver.
        The model is built during optimization from the energy system configuration.

        Returns:
            OptimizationResults containing the solution and metadata.

        """
        model_builder = EnergyAlgebraicModelBuilder(
            energy_system_parameters=self._validated_model.energy_system_parameters,
        )
        milp_model = model_builder.build()
        return optimize_algebraic_model(milp_model)
