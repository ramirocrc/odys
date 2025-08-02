"""Base solver interface for energy system optimization.

This module provides the base solver interface and abstract classes
for implementing different optimization solvers.
"""

from abc import ABC, abstractmethod

from optimes.math_model.algebraic_model import AlgebraicModel
from optimes.optimization.optimization_results import OptimizationResults


class AlgebraicModelSolver(ABC):
    """Abstract base class for optimization solvers.

    This class defines the interface that all solvers must implement
    to be compatible with the optimization framework.
    """

    @abstractmethod
    def solve(self, model: AlgebraicModel, *args: object, **kwargs: object) -> OptimizationResults:
        """Solve the optimization model.

        Args:
            model: The algebraic model to solve
            *args: Additional positional arguments for the solver
            **kwargs: Additional keyword arguments for the solver

        Returns:
            OptimizationResults containing the solution and metadata

        """
