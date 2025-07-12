import pyomo.environ as pyo
from pyomo.opt import SolverResults, SolverStatus, TerminationCondition

from optimes.assets.portfolio import AssetPortfolio
from optimes.math_model.constraints import (
    BatteryChargeModeConstraint,
    BatteryDischargeModeConstraint,
    BatterySocBoundsConstraint,
    BatterySocDynamicsConstraint,
    BatterySocEndConstraint,
    GenerationLimitConstraint,
    PowerBalanceConstraint,
)
from optimes.math_model.model_enums import (
    EnergyModelConstraint,
    EnergyModelObjective,
    EnergyModelSet,
    EnergyModelVariable,
)
from optimes.math_model.objectives import minimize_operational_cost_of
from optimes.solvers.highs_solver import HiGHSolver
from optimes.system.load import LoadProfile
from optimes.utils.logging import get_logger

logger = get_logger(__name__)


class EnergyModel:
    def __init__(self, portfolio: AssetPortfolio, load_profile: LoadProfile) -> None:
        self._portfolio = portfolio
        self._load_profile = load_profile
        self._pyo_model = pyo.ConcreteModel()
        self._solver = HiGHSolver()
        self._results: SolverResults | None = None

    def _build(self) -> None:
        self._add_model_sets()
        self._add_model_variables()
        self._add_model_constraints()
        self._add_model_objective()

    def _add_model_sets(self) -> None:
        time_indices = list(range(len(self._load_profile.profile)))
        generator_indices = list(range(len(self._portfolio.generators)))
        battery_indices = list(range(len(self._portfolio.batteries)))
        self._add_set(EnergyModelSet.TIME, pyo.Set(initialize=time_indices))
        self._add_set(EnergyModelSet.GENERATORS, pyo.Set(initialize=generator_indices))
        self._add_set(EnergyModelSet.BATTERIES, pyo.Set(initialize=battery_indices))

    def _add_model_variables(self) -> None:
        self._add_power_generator_variables()
        self._add_battery_variables()

    def _add_power_generator_variables(self) -> None:
        self._add_variable(
            EnergyModelVariable.GENERATOR_POWER,
            pyo.Var(
                self.get_set(EnergyModelSet.TIME),
                self.get_set(EnergyModelSet.GENERATORS),
                domain=pyo.NonNegativeReals,
            ),
        )

    def _add_battery_variables(self) -> None:
        self._add_variable(
            EnergyModelVariable.BATTERY_CHARGE,
            pyo.Var(
                self.get_set(EnergyModelSet.TIME),
                self.get_set(EnergyModelSet.BATTERIES),
                domain=pyo.NonNegativeReals,
                name=EnergyModelVariable.BATTERY_CHARGE.value,
            ),
        )
        self._add_variable(
            EnergyModelVariable.BATTERY_DISCHARGE,
            pyo.Var(
                self.get_set(EnergyModelSet.TIME),
                self.get_set(EnergyModelSet.BATTERIES),
                domain=pyo.NonNegativeReals,
                name=EnergyModelVariable.BATTERY_DISCHARGE.value,
            ),
        )
        self._add_variable(
            EnergyModelVariable.BATTERY_SOC,
            pyo.Var(
                self.get_set(EnergyModelSet.TIME),
                self.get_set(EnergyModelSet.BATTERIES),
                domain=pyo.NonNegativeReals,
                name=EnergyModelVariable.BATTERY_SOC.value,
            ),
        )
        self._add_variable(
            EnergyModelVariable.BATTERY_CHARGE_MODE,
            pyo.Var(
                self.get_set(EnergyModelSet.TIME),
                self.get_set(EnergyModelSet.BATTERIES),
                within=pyo.Binary,
            ),
        )

    def _add_model_constraints(self) -> None:
        self._add_power_balance_constraint()
        self._add_power_generator_constraints()
        self._add_model_battery_constraints()

    def _add_power_balance_constraint(self) -> None:
        power_balance_constraint = PowerBalanceConstraint(
            generator_power=self.get_variable(EnergyModelVariable.GENERATOR_POWER),
            battery_discharge=self.get_variable(EnergyModelVariable.BATTERY_DISCHARGE),
            battery_charge=self.get_variable(EnergyModelVariable.BATTERY_CHARGE),
            load_profile=self._load_profile,
        )
        self._add_constraint(
            power_balance_constraint.name,
            power_balance_constraint.constraint,
        )

    def _add_power_generator_constraints(self) -> None:
        generation_limit_constraint = GenerationLimitConstraint(
            generator_power=self.get_variable(EnergyModelVariable.GENERATOR_POWER),
            generators=self._portfolio.generators,
        )
        self._add_constraint(
            generation_limit_constraint.name,
            generation_limit_constraint.constraint,
        )

    def _add_model_battery_constraints(self) -> None:
        battery_charge_limit_constraint = BatteryChargeModeConstraint(
            battery_charge=self.get_variable(EnergyModelVariable.BATTERY_CHARGE),
            battery_charge_mode=self.get_variable(EnergyModelVariable.BATTERY_CHARGE_MODE),
            batteries=self._portfolio.batteries,
        )
        self._add_constraint(
            battery_charge_limit_constraint.name,
            battery_charge_limit_constraint.constraint,
        )

        battery_discharge_limit_constraint = BatteryDischargeModeConstraint(
            battery_discharge=self.get_variable(EnergyModelVariable.BATTERY_DISCHARGE),
            battery_charge_mode=self.get_variable(EnergyModelVariable.BATTERY_CHARGE_MODE),
            batteries=self._portfolio.batteries,
        )
        self._add_constraint(
            battery_discharge_limit_constraint.name,
            battery_discharge_limit_constraint.constraint,
        )

        battery_soc_dynamics_constraint = BatterySocDynamicsConstraint(
            battery_soc=self.get_variable(EnergyModelVariable.BATTERY_SOC),
            battery_charge=self.get_variable(EnergyModelVariable.BATTERY_CHARGE),
            battery_discharge=self.get_variable(EnergyModelVariable.BATTERY_DISCHARGE),
            batteries=self._portfolio.batteries,
        )
        self._add_constraint(
            battery_soc_dynamics_constraint.name,
            battery_soc_dynamics_constraint.constraint,
        )

        battery_soc_bounds_constraint = BatterySocBoundsConstraint(
            battery_soc=self.get_variable(EnergyModelVariable.BATTERY_SOC),
            batteries=self._portfolio.batteries,
        )
        self._add_constraint(
            battery_soc_bounds_constraint.name,
            battery_soc_bounds_constraint.constraint,
        )

        battery_soc_end_constraint = BatterySocEndConstraint(
            battery_soc=self.get_variable(EnergyModelVariable.BATTERY_SOC),
            batteries=self._portfolio.batteries,
        )
        self._add_constraint(
            battery_soc_end_constraint.name,
            battery_soc_end_constraint.constraint,
        )

    def _add_model_objective(self) -> None:
        self._add_objective(
            name=EnergyModelObjective.MIN_OPERATIONAL_COST,
            objective=minimize_operational_cost_of(
                generator_power=self.get_variable(EnergyModelVariable.GENERATOR_POWER),
                generators=self._portfolio.generators,
            ),
        )

    @property
    def solver_results(self) -> SolverResults:
        if self._results is None:
            msg = "No solve has been performed yet."
            raise RuntimeError(msg)
        return self._results

    def _add_set(self, name: EnergyModelSet, set_: pyo.Set) -> None:
        if not isinstance(name, EnergyModelSet):
            msg = f"Name {name} is not a valid EnergyModelSet."
            raise TypeError(msg)
        if not isinstance(set_, pyo.Set):
            msg = f"Set {set_} is not a valid Pyomo Set."
            raise TypeError(msg)
        setattr(self._pyo_model, name.value, set_)

    def _add_variable(self, name: EnergyModelVariable, variable: pyo.Var) -> None:
        if not isinstance(name, EnergyModelVariable):
            msg = f"Name {name} is not a valid EnergyModelVariable."
            raise TypeError(msg)
        if not isinstance(variable, pyo.Var):
            msg = f"Variable {variable} is not a valid Pyomo Var."
            raise TypeError(msg)
        setattr(self._pyo_model, name.value, variable)

    def _add_constraint(self, name: EnergyModelConstraint, constraint: pyo.Constraint) -> None:
        if not isinstance(name, EnergyModelConstraint):
            msg = f"Name {name} is not a valid EnergyModelConstraint."
            raise TypeError(msg)
        if not isinstance(constraint, pyo.Constraint):
            msg = f"Constraint {constraint} is not a valid Pyomo Constraint."
            raise TypeError(msg)

        setattr(self._pyo_model, name.value, constraint)

    def _add_objective(self, name: EnergyModelObjective, objective: pyo.Objective) -> None:
        if not isinstance(name, EnergyModelObjective):
            msg = f"Name {name} is not a valid EnergyModelObjective."
            raise TypeError(msg)
        if not isinstance(objective, pyo.Objective):
            msg = f"Objective {objective} is not a valid Pyomo Objective."
            raise TypeError(msg)
        setattr(self._pyo_model, name.value, objective)

    def get_variable(self, name: EnergyModelVariable) -> pyo.Var:
        if not isinstance(name, EnergyModelVariable):
            msg = f"Name {name} is not a valid EnergyModelVariable."
            raise TypeError(msg)
        if not hasattr(self._pyo_model, name.value):
            msg = f"Variable {name.value} does not exist in the model."
            raise AttributeError(msg)
        return getattr(self._pyo_model, name.value)

    def get_set(self, name: EnergyModelSet) -> pyo.Set:
        if not isinstance(name, EnergyModelSet):
            msg = f"Name {name} is not a valid EnergyModelSet."
            raise TypeError(msg)
        if not hasattr(self._pyo_model, name.value):
            msg = f"Set {name.value} does not exist in the model."
            raise AttributeError(msg)
        return getattr(self._pyo_model, name.value)

    def optimize(self) -> None:
        """
        Optimize the model using the specified solver.
        This method is a wrapper around the `solve` method.
        """
        self._build()
        self._solve()

    def _solve(self) -> SolverResults:
        """
        Solve the model using the specified solver.
        """

        if not isinstance(self._pyo_model, pyo.ConcreteModel):
            msg = "Model is not a valid Pyomo ConcreteModel."
            raise TypeError(msg)
        self._results = self._solver.solve(self._pyo_model)
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
