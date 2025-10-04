import linopy

from optimes._math_model.model_components.constraints.model_constraint import ModelConstraint
from optimes._math_model.model_components.parameters import (
    SystemParameters,
)
from optimes._math_model.model_components.sets import EnergyModelDimension
from optimes._math_model.model_components.variables import ModelVariable


class ScenarioConstraints:
    def __init__(self, linopy_model: linopy.Model, params: SystemParameters) -> None:
        self.model = linopy_model
        self.params = params
        self.var_generator_power = self.model.variables[ModelVariable.GENERATOR_POWER.var_name]
        self.var_battery_charge = self.model.variables[ModelVariable.BATTERY_POWER_IN.var_name]
        self.var_battery_discharge = self.model.variables[ModelVariable.BATTERY_POWER_OUT.var_name]

    @property
    def all(self) -> tuple[ModelConstraint, ...]:
        constraints = [
            self._get_power_balance_constraint(),
            self._get_available_capcity_profiles_constraint(),
        ]
        if self.params.enforce_non_anticipativity:
            constraints += self._get_non_anticipativity_constraint()
        return tuple(constraints)

    def _get_power_balance_constraint(self) -> ModelConstraint:
        """Linopy power balance constraint ensuring supply equals demand.

        This constraint ensures that at each time period and scenario, the total power
        generation plus battery discharge equals the demand plus battery charging.
        """
        generation_total = self.var_generator_power.sum(EnergyModelDimension.Generators)
        discharge_total = self.var_battery_discharge.sum(EnergyModelDimension.Batteries)
        charge_total = self.var_battery_charge.sum(EnergyModelDimension.Batteries)

        expression = generation_total + discharge_total - charge_total - self.params.demand_profile == 0
        return ModelConstraint(
            name="power_balance_constraint",
            constraint=expression,
        )

    def _get_available_capcity_profiles_constraint(self) -> ModelConstraint:
        expression = self.var_generator_power <= self.params.available_capacity_profiles
        return ModelConstraint(
            name="available_capacity_constraint",
            constraint=expression,
        )

    def _get_non_anticipativity_constraint(self) -> list[ModelConstraint]:
        """Non-anticipativity constraint ensuring variables have same values across scenarios.

        This constraint enforces that decision variables take the same values across
        all scenarios, reflecting that decisions are made before uncertainty is revealed.
        """
        constraints = []
        for variable in ModelVariable:
            linopy_var = self.model.variables[variable.var_name]
            first_scenario_var = linopy_var.isel({EnergyModelDimension.Scenarios: 0})
            expression = linopy_var - first_scenario_var == 0
            constraints.append(
                ModelConstraint(
                    name=f"non_anticipativity_{variable.name}_constraint",
                    constraint=expression,
                ),
            )

        return constraints
