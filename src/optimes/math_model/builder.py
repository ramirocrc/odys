import pyomo.environ as pyo

from optimes.energy_system.energy_system_conditions import EnergySystem
from optimes.math_model.algebraic_model import AlgebraicModel
from optimes.math_model.model_components.constraints import (
    BatteryChargeModeConstraint,
    BatteryDischargeModeConstraint,
    BatterySocBoundsConstraint,
    BatterySocDynamicsConstraint,
    BatterySocEndConstraint,
    GenerationLimitConstraint,
    PowerBalanceConstraint,
)
from optimes.math_model.model_components.objectives import MinimizeOperationalCostObjective
from optimes.math_model.model_components.parameters import EnergyModelParameterName, SystemParameter
from optimes.math_model.model_components.sets import EnergyModelSetName, SystemSet
from optimes.math_model.model_components.variables import EnergyModelVariableName, SystemVarible
from optimes.utils.logging import get_logger

logger = get_logger(__name__)


class EnergyAlgebraicModelBuilder:
    def __init__(
        self,
        model_data: EnergySystem,
    ) -> None:
        self._model_data = model_data
        self._ext_pyo_model = AlgebraicModel()

    def build(self) -> AlgebraicModel:
        self._add_model_sets()
        self._add_model_parameters()
        self._add_model_variables()
        self._add_model_constraints()
        self._add_model_objective()
        return self._ext_pyo_model

    def _add_model_sets(self) -> None:
        time_indices = range(len(self._model_data.demand_profile))
        generator_indices = (gen.name for gen in self._model_data.portfolio.generators)
        battery_indices = (bat.name for bat in self._model_data.portfolio.batteries)
        self._ext_pyo_model.new_component(
            SystemSet(
                name=EnergyModelSetName.TIME,
                component=pyo.Set(initialize=time_indices),
            ),
        )
        self._ext_pyo_model.new_component(
            SystemSet(
                name=EnergyModelSetName.GENERATORS,
                component=pyo.Set(initialize=generator_indices),
            ),
        )
        self._ext_pyo_model.new_component(
            SystemSet(
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
            SystemParameter(
                name=EnergyModelParameterName.GENERATOR_NOMINAL_POWER,
                component=pyo.Param(
                    self._ext_pyo_model[EnergyModelSetName.GENERATORS],
                    initialize={gen.name: gen.nominal_power for gen in self._model_data.portfolio.generators},
                    mutable=False,
                    name=EnergyModelParameterName.GENERATOR_NOMINAL_POWER.value,
                ),
            ),
        )

        self._ext_pyo_model.new_component(
            SystemParameter(
                name=EnergyModelParameterName.GENERATOR_VARIABLE_COST,
                component=pyo.Param(
                    self._ext_pyo_model[EnergyModelSetName.GENERATORS],
                    initialize={gen.name: gen.variable_cost for gen in self._model_data.portfolio.generators},
                    mutable=False,
                    name=EnergyModelParameterName.GENERATOR_VARIABLE_COST.value,
                ),
            ),
        )

    def _add_battery_parameters(self) -> None:
        self._ext_pyo_model.new_component(
            SystemParameter(
                name=EnergyModelParameterName.BATTERY_MAX_POWER,
                component=pyo.Param(
                    self._ext_pyo_model[EnergyModelSetName.BATTERIES],
                    initialize={battery.name: battery.max_power for battery in self._model_data.portfolio.batteries},
                    mutable=False,
                    name=EnergyModelParameterName.BATTERY_MAX_POWER.value,
                ),
            ),
        )

        self._ext_pyo_model.new_component(
            SystemParameter(
                name=EnergyModelParameterName.BATTERY_EFFICIENCY_CHARGE,
                component=pyo.Param(
                    self._ext_pyo_model[EnergyModelSetName.BATTERIES],
                    initialize={
                        battery.name: battery.efficiency_charging for battery in self._model_data.portfolio.batteries
                    },
                    mutable=False,
                    name=EnergyModelParameterName.BATTERY_EFFICIENCY_CHARGE.value,
                ),
            ),
        )

        self._ext_pyo_model.new_component(
            SystemParameter(
                name=EnergyModelParameterName.BATTERY_EFFICIENCY_DISCHARGE,
                component=pyo.Param(
                    self._ext_pyo_model[EnergyModelSetName.BATTERIES],
                    initialize={
                        battery.name: battery.efficiency_discharging for battery in self._model_data.portfolio.batteries
                    },
                    mutable=False,
                    name=EnergyModelParameterName.BATTERY_EFFICIENCY_DISCHARGE.value,
                ),
            ),
        )

        self._ext_pyo_model.new_component(
            SystemParameter(
                name=EnergyModelParameterName.BATTERY_SOC_INITIAL,
                component=pyo.Param(
                    self._ext_pyo_model[EnergyModelSetName.BATTERIES],
                    initialize={battery.name: battery.soc_initial for battery in self._model_data.portfolio.batteries},
                    mutable=False,
                    name=EnergyModelParameterName.BATTERY_SOC_INITIAL.value,
                ),
            ),
        )

        self._ext_pyo_model.new_component(
            SystemParameter(
                name=EnergyModelParameterName.BATTERY_SOC_TERMINAL,
                component=pyo.Param(
                    self._ext_pyo_model[EnergyModelSetName.BATTERIES],
                    initialize={battery.name: battery.soc_terminal for battery in self._model_data.portfolio.batteries},
                    mutable=False,
                    name=EnergyModelParameterName.BATTERY_SOC_TERMINAL.value,
                ),
            ),
        )

        self._ext_pyo_model.new_component(
            SystemParameter(
                name=EnergyModelParameterName.BATTERY_CAPACITY,
                component=pyo.Param(
                    self._ext_pyo_model[EnergyModelSetName.BATTERIES],
                    initialize={battery.name: battery.capacity for battery in self._model_data.portfolio.batteries},
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
            SystemParameter(
                name=EnergyModelParameterName.SCENARIO_TIMESTEP,
                component=pyo.Param(
                    initialize=self._model_data.timestep,
                    mutable=False,
                    name=EnergyModelParameterName.SCENARIO_TIMESTEP.value,
                    within=pyo.Any,
                ),
            ),
        )

    def _add_demand_parameters(self) -> None:
        self._ext_pyo_model.new_component(
            SystemParameter(
                name=EnergyModelParameterName.DEMAND,
                component=pyo.Param(
                    self._ext_pyo_model[EnergyModelSetName.TIME],
                    initialize=self._model_data.demand_profile,
                    mutable=False,
                    name=EnergyModelParameterName.DEMAND.value,
                ),
            ),
        )

    def _add_available_capacity_parameters(self) -> None:
        if self._model_data.available_capacity_profiles is None:
            return
        msg = "Available capacity profiles not implemented."
        raise NotImplementedError(msg)

    def _add_model_variables(self) -> None:
        self._add_power_generator_variables()
        self._add_battery_variables()

    def _add_power_generator_variables(self) -> None:
        self._ext_pyo_model.new_component(
            SystemVarible(
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
            SystemVarible(
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
            SystemVarible(
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
            SystemVarible(
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
            SystemVarible(
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
        if self._model_data.available_capacity_profiles is None:
            return

    def _add_model_objective(self) -> None:
        objective = MinimizeOperationalCostObjective(
            var_generator_power=self._ext_pyo_model[EnergyModelVariableName.GENERATOR_POWER],
            param_generator_variable_cost=self._ext_pyo_model[EnergyModelParameterName.GENERATOR_VARIABLE_COST],
            param_scenario_timestep=self._ext_pyo_model[EnergyModelParameterName.SCENARIO_TIMESTEP],
        )
        self._ext_pyo_model.new_component(objective)
