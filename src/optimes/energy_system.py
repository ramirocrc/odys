"""Model optimizer for energy system optimization.

This module provides the EnergySystemOptimizer class for solving
energy system optimization problems.
"""

from datetime import timedelta

from optimes._math_model.model_builder import EnergyAlgebraicModelBuilder
from optimes.energy_system_models.assets.portfolio import AssetPortfolio
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
        scenarios: Scenario | list[StochasticScenario],
        *,
        enforce_non_anticipativity: bool = False,
    ) -> None:
        """Initialize the energy system configuration and optimizer.

        Args:
            portfolio: The portfolio of energy assets (generators, batteries, etc.).
            demand_profile: Sequence of power demand values for each time period.
            timestep: Duration of each time period.
            number_of_steps: Number of time steps.
            power_unit: Unit used for power quantities ('W', 'kW', or 'MW').
            available_capacity_profiles: Optional dict mapping generator names to
            scenarios: Sequence of stochastic scenarios. Probabilities must add up to 1.
            enforce_non_anticipativity: When True, decision variables must take the same values across all scenarios,
            reflecting that decisions are made before uncertainty is revealed. When False, scenarios are optimized
            separately allowing different decisions per scenario.

        """
        self._validated_model = ValidatedEnergySystem(
            portfolio=portfolio,
            timestep=timestep,
            number_of_steps=number_of_steps,
            power_unit=power_unit,  # pyright: ignore reportArgumentType
            scenarios=scenarios,
            enforce_non_anticipativity=enforce_non_anticipativity,
        )

    def optimize(
        self,
    ) -> OptimizationResults:
        """Optimize the energy system.

        This method solves the pre-built algebraic model using HiGHS solver.
        The model is built during optimization from the energy system configuration.

        Returns:
            OptimizationResults containing the solution and metadata.

        """
        model_builder = EnergyAlgebraicModelBuilder(
            energy_system_parameters=self._validated_model.parameters,
        )
        linopy_model = model_builder.build()
        return optimize_algebraic_model(linopy_model)
