from linopy import Model

from optimes._math_model.model_components.constraints.battery_constraints import (
    BatteryChargeModeConstraint,
    BatteryDischargeModeConstraint,
    BatteryNetPowerConstraint,
    BatterySocBoundsConstraint,
    BatterySocDynamicsConstraint,
    BatterySocEndConstraint,
    BatterySocStartConstraint,
)
from optimes._math_model.model_components.constraints.generator_constraints import GenerationLimitConstraint
from optimes._math_model.model_components.constraints.power_balance_constraints import PowerBalanceConstraint
from optimes._math_model.model_components.objectives import (
    LinopyMinimizeOperationalCostObjective,
)
from optimes._math_model.model_components.variables import (
    EnergyModelVariableName,
    LinopyVariableParameters,
    SystemVariable,
)
from optimes.energy_system_models.validated_energy_system import ValidatedEnergySystem
from optimes.utils.logging import get_logger

logger = get_logger(__name__)


class EnergyAlgebraicModelBuilder:
    def __init__(
        self,
        validated_energy_system: ValidatedEnergySystem,
    ) -> None:
        self._energy_system = validated_energy_system
        self._linopy_model = Model(force_dim_names=True)
        self._model_is_built: bool = False

    def build(self) -> Model:
        if self._model_is_built:
            msg = "Model has already been built."
            raise AttributeError(msg)
        self._add_model_variables()
        self._add_model_constraints()
        self._add_model_objective()
        self._model_is_built = True

        return self._linopy_model

    def _add_model_variables(self) -> None:
        for generator_variable_i in SystemVariable.generator_variables():
            linopy_variable_parameters = generator_variable_i.get_linopy_variable_parameters(
                time_set=self._energy_system.sets.time,
                asset_set=self._energy_system.sets.generators,
            )
            self.add_variable_to_model(linopy_variable_parameters)

        for battery_variable_i in SystemVariable.battery_variables():
            linopy_variable_parameters = battery_variable_i.get_linopy_variable_parameters(
                time_set=self._energy_system.sets.time,
                asset_set=self._energy_system.sets.batteries,
            )
            self.add_variable_to_model(linopy_variable_parameters)

    def add_variable_to_model(self, variable: LinopyVariableParameters) -> None:
        self._linopy_model.add_variables(
            name=variable.name,
            coords=variable.coords,
            dims=variable.dims,
            lower=variable.lower,
            binary=variable.binary,
        )

    def _add_model_constraints(self) -> None:
        self._add_power_balance_constraint()
        self._add_power_generator_constraints()
        self._add_model_battery_constraints()
        self._add_scenario_constraints()

    def _add_power_balance_constraint(self) -> None:
        # Add linopy power balance constraint
        power_balance_constraint = PowerBalanceConstraint(
            var_generator_power=self._linopy_model.variables[EnergyModelVariableName.GENERATOR_POWER],
            var_battery_discharge=self._linopy_model.variables[EnergyModelVariableName.BATTERY_POWER_OUT],
            var_battery_charge=self._linopy_model.variables[EnergyModelVariableName.BATTERY_POWER_IN],
            demand_profile=self._energy_system.parameters.demand_profile,
        )
        self._linopy_model.add_constraints(
            power_balance_constraint.constraint,
            name=power_balance_constraint.name,
        )

    def _add_power_generator_constraints(self) -> None:
        linopy_generation_limit_constraint = GenerationLimitConstraint(
            var_generator_power=self._linopy_model.variables[EnergyModelVariableName.GENERATOR_POWER],
            param_generator_nominal_power=self._energy_system.parameters.generators_nomianl_power,
        )
        self._linopy_model.add_constraints(
            linopy_generation_limit_constraint.constraint,
            name=linopy_generation_limit_constraint.name,
        )

    def _add_model_battery_constraints(self) -> None:
        linopy_battery_charge_limit_constraint = BatteryChargeModeConstraint(
            var_battery_charge=self._linopy_model.variables[EnergyModelVariableName.BATTERY_POWER_IN],
            var_battery_charge_mode=self._linopy_model.variables[EnergyModelVariableName.BATTERY_CHARGE_MODE],
            param_battery_max_power=self._energy_system.parameters.batteries_max_power,
        )
        self._linopy_model.add_constraints(
            linopy_battery_charge_limit_constraint.constraint,
            name=linopy_battery_charge_limit_constraint.name,
        )

        linopy_battery_discharge_limit_constraint = BatteryDischargeModeConstraint(
            var_battery_discharge=self._linopy_model.variables[EnergyModelVariableName.BATTERY_POWER_OUT],
            var_battery_charge_mode=self._linopy_model.variables[EnergyModelVariableName.BATTERY_CHARGE_MODE],
            param_battery_max_power=self._energy_system.parameters.batteries_max_power,
        )
        self._linopy_model.add_constraints(
            linopy_battery_discharge_limit_constraint.constraint,
            name=linopy_battery_discharge_limit_constraint.name,
        )
        linopy_soc_dynamics_constraint = BatterySocDynamicsConstraint(
            var_battery_charge=self._linopy_model.variables[EnergyModelVariableName.BATTERY_POWER_IN],
            var_battery_discharge=self._linopy_model.variables[EnergyModelVariableName.BATTERY_POWER_OUT],
            var_battery_soc=self._linopy_model.variables[EnergyModelVariableName.BATTERY_SOC],
            param_battery_efficiency_charging=self._energy_system.parameters.batteries_efficiency_charging,
            param_battery_efficiency_discharging=self._energy_system.parameters.batteries_efficiency_discharging,
        )

        self._linopy_model.add_constraints(
            linopy_soc_dynamics_constraint.constraint,
            name=linopy_soc_dynamics_constraint.name,
        )
        linopy_soc_start_constraint = BatterySocStartConstraint(
            var_battery_charge=self._linopy_model.variables[EnergyModelVariableName.BATTERY_POWER_IN],
            var_battery_discharge=self._linopy_model.variables[EnergyModelVariableName.BATTERY_POWER_OUT],
            var_battery_soc=self._linopy_model.variables[EnergyModelVariableName.BATTERY_SOC],
            param_battery_efficiency_charging=self._energy_system.parameters.batteries_efficiency_charging,
            param_battery_efficiency_discharging=self._energy_system.parameters.batteries_efficiency_discharging,
            param_battery_soc_initial=self._energy_system.parameters.batteries_soc_start,
        )

        self._linopy_model.add_constraints(
            linopy_soc_start_constraint.constraint,
            name=linopy_soc_start_constraint.name,
        )

        linopy_soc_bounds_constriant = BatterySocBoundsConstraint(
            var_battery_soc=self._linopy_model.variables[EnergyModelVariableName.BATTERY_SOC],
            param_battery_capacity=self._energy_system.parameters.batteries_capacity,
        )
        self._linopy_model.add_constraints(
            linopy_soc_bounds_constriant.constraint,
            name=linopy_soc_bounds_constriant.name,
        )

        linopy_soc_end_dynamics_constraints = BatterySocEndConstraint(
            var_battery_soc=self._linopy_model.variables[EnergyModelVariableName.BATTERY_SOC],
            param_battery_soc_end=self._energy_system.parameters.batteries_soc_end,
        )
        self._linopy_model.add_constraints(
            linopy_soc_end_dynamics_constraints.constraint,
            name=linopy_soc_end_dynamics_constraints.name,
        )
        linopy_net_power_constraints = BatteryNetPowerConstraint(
            var_battery_charge=self._linopy_model.variables[EnergyModelVariableName.BATTERY_POWER_IN],
            var_battery_discharge=self._linopy_model.variables[EnergyModelVariableName.BATTERY_POWER_OUT],
            var_battery_net_power=self._linopy_model.variables[EnergyModelVariableName.BATTERY_POWER_NET],
        )
        self._linopy_model.add_constraints(
            linopy_net_power_constraints.constraint,
            name=linopy_net_power_constraints.name,
        )

    def _add_scenario_constraints(self) -> None:
        if self._energy_system.available_capacity_profiles is None:
            return

    def _add_model_objective(self) -> None:
        linopy_objective = LinopyMinimizeOperationalCostObjective(
            var_generator_power=self._linopy_model.variables[EnergyModelVariableName.GENERATOR_POWER],
            param_generator_variable_cost=self._energy_system.parameters.generators_variable_cost,
        )
        self._linopy_model.add_objective(linopy_objective.function)
