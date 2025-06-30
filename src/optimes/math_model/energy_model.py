from enum import Enum

import pyomo.environ as pyo
from pyomo.opt import SolverResults, SolverStatus, TerminationCondition

from optimes.solvers.highs_solver import HiGHSolver
from optimes.utils.logging import get_logger

logger = get_logger(__name__)


class EnergyModelSet(Enum):
    TIME = "time"
    GENERATORS = "generators"
    BATTERIES = "batteries"


class EnergyModelVariable(Enum):
    GENERATOR_POWER = "generator_power"
    BATTERY_CHARGE = "battery_charge"
    BATTERY_DISCHARGE = "battery_discharge"
    BATTERY_SOC = "battery_soc"
    BATTERY_CHARGE_MODE = "battery_charge_mode"


class EnergyModelConstraint(Enum):
    POWER_BALANCE = "power_balance"
    GENERATOR_LIMIT = "generator_limit"
    BATTERY_CHARGE_LIMIT = "battery_charge_limit"
    BATTERY_DISCHARGE_LIMIT = "battery_discharge_limit"
    BATTERY_SOC_DYNAMICS = "battery_soc_dynamics"
    BATTERY_SOC_BOUNDS = "battery_soc_bounds"
    BATTERY_SOC_TERMINAL = "battery_soc_terminal"


class EnergyModelObjective(Enum):
    TOTAL_VARIABLE_COST = "total_variable_cost"


class EnergyModel(pyo.ConcreteModel):
    """
    Wrapper around Pyomo ConcreteModel that holds all Sets, Vars, Constraints, and the Objective.
    Does not store portfolio or load_profile internally—just the optimization elements.
    """

    def __init__(self, *args: object, **kwargs: object) -> None:
        super().__init__(*args, **kwargs)
        self._results: SolverResults | None = None

    @property
    def solver_results(self) -> SolverResults:
        if self._results is None:
            msg = "No solve has been performed yet."
            raise RuntimeError(msg)
        return self._results

    def add_set(self, name: EnergyModelSet, set_: pyo.Set) -> None:
        if not isinstance(name, EnergyModelSet):
            msg = f"Name {name} is not a valid EnergyModelSet."
            raise TypeError(msg)
        if not isinstance(set_, pyo.Set):
            msg = f"Set {set_} is not a valid Pyomo Set."
            raise TypeError(msg)
        setattr(self, name.value, set_)

    def add_variable(self, name: EnergyModelVariable, variable: pyo.Var) -> None:
        if not isinstance(name, EnergyModelVariable):
            msg = f"Name {name} is not a valid EnergyModelVariable."
            raise TypeError(msg)
        if not isinstance(variable, pyo.Var):
            msg = f"Variable {variable} is not a valid Pyomo Var."
            raise TypeError(msg)
        setattr(self, name.value, variable)

    def add_constraint(self, name: EnergyModelConstraint, constraint: pyo.Constraint) -> None:
        if not isinstance(name, EnergyModelConstraint):
            msg = f"Name {name} is not a valid EnergyModelConstraint."
            raise TypeError(msg)
        if not isinstance(constraint, pyo.Constraint):
            msg = f"Constraint {constraint} is not a valid Pyomo Constraint."
            raise TypeError(msg)

        setattr(self, name.value, constraint)

    def add_objective(self, name: EnergyModelObjective, objective: pyo.Objective) -> None:
        if not isinstance(name, EnergyModelObjective):
            msg = f"Name {name} is not a valid EnergyModelObjective."
            raise TypeError(msg)
        if not isinstance(objective, pyo.Objective):
            msg = f"Objective {objective} is not a valid Pyomo Objective."
            raise TypeError(msg)
        setattr(self, name.value, objective)

    def get_variable(self, name: EnergyModelVariable) -> pyo.Var:
        if not isinstance(name, EnergyModelVariable):
            msg = f"Name {name} is not a valid EnergyModelVariable."
            raise TypeError(msg)
        if not hasattr(self, name.value):
            msg = f"Variable {name.value} does not exist in the model."
            raise AttributeError(msg)
        return getattr(self, name.value)

    def get_set(self, name: EnergyModelSet) -> pyo.Set:
        if not isinstance(name, EnergyModelSet):
            msg = f"Name {name} is not a valid EnergyModelSet."
            raise TypeError(msg)
        if not hasattr(self, name.value):
            msg = f"Set {name.value} does not exist in the model."
            raise AttributeError(msg)
        return getattr(self, name.value)

    def solve(self) -> SolverResults:
        """
        Solve the model using the specified solver.
        """

        self._solver = HiGHSolver()
        self._results = self._solver.solve(self)
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
