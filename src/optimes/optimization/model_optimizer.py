"""Model optimizer for energy system optimization.

This module provides the EnergySystemOptimizer class for solving
energy system optimization problems.
"""

from optimes._math_model.model_builder import EnergyAlgebraicModelBuilder
from optimes.energy_system.energy_system_conditions import EnergySystem
from optimes.optimization.optimization_results import OptimizationResults
from optimes.solvers.base_solver import AlgebraicModelSolver
from optimes.solvers.highs_solver import HiGHSolver
from optimes.utils.logging import get_logger

logger = get_logger(__name__)


class EnergySystemOptimizer:
    """Optimizer for energy system models.

    This class provides a high-level interface for optimizing energy systems.
    It handles model building, solving, and result processing.
    """

    def __init__(
        self,
        model_data: EnergySystem,
        solver: AlgebraicModelSolver | None = None,
    ) -> None:
        """Initialize the energy system optimizer.

        Args:
            model_data: The energy system configuration to optimize.
            solver: The solver to use for optimization. Defaults to HiGHSolver.

        """
        self._model_data = model_data
        self._solver = solver if solver is not None else HiGHSolver()

    def optimize(self) -> OptimizationResults:
        """Optimize the energy system.

        This method builds the algebraic model from the energy system
        configuration and solves it using the specified solver.

        Returns:
            OptimizationResults containing the solution and metadata.

        """
        model_builder = EnergyAlgebraicModelBuilder(self._model_data)
        algebraic_model = model_builder.build()
        return self._solver.solve(algebraic_model)
