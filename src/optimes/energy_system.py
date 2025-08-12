"""Model optimizer for energy system optimization.

This module provides the EnergySystemOptimizer class for solving
energy system optimization problems.
"""

from datetime import timedelta

from optimes._math_model.model_builder import EnergyAlgebraicModelBuilder
from optimes.energy_system_models.assets.portfolio import AssetPortfolio
from optimes.energy_system_models.validated_energy_system import ValidatedEnergySystem
from optimes.optimization.optimization_results import OptimizationResults
from optimes.solvers.base_solver import AlgebraicModelSolver
from optimes.solvers.highs_solver import HiGHSolver
from optimes.utils.logging import get_logger

logger = get_logger(__name__)


class EnergySystem:
    """Energy system configuration and optimization orchestrator.

    This class provides a high-level interface for configuring and optimizing
    energy systems. It handles system validation, model building, and
    optimization execution through external solvers.
    """

    def __init__(
        self,
        portfolio: AssetPortfolio,
        demand_profile: list[float],
        timestep: timedelta,
        available_capacity_profiles: dict[str, list[float]] | None = None,
    ) -> None:
        """Initialize the energy system configuration and optimizer.

        Args:
            portfolio: The portfolio of energy assets (generators, batteries, etc.).
            demand_profile: List of power demand values for each time period.
            timestep: Duration of each time period.
            available_capacity_profiles: Optional dict mapping generator names to
                their available capacity profiles over time.

        """
        validated_model = ValidatedEnergySystem(
            portfolio=portfolio,
            demand_profile=demand_profile,
            timestep=timestep,
            available_capacity_profiles=available_capacity_profiles,
        )
        model_builder = EnergyAlgebraicModelBuilder(validated_model)
        self._algebraic_model = model_builder.build()

    def optimize(
        self,
        solver: AlgebraicModelSolver | None = None,
    ) -> OptimizationResults:
        """Optimize the energy system.

        This method solves the pre-built algebraic model using the specified solver.
        The model is built during initialization from the energy system configuration.

        Args:
            solver: The solver to use for optimization. Defaults to HiGHSolver.

        Returns:
            OptimizationResults containing the solution and metadata.

        """
        solver = solver if solver is not None else HiGHSolver()
        return solver.solve(self._algebraic_model)
