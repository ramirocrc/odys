"""Scenario-level constraints for the optimization model."""

from odys.domain.exceptions import OdysValidationError
from odys.optimization.constraints.constraints_group import ConstraintGroup, constraint
from odys.optimization.constraints.model_constraint import ModelConstraint
from odys.optimization.model.milp_model import EnergyMILPModel
from odys.optimization.model.sets import ModelDimension
from odys.optimization.model.variables import MARKET_VARIABLES


class ScenarioConstraints(ConstraintGroup):
    """Builds power balance, available capacity, and non-anticipativity constraints."""

    def __init__(self, milp_model: EnergyMILPModel) -> None:
        """Initialize with the MILP model and optional market parameters."""
        self.model = milp_model
        self._params = milp_model.parameters

    @constraint
    def _get_power_balance_constraint(self) -> ModelConstraint:
        """Linopy power balance constraint ensuring supply equals demand."""
        lhs = 0

        if not self._params.generators.is_empty:
            lhs += self.model.generator_power.sum(ModelDimension.Generators)

        if not self._params.storages.is_empty:
            lhs += self.model.storage_power_out.sum(ModelDimension.Storages)
            lhs += -self.model.storage_power_in.sum(ModelDimension.Storages)

        if not self._params.markets.is_empty:
            lhs += self.model.market_buy_volume.sum(ModelDimension.Markets)
            lhs += -self.model.market_sell_volume.sum(ModelDimension.Markets)

        if self._params.scenarios.fixed_load_profiles is not None:
            lhs += -self._params.scenarios.fixed_load_profiles

        if not self._params.flexible_loads.is_empty:
            base_profiles = self._params.scenarios.flexible_load_base_profiles
            if base_profiles is None:
                msg = "Flexible loads exist but base profiles are missing"
                raise OdysValidationError(msg)
            lhs += -base_profiles.sum(ModelDimension.FlexibleLoads)
            lhs += -self.model.load_adjustment.sum(ModelDimension.FlexibleLoads)

        return ModelConstraint(
            name="power_balance_constraint",
            constraint=lhs == 0,  # pyright: ignore[reportArgumentType]
        )

    @constraint
    def _get_available_capacity_profiles_constraint(self) -> list[ModelConstraint]:
        if self._params.generators.is_empty or self._params.scenarios.available_capacity_profiles is None:
            return []
        expression = self.model.generator_power <= self._params.scenarios.available_capacity_profiles
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
        if self._params.markets.is_empty:
            return []

        constraints = []
        stage_fixed_markets = self._params.markets.stage_fixed

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
