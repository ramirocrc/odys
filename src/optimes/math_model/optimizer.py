import pyomo.environ as pyo
from pyomo.opt import SolverResults, SolverStatus, TerminationCondition

from optimes.energy_system.energy_system_conditions import EnergySystem
from optimes.math_model.builder import EnergyAlgebraicModelBuilder
from optimes.solvers.highs_solver import HiGHSolver
from optimes.utils.logging import get_logger

logger = get_logger(__name__)


class EnergySystemOptimizer:
    def __init__(
        self,
        model_data: EnergySystem,
    ) -> None:
        model_builder = EnergyAlgebraicModelBuilder(model_data)
        self.pyo_model = model_builder.build()
        self._solver = HiGHSolver()
        self._results: SolverResults | None = None

    def optimize(self) -> None:
        """
        Optimize the model using the specified solver.
        This method is a wrapper around the `solve` method.
        """
        self._solve()

    @property
    def solver_results(self) -> SolverResults:
        if self._results is None:
            msg = "No optimization has been performed yet."
            raise RuntimeError(msg)
        return self._results

    def _solve(self) -> SolverResults:
        """
        Solve the model using the specified solver.
        """

        if not isinstance(self.pyo_model, pyo.ConcreteModel):
            msg = "Model is not a valid Pyomo ConcreteModel."
            raise TypeError(msg)
        self._results = self._solver.solve(self.pyo_model)

        return self._results

    def solving_status(self) -> SolverStatus | None:
        """
        Returns the solving status of the last solve operation.
        """
        if self._results is None:
            msg = "No solve has been performed yet."
            logger.warning(msg)
            return None
        status = self._results.solver.status

        if not isinstance(status, SolverStatus):
            msg = "Results are not of type SolverResults."
            raise TypeError(msg)

        return status

    def termination_condition(self) -> TerminationCondition | None:
        """
        Returns the termination condition of the last solve operation.
        """
        if self._results is None:
            msg = "No solve has been performed yet."
            logger.warning(msg)
            return None

        termination_condition = self._results.solver.termination_condition
        if not isinstance(termination_condition, TerminationCondition):
            msg = "Results are not of type SolverResults."
            raise TypeError(msg)

        return termination_condition
