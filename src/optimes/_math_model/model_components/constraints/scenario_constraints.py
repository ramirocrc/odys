from optimes._math_model.milp_model import EnergyMILPModel
from optimes._math_model.model_components.constraints.model_constraint import ModelConstraint
from optimes._math_model.model_components.sets import ModelDimension
from optimes._math_model.model_components.variables import ModelVariable


class ScenarioConstraints:
    def __init__(self, milp_model: EnergyMILPModel) -> None:
        self.model = milp_model
        self.params = milp_model.parameters.scenario
        self._include_generators = bool(milp_model.parameters.generators)
        self._include_batteries = bool(milp_model.parameters.batteries)
        self._include_markets = bool(milp_model.parameters.markets)

    @property
    def all(self) -> tuple[ModelConstraint, ...]:
        constraints = [
            self._get_power_balance_constraint(),
        ]
        if self._include_generators and self.params.available_capacity_profiles is not None:
            constraints.append(self._get_available_capacity_profiles_constraint())
        if self.params.enforce_non_anticipativity:
            constraints += self._get_non_anticipativity_constraint()
        return tuple(constraints)

    def _get_power_balance_constraint(self) -> ModelConstraint:
        """Linopy power balance constraint ensuring supply equals demand.

        This constraint ensures that at each time period and scenario, the total power
        generation plus battery discharge equals the demand plus battery charging.
        """
        lhs = 0
        if self._include_generators:
            lhs += self.model.generator_power.sum(ModelDimension.Generators)

        if self._include_batteries:
            lhs += self.model.battery_power_out.sum(ModelDimension.Batteries)
            lhs -= self.model.battery_power_in.sum(ModelDimension.Batteries)

        if self._include_markets:
            lhs += self.model.market_traded_volume.sum(ModelDimension.Markets)

        if self.params.load_profiles is not None:
            lhs -= self.params.load_profiles

        return ModelConstraint(
            name="power_balance_constraint",
            constraint=lhs == 0,  # pyright: ignore reportArgumentType
        )

    def _get_available_capacity_profiles_constraint(self) -> ModelConstraint:
        var_generator_power = self.model.generator_power
        expression = var_generator_power <= self.params.available_capacity_profiles  # pyright: ignore reportOperatorIssue # Validated before calling function
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
            # Only create constraints for variables that exist in the model
            if variable.var_name in self.model.linopy_model.variables:
                linopy_var = self.model.linopy_model.variables[variable.var_name]
                first_scenario_var = linopy_var.isel({ModelDimension.Scenarios: 0})
                expression = linopy_var - first_scenario_var == 0
                constraints.append(
                    ModelConstraint(
                        name=f"non_anticipativity_{variable.var_name}_constraint",
                        constraint=expression,
                    ),
                )

        return constraints
