from typing import Self

import pyomo.environ as pyo
from pydantic import BaseModel, model_validator
from pyomo.core.base.set import IndexedComponent
from pyomo.opt import SolverResults, SolverStatus, TerminationCondition

from optimes.assets.generator import PowerGenerator
from optimes.assets.portfolio import AssetPortfolio
from optimes.math_model.pyomo_components.component_protocol import PyomoComponentProtocol
from optimes.math_model.pyomo_components.constraints import (
    BatteryChargeModeConstraint,
    BatteryDischargeModeConstraint,
    BatterySocBoundsConstraint,
    BatterySocDynamicsConstraint,
    BatterySocEndConstraint,
    GenerationLimitConstraint,
    PowerBalanceConstraint,
)
from optimes.math_model.pyomo_components.objectives import MinimizeOperationalCostObjective
from optimes.math_model.pyomo_components.parameters import EnergyModelParameterName, PyomoParameter
from optimes.math_model.pyomo_components.sets import EnergyModelSetName, PyomoSet
from optimes.math_model.pyomo_components.variables import EnergyModelVariableName, PyomoVariable
from optimes.solvers.highs_solver import HiGHSolver
from optimes.system.scenario import ScenarioConditions
from optimes.utils.logging import get_logger

logger = get_logger(__name__)


class ExtendedPyomoModel(pyo.ConcreteModel):
    def new_component(self, component: PyomoComponentProtocol) -> None:
        if hasattr(self, component.name.value):
            msg = f"Component {component.name} already exists in the model."
            raise AttributeError(msg)
        if not isinstance(component.component, IndexedComponent):
            msg = f"Expected IndexedComponent, got {type(component.component)}"
            raise TypeError(msg)
        setattr(self, component.name.value, component.component)

    def __getitem__(
        self,
        name: EnergyModelVariableName | EnergyModelParameterName | EnergyModelSetName,
    ) -> IndexedComponent:
        if not hasattr(self, name.value):
            msg = f"Component {name.value} does not exist in the model."
            raise AttributeError(msg)
        return getattr(self, name.value)


class PyomoModelInputData(BaseModel, arbitrary_types_allowed=True):
    portfolio: AssetPortfolio
    scenario: ScenarioConditions

    @model_validator(mode="after")
    def _validate_inputs(self) -> Self:
        if self.scenario.available_capacity_profiles is not None:
            self._validate_available_capacity()

        self._validate_demand_can_be_met()
        return self

    def _validate_available_capacity(self) -> None:
        for asset_name, capacities in self.scenario.available_capacity_profiles.items():
            asset = self._portfolio.get_asset(asset_name)
            if not isinstance(asset, PowerGenerator):
                msg = (
                    "Available capacity can only be specified for generators, "
                    f"but got '{asset_name}' of type {type(asset)}."
                )
            if len(capacities) != len(self.scenario.demand_profile):
                msg = (
                    f"Available capacity for '{asset_name}' has a length of {len(capacities)}, "
                    f"which doesn't  match the length of the load profile ({len(self.scenario.demand_profile)})."
                )
                raise ValueError(msg)

    def _validate_demand_can_be_met(self) -> None:
        self._validate_enough_power_to_meet_demand()
        self._valiate_enough_energy_to_meet_demand()

    def _validate_enough_power_to_meet_demand(self) -> None:
        cumulative_generators_power = sum(gen.nominal_power for gen in self.portfolio.generators)
        # TODO: We assume full capacity can be discharged -> Needs to be limited by max power
        cumulative_battery_capacities = sum(bat.capacity for bat in self.portfolio.batteries)
        max_available_power = cumulative_generators_power + cumulative_battery_capacities
        for t, demand_t in enumerate(self.scenario.demand_profile):
            if max_available_power < demand_t:
                msg = (
                    f"Infeasible problem at time index {t}: "
                    f"Demand = {demand_t}, but maximum available generation + battery = {max_available_power}."
                )
                raise ValueError(msg)

    def _valiate_enough_energy_to_meet_demand(self) -> None:
        # TODO: Validate that:
        # sum(demand * deltat) <= sum(generator.nominal_power) + sum(battery.soc_initial - battery.soc_terminal) # noqa: ERA001, E501
        pass


class PyomoModelBuilder:
    def __init__(
        self,
        model_data: PyomoModelInputData,
    ) -> None:
        self._portfolio = model_data.portfolio
        self._scenario = model_data.scenario
        self._ext_pyo_model = ExtendedPyomoModel()

    def build(self) -> ExtendedPyomoModel:
        self._add_model_sets()
        self._add_model_parameters()
        self._add_model_variables()
        self._add_model_constraints()
        self._add_model_objective()
        return self._ext_pyo_model

    def _add_model_sets(self) -> None:
        time_indices = list(range(len(self._scenario.demand_profile)))
        generator_indices = [gen.name for gen in self._portfolio.generators]
        battery_indices = [bat.name for bat in self._portfolio.batteries]
        self._ext_pyo_model.new_component(
            PyomoSet(
                name=EnergyModelSetName.TIME,
                component=pyo.Set(initialize=time_indices),
            ),
        )
        self._ext_pyo_model.new_component(
            PyomoSet(
                name=EnergyModelSetName.GENERATORS,
                component=pyo.Set(initialize=generator_indices),
            ),
        )
        self._ext_pyo_model.new_component(
            PyomoSet(
                name=EnergyModelSetName.BATTERIES,
                component=pyo.Set(initialize=battery_indices),
            ),
        )

    def _add_model_parameters(self) -> None:
        """
        This method is intentionally left empty.
        Parameters are not used in this model, but can be added if needed.
        """
        self._add_generator_parameters()
        self._add_battery_parameters()
        self._add_scenario_parameters()

    def _add_generator_parameters(self) -> None:
        self._ext_pyo_model.new_component(
            PyomoParameter(
                name=EnergyModelParameterName.GENERATOR_NOMINAL_POWER,
                component=pyo.Param(
                    self._ext_pyo_model[EnergyModelSetName.GENERATORS],
                    initialize={gen.name: gen.nominal_power for gen in self._portfolio.generators},
                    mutable=False,
                    name=EnergyModelParameterName.GENERATOR_NOMINAL_POWER.value,
                ),
            ),
        )

        self._ext_pyo_model.new_component(
            PyomoParameter(
                name=EnergyModelParameterName.GENERATOR_VARIABLE_COST,
                component=pyo.Param(
                    self._ext_pyo_model[EnergyModelSetName.GENERATORS],
                    initialize={gen.name: gen.variable_cost for gen in self._portfolio.generators},
                    mutable=False,
                    name=EnergyModelParameterName.GENERATOR_VARIABLE_COST.value,
                ),
            ),
        )

    def _add_battery_parameters(self) -> None:
        self._ext_pyo_model.new_component(
            PyomoParameter(
                name=EnergyModelParameterName.BATTERY_MAX_POWER,
                component=pyo.Param(
                    self._ext_pyo_model[EnergyModelSetName.BATTERIES],
                    initialize={battery.name: battery.max_power for battery in self._portfolio.batteries},
                    mutable=False,
                    name=EnergyModelParameterName.BATTERY_MAX_POWER.value,
                ),
            ),
        )

        self._ext_pyo_model.new_component(
            PyomoParameter(
                name=EnergyModelParameterName.BATTERY_EFFICIENCY_CHARGE,
                component=pyo.Param(
                    self._ext_pyo_model[EnergyModelSetName.BATTERIES],
                    initialize={battery.name: battery.efficiency_charging for battery in self._portfolio.batteries},
                    mutable=False,
                    name=EnergyModelParameterName.BATTERY_EFFICIENCY_CHARGE.value,
                ),
            ),
        )

        self._ext_pyo_model.new_component(
            PyomoParameter(
                name=EnergyModelParameterName.BATTERY_EFFICIENCY_DISCHARGE,
                component=pyo.Param(
                    self._ext_pyo_model[EnergyModelSetName.BATTERIES],
                    initialize={battery.name: battery.efficiency_discharging for battery in self._portfolio.batteries},
                    mutable=False,
                    name=EnergyModelParameterName.BATTERY_EFFICIENCY_DISCHARGE.value,
                ),
            ),
        )

        self._ext_pyo_model.new_component(
            PyomoParameter(
                name=EnergyModelParameterName.BATTERY_SOC_INITIAL,
                component=pyo.Param(
                    self._ext_pyo_model[EnergyModelSetName.BATTERIES],
                    initialize={battery.name: battery.soc_initial for battery in self._portfolio.batteries},
                    mutable=False,
                    name=EnergyModelParameterName.BATTERY_SOC_INITIAL.value,
                ),
            ),
        )

        self._ext_pyo_model.new_component(
            PyomoParameter(
                name=EnergyModelParameterName.BATTERY_SOC_TERMINAL,
                component=pyo.Param(
                    self._ext_pyo_model[EnergyModelSetName.BATTERIES],
                    initialize={battery.name: battery.soc_terminal for battery in self._portfolio.batteries},
                    mutable=False,
                    name=EnergyModelParameterName.BATTERY_SOC_TERMINAL.value,
                ),
            ),
        )

        self._ext_pyo_model.new_component(
            PyomoParameter(
                name=EnergyModelParameterName.BATTERY_CAPACITY,
                component=pyo.Param(
                    self._ext_pyo_model[EnergyModelSetName.BATTERIES],
                    initialize={battery.name: battery.capacity for battery in self._portfolio.batteries},
                    mutable=False,
                    name=EnergyModelParameterName.BATTERY_CAPACITY.value,
                ),
            ),
        )

    def _add_scenario_parameters(self) -> None:
        self._add_timestep_parameter()
        self._add_demand_parameters()
        self._add_available_capacity_parameters()

    def _add_timestep_parameter(self) -> None:
        self._ext_pyo_model.new_component(
            PyomoParameter(
                name=EnergyModelParameterName.SCENARIO_TIMESTEP,
                component=pyo.Param(
                    initialize=self._scenario.timestep,
                    mutable=False,
                    name=EnergyModelParameterName.SCENARIO_TIMESTEP.value,
                ),
            ),
        )

    def _add_demand_parameters(self) -> None:
        self._ext_pyo_model.new_component(
            PyomoParameter(
                name=EnergyModelParameterName.DEMAND,
                component=pyo.Param(
                    self._ext_pyo_model[EnergyModelSetName.TIME],
                    initialize=self._scenario.demand_profile,
                    mutable=False,
                    name=EnergyModelParameterName.DEMAND.value,
                ),
            ),
        )

    def _add_available_capacity_parameters(self) -> None:
        if self._scenario.available_capacity_profiles is None:
            return
        msg = "Available capacity profiles not implemented."
        raise NotImplementedError(msg)

    def _add_model_variables(self) -> None:
        self._add_power_generator_variables()
        self._add_battery_variables()

    def _add_power_generator_variables(self) -> None:
        self._ext_pyo_model.new_component(
            PyomoVariable(
                name=EnergyModelVariableName.GENERATOR_POWER,
                component=pyo.Var(
                    self._ext_pyo_model[EnergyModelSetName.TIME],
                    self._ext_pyo_model[EnergyModelSetName.GENERATORS],
                    domain=pyo.NonNegativeReals,
                ),
            ),
        )

    def _add_battery_variables(self) -> None:
        self._ext_pyo_model.new_component(
            PyomoVariable(
                name=EnergyModelVariableName.BATTERY_CHARGE,
                component=pyo.Var(
                    self._ext_pyo_model[EnergyModelSetName.TIME],
                    self._ext_pyo_model[EnergyModelSetName.BATTERIES],
                    domain=pyo.NonNegativeReals,
                    name=EnergyModelVariableName.BATTERY_CHARGE.value,
                ),
            ),
        )
        self._ext_pyo_model.new_component(
            PyomoVariable(
                name=EnergyModelVariableName.BATTERY_DISCHARGE,
                component=pyo.Var(
                    self._ext_pyo_model[EnergyModelSetName.TIME],
                    self._ext_pyo_model[EnergyModelSetName.BATTERIES],
                    domain=pyo.NonNegativeReals,
                    name=EnergyModelVariableName.BATTERY_DISCHARGE.value,
                ),
            ),
        )
        self._ext_pyo_model.new_component(
            PyomoVariable(
                name=EnergyModelVariableName.BATTERY_SOC,
                component=pyo.Var(
                    self._ext_pyo_model[EnergyModelSetName.TIME],
                    self._ext_pyo_model[EnergyModelSetName.BATTERIES],
                    domain=pyo.NonNegativeReals,
                    name=EnergyModelVariableName.BATTERY_SOC.value,
                ),
            ),
        )
        self._ext_pyo_model.new_component(
            PyomoVariable(
                name=EnergyModelVariableName.BATTERY_CHARGE_MODE,
                component=pyo.Var(
                    self._ext_pyo_model[EnergyModelSetName.TIME],
                    self._ext_pyo_model[EnergyModelSetName.BATTERIES],
                    within=pyo.Binary,
                ),
            ),
        )

    def _add_model_constraints(self) -> None:
        self._add_power_balance_constraint()
        self._add_power_generator_constraints()
        self._add_model_battery_constraints()
        self._add_scenario_constraints()

    def _add_power_balance_constraint(self) -> None:
        power_balance_constraint = PowerBalanceConstraint(
            var_generator_power=self._ext_pyo_model[EnergyModelVariableName.GENERATOR_POWER],
            var_battery_discharge=self._ext_pyo_model[EnergyModelVariableName.BATTERY_DISCHARGE],
            var_battery_charge=self._ext_pyo_model[EnergyModelVariableName.BATTERY_CHARGE],
            param_demand=self._ext_pyo_model[EnergyModelParameterName.DEMAND],
        )
        self._ext_pyo_model.new_component(power_balance_constraint)

    def _add_power_generator_constraints(self) -> None:
        generation_limit_constraint = GenerationLimitConstraint(
            var_generator_power=self._ext_pyo_model[EnergyModelVariableName.GENERATOR_POWER],
            param_generator_nominal_power=self._ext_pyo_model[EnergyModelParameterName.GENERATOR_NOMINAL_POWER],
        )
        self._ext_pyo_model.new_component(generation_limit_constraint)

    def _add_model_battery_constraints(self) -> None:
        battery_charge_limit_constraint = BatteryChargeModeConstraint(
            var_battery_charge=self._ext_pyo_model[EnergyModelVariableName.BATTERY_CHARGE],
            var_battery_charge_mode=self._ext_pyo_model[EnergyModelVariableName.BATTERY_CHARGE_MODE],
            param_battery_max_power=self._ext_pyo_model[EnergyModelParameterName.BATTERY_MAX_POWER],
        )
        self._ext_pyo_model.new_component(battery_charge_limit_constraint)

        battery_discharge_limit_constraint = BatteryDischargeModeConstraint(
            var_battery_discharge=self._ext_pyo_model[EnergyModelVariableName.BATTERY_DISCHARGE],
            var_battery_charge_mode=self._ext_pyo_model[EnergyModelVariableName.BATTERY_CHARGE_MODE],
            param_battery_max_power=self._ext_pyo_model[EnergyModelParameterName.BATTERY_MAX_POWER],
        )
        self._ext_pyo_model.new_component(battery_discharge_limit_constraint)

        battery_soc_dynamics_constraint = BatterySocDynamicsConstraint(
            var_battery_soc=self._ext_pyo_model[EnergyModelVariableName.BATTERY_SOC],
            var_battery_charge=self._ext_pyo_model[EnergyModelVariableName.BATTERY_CHARGE],
            var_battery_discharge=self._ext_pyo_model[EnergyModelVariableName.BATTERY_DISCHARGE],
            param_battery_efficiency_charging=self._ext_pyo_model[EnergyModelParameterName.BATTERY_EFFICIENCY_CHARGE],
            param_battery_efficiency_discharging=self._ext_pyo_model[
                EnergyModelParameterName.BATTERY_EFFICIENCY_DISCHARGE
            ],
            param_battery_soc_initial=self._ext_pyo_model[EnergyModelParameterName.BATTERY_SOC_INITIAL],
        )
        self._ext_pyo_model.new_component(battery_soc_dynamics_constraint)

        battery_soc_bounds_constraint = BatterySocBoundsConstraint(
            var_battery_soc=self._ext_pyo_model[EnergyModelVariableName.BATTERY_SOC],
            param_battery_capacity=self._ext_pyo_model[EnergyModelParameterName.BATTERY_CAPACITY],
        )
        self._ext_pyo_model.new_component(battery_soc_bounds_constraint)

        battery_soc_end_constraint = BatterySocEndConstraint(
            var_battery_soc=self._ext_pyo_model[EnergyModelVariableName.BATTERY_SOC],
            param_battery_soc_terminal=self._ext_pyo_model[EnergyModelParameterName.BATTERY_SOC_TERMINAL],
        )

        self._ext_pyo_model.new_component(battery_soc_end_constraint)

    def _add_scenario_constraints(self) -> None:
        if self._scenario.available_capacity_profiles is None:
            return

    def _add_model_objective(self) -> None:
        objective = MinimizeOperationalCostObjective(
            var_generator_power=self._ext_pyo_model[EnergyModelVariableName.GENERATOR_POWER],
            param_generator_variable_cost=self._ext_pyo_model[EnergyModelParameterName.GENERATOR_VARIABLE_COST],
            param_scenario_timestep=self._ext_pyo_model[EnergyModelParameterName.SCENARIO_TIMESTEP],
        )
        self._ext_pyo_model.new_component(objective)


class EnergyModel:
    def __init__(
        self,
        portfolio: AssetPortfolio,
        scenario: ScenarioConditions,
    ) -> None:
        self._portfolio = portfolio
        self._scenario = scenario
        model_data = PyomoModelInputData(portfolio=portfolio, scenario=scenario)
        model_builder = PyomoModelBuilder(model_data)
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
