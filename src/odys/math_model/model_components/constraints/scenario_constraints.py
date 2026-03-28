"""Scenario-level constraints for the optimization model."""

from odys.math_model.milp_model import EnergyMILPModel
from odys.math_model.model_components.constraints.constraints_group import ConstraintGroup, constraint
from odys.math_model.model_components.constraints.model_constraint import ModelConstraint
from odys.math_model.model_components.parameters.market_parameters import MarketParameters
from odys.math_model.model_components.sets import ModelDimension
from odys.math_model.model_components.variables import MARKET_VARIABLES


class ScenarioConstraints(ConstraintGroup):
    """Builds power balance, available capacity, and non-anticipativity constraints."""

    def __init__(
        self,
        milp_model: EnergyMILPModel,
        market_params: MarketParameters | None = None,
    ) -> None:
        """Initialize with the MILP model and optional market parameters."""
        self.model = milp_model
        self.scenario_params = milp_model.parameters.scenarios
        self.market_params = market_params
        self._include_generators = bool(milp_model.parameters.generators)
        self._include_storages = bool(milp_model.parameters.storages)
        self._include_markets = bool(market_params)

    @constraint
    def _get_power_balance_constraint(self) -> ModelConstraint:
        """Linopy power balance constraint ensuring supply equals demand.

        This constraint ensures that at each time period and scenario, the total power
        generation plus battery discharge equals the demand plus battery charging.
        """
        lhs = 0
        if self._include_generators:
            lhs += self.model.generator_power.sum(ModelDimension.Generators)

        if self._include_storages:
            lhs += self.model.storage_power_out.sum(ModelDimension.Storages)
            lhs += -self.model.storage_power_in.sum(ModelDimension.Storages)

        if self._include_markets:
            lhs += self.model.market_buy_volume.sum(ModelDimension.Markets)
            lhs += -self.model.market_sell_volume.sum(ModelDimension.Markets)

        if self.scenario_params.load_profiles is not None:
            lhs += -self.scenario_params.load_profiles

        return ModelConstraint(
            name="power_balance_constraint",
            constraint=lhs == 0,  # ty: ignore  # pyright: ignore[reportArgumentType]
        )

    @constraint
    def _get_available_capacity_profiles_constraint(self) -> list[ModelConstraint]:
        if not self._include_generators or self.scenario_params.available_capacity_profiles is None:
            return []
        expression = self.model.generator_power <= self.scenario_params.available_capacity_profiles
        return [
            ModelConstraint(
                name="available_capacity_constraint",
                constraint=expression,
            ),
        ]

    @constraint
    def _get_non_anticipativity_constraint(self) -> list[ModelConstraint]:
        """Non-anticipativity constraint ensuring variables have same values across scenarios.

        This constraint enforces that decision variables take the same values across
        all scenarios, reflecting that decisions are made before uncertainty is revealed.
        Only applies to markets where stage_fixed is True.
        """
        if self.market_params is None:
            return []

        constraints = []
        stage_fixed_markets = self.market_params.stage_fixed

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
