from optimes._math_model.milp_model import EnergyMILPModel
from optimes._math_model.model_components.constraints.model_constraint import ModelConstraint
from optimes._math_model.model_components.sets import ModelDimension
from optimes._math_model.model_components.variables import MARKET_VARIABLES


class ScenarioConstraints:
    def __init__(
        self,
        milp_model: EnergyMILPModel,
    ) -> None:
        self.model = milp_model
        self.scenario_params = milp_model.parameters.scenarios
        self.market_params = milp_model.parameters.markets
        self._include_generators = bool(milp_model.parameters.generators)
        self._include_batteries = bool(milp_model.parameters.batteries)
        self._include_markets = bool(milp_model.parameters.markets)

    @property
    def all(self) -> tuple[ModelConstraint, ...]:
        constraints = [
            self._get_power_balance_constraint(),
        ]

        if self._include_generators and self.scenario_params.available_capacity_profiles is not None:
            constraints.append(self._get_available_capacity_profiles_constraint())

        if self._include_markets:
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
            lhs += -self.model.battery_power_in.sum(ModelDimension.Batteries)

        if self._include_markets:
            lhs += -self.model.market_volume_sold.sum(ModelDimension.Markets)

        if self.scenario_params.load_profiles is not None:
            lhs += -self.scenario_params.load_profiles

        return ModelConstraint(
            name="power_balance_constraint",
            constraint=lhs == 0,  # pyright: ignore reportArgumentType
        )

    def _get_available_capacity_profiles_constraint(self) -> ModelConstraint:
        var_generator_power = self.model.generator_power
        expression = var_generator_power <= self.scenario_params.available_capacity_profiles  # pyright: ignore reportOperatorIssue # Validated before calling function
        return ModelConstraint(
            name="available_capacity_constraint",
            constraint=expression,
        )

    def _get_non_anticipativity_constraint(self) -> list[ModelConstraint]:
        """Non-anticipativity constraint ensuring variables have same values across scenarios.

        This constraint enforces that decision variables take the same values across
        all scenarios, reflecting that decisions are made before uncertainty is revealed.
        Only applies to markets where stage_fixed is True.
        """
        constraints = []
        stage_fixed_markets = self.market_params.stage_fixed  # pyright: ignore reportArgumentType

        for market_var in MARKET_VARIABLES:
            linopy_var = self.model.linopy_model.variables[market_var.var_name]
            market_with_fixed_stage_var = linopy_var.where(stage_fixed_markets, drop=True)
            market_with_fixed_stage_first_scenario_var = market_with_fixed_stage_var.isel({ModelDimension.Scenarios: 0})
            expression = market_with_fixed_stage_var - market_with_fixed_stage_first_scenario_var == 0
            constraints.append(
                ModelConstraint(
                    name=f"non_anticipativity_{market_var.var_name}_constraint",
                    constraint=expression,
                ),
            )

        return constraints
