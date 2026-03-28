"""Market-related constraints for the optimization model."""

from odys.energy_system_models.markets import TradeDirection
from odys.math_model.milp_model import EnergyMILPModel
from odys.math_model.model_components.constraints.constraints_group import ConstraintGroup, constraint
from odys.math_model.model_components.constraints.model_constraint import ModelConstraint
from odys.math_model.model_components.parameters.market_parameters import MarketParameters


class MarketConstraints(ConstraintGroup):
    """Builds constraints for market trading volumes, mutual exclusivity, and trade direction."""

    def __init__(self, milp_model: EnergyMILPModel, params: MarketParameters) -> None:
        """Initialize with the MILP model and market parameters."""
        self.model = milp_model
        self.params = params

    @constraint
    def _get_market_max_sell_volume_constraint(self) -> ModelConstraint:
        return ModelConstraint(
            constraint=self.model.market_sell_volume <= self.params.max_volume,
            name="market_max_sell_volume_constraint",
        )

    @constraint
    def _get_market_max_buy_volume_constraint(self) -> ModelConstraint:
        return ModelConstraint(
            constraint=self.model.market_buy_volume <= self.params.max_volume,
            name="market_max_buy_volume_constraint",
        )

    @constraint
    def _get_market_mutual_exclusivity_sell_constraint(self) -> ModelConstraint:
        return ModelConstraint(
            constraint=self.model.market_sell_volume <= self.model.market_trade_mode * self.params.max_volume,
            name="market_mutual_exclusivity_sell_constraint",
        )

    @constraint
    def _get_market_mutual_exclusivity_buy_constraint(self) -> ModelConstraint:
        return ModelConstraint(
            constraint=self.model.market_buy_volume + self.model.market_trade_mode * self.params.max_volume
            <= self.params.max_volume,
            name="market_mutual_exclusivity_buy_constraint",
        )

    @constraint
    def _get_trade_direction_constraints(self) -> list[ModelConstraint]:
        """Generate constraints based on trade_direction parameter for each market."""
        constraints = []

        buy_only_mask = self.params.trade_direction == TradeDirection.BUY_ONLY
        sell_constraint = self.model.market_sell_volume.where(buy_only_mask, drop=True) == 0
        constraints.append(
            ModelConstraint(
                constraint=sell_constraint,
                name="market_buy_only_constraint",
            ),
        )

        sell_only_mask = self.params.trade_direction == TradeDirection.SELL_ONLY
        buy_constraint = self.model.market_buy_volume.where(sell_only_mask, drop=True) == 0
        constraints.append(
            ModelConstraint(
                constraint=buy_constraint,
                name="market_sell_only_constraint",
            ),
        )

        return constraints
