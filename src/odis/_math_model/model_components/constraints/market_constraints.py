from odis._math_model.milp_model import EnergyMILPModel
from odis._math_model.model_components.constraints.model_constraint import ModelConstraint
from odis.energy_system_models.markets import TradeDirection


class MarketConstraints:
    def __init__(self, milp_model: EnergyMILPModel) -> None:
        self.model = milp_model
        self.params = milp_model.parameters.markets

    def _validate_market_parameters_exist(self) -> None:
        if self.params is None:
            msg = "No parameters specified."
            raise ValueError(msg)

    @property
    def all(self) -> tuple[ModelConstraint, ...]:
        if self.params is None:
            return ()
        constraints = [
            self._get_market_max_buy_volume_constraint(),
            self._get_market_max_sell_volume_constraint(),
            self._get_market_mutual_exclusivity_buy_constraint(),
            self._get_market_mutual_exclusivity_sell_constraint(),
            *self._get_trade_direction_constraints(),
        ]

        return tuple(constraints)

    def _get_market_max_sell_volume_constraint(self) -> ModelConstraint:
        constraint = self.model.market_sell_volume <= self.params.max_volume  # pyright: ignore reportOperatorIssue
        return ModelConstraint(
            constraint=constraint,
            name="market_max_sell_volume_constraint",
        )

    def _get_market_max_buy_volume_constraint(self) -> ModelConstraint:
        constraint = self.model.market_buy_volume <= self.params.max_volume  # pyright: ignore reportOperatorIssue
        return ModelConstraint(
            constraint=constraint,
            name="market_max_buy_volume_constraint",
        )

    def _get_market_mutual_exclusivity_sell_constraint(self) -> ModelConstraint:
        constraint = self.model.market_sell_volume <= self.model.market_trade_mode * self.params.max_volume  # pyright: ignore reportOperatorIssue
        return ModelConstraint(
            constraint=constraint,
            name="market_mutual_exclusivity_sell_constraint",
        )

    def _get_market_mutual_exclusivity_buy_constraint(self) -> ModelConstraint:
        constraint = (
            self.model.market_buy_volume + self.model.market_trade_mode * self.params.max_volume  # pyright: ignore reportOperatorIssue
            <= self.params.max_volume  # pyright: ignore optionalMemberAccess
        )
        return ModelConstraint(
            constraint=constraint,
            name="market_mutual_exclusivity_buy_constraint",
        )

    def _get_trade_direction_constraints(self) -> list[ModelConstraint]:
        """Generate constraints based on trade_direction parameter for each market."""
        constraints = []

        buy_only_mask = self.params.trade_direction == TradeDirection.BUY  # pyright: ignore reportOperatorIssue
        sell_constraint = self.model.market_sell_volume.where(buy_only_mask, drop=True) == 0
        constraints.append(
            ModelConstraint(
                constraint=sell_constraint,
                name="market_buy_only_constraint",
            ),
        )

        sell_only_mask = self.params.trade_direction == TradeDirection.SELL  # pyright: ignore reportOperatorIssue
        buy_constraint = self.model.market_buy_volume.where(sell_only_mask, drop=True) == 0
        constraints.append(
            ModelConstraint(
                constraint=buy_constraint,
                name="market_sell_only_constraint",
            ),
        )

        return constraints
