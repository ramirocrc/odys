import pyomo.environ as pyo
from pyomo.opt import SolverResults


class HiGHSolver:
    def __init__(self) -> None:
        self._solver = pyo.SolverFactory("highs")

    def solve(self, model: pyo.ConcreteModel, *args: object, **kwargs: object) -> SolverResults:
        return self._solver.solve(
            model,
            *args,
            **kwargs,
        )
