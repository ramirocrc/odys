"""Market-related constraints for the optimization model."""

from odys.energy_system_models.markets import TradeDirection
from odys.math_model.milp_model import EnergyMILPModel
from odys.math_model.model_components.constraints.model_constraint import ModelConstraint


class MarketConstraints:
    """Builds constraints for market trading volumes, mutual exclusivity, and trade direction."""

    def __init__(self, milp_model: EnergyMILPModel) -> None:
        """Initialize with the MILP model containing market variables and parameters."""
        self.model = milp_model
        self.params = milp_model.parameters.markets

    def _validate_market_parameters_exist(self) -> None:
        if self.params is None:
            msg = "No parameters specified."
            raise ValueError(msg)

    @property
    def all(self) -> tuple[ModelConstraint, ...]:
        """Return all market constraints, or an empty tuple if no markets exist."""
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
        constraint = self.model.market_sell_volume <= self.params.max_volume  # ty: ignore # pyrefly: ignore  # pyright: ignore[reportOptionalMemberAccess]
        return ModelConstraint(
            constraint=constraint,
            name="market_max_sell_volume_constraint",
        )

    def _get_market_max_buy_volume_constraint(self) -> ModelConstraint:
        constraint = self.model.market_buy_volume <= self.params.max_volume  # ty: ignore # pyrefly: ignore  # pyright: ignore[reportOptionalMemberAccess]
        return ModelConstraint(
            constraint=constraint,
            name="market_max_buy_volume_constraint",
        )

    def _get_market_mutual_exclusivity_sell_constraint(self) -> ModelConstraint:
        constraint = self.model.market_sell_volume <= self.model.market_trade_mode * self.params.max_volume  # ty: ignore # pyrefly: ignore  # pyright: ignore[reportOptionalMemberAccess]
        return ModelConstraint(
            constraint=constraint,
            name="market_mutual_exclusivity_sell_constraint",
        )

    def _get_market_mutual_exclusivity_buy_constraint(self) -> ModelConstraint:
        constraint = (
            self.model.market_buy_volume + self.model.market_trade_mode * self.params.max_volume  # ty: ignore # pyrefly: ignore  # pyright: ignore[reportOptionalMemberAccess]
            <= self.params.max_volume  # ty: ignore # pyrefly: ignore  # pyright: ignore[reportOptionalMemberAccess]
        )
        return ModelConstraint(
            constraint=constraint,
            name="market_mutual_exclusivity_buy_constraint",
        )

    def _get_trade_direction_constraints(self) -> list[ModelConstraint]:
        """Generate constraints based on trade_direction parameter for each market."""
        constraints = []

        buy_only_mask = self.params.trade_direction == TradeDirection.BUY  # ty: ignore # pyrefly: ignore  # pyright: ignore[reportOptionalMemberAccess]
        sell_constraint = self.model.market_sell_volume.where(buy_only_mask, drop=True) == 0  # pyrefly: ignore
        constraints.append(
            ModelConstraint(
                constraint=sell_constraint,
                name="market_buy_only_constraint",
            ),
        )

        sell_only_mask = self.params.trade_direction == TradeDirection.SELL  # ty: ignore # pyrefly: ignore  # pyright: ignore[reportOptionalMemberAccess]
        buy_constraint = self.model.market_buy_volume.where(sell_only_mask, drop=True) == 0  # pyrefly: ignore
        constraints.append(
            ModelConstraint(
                constraint=buy_constraint,
                name="market_sell_only_constraint",
            ),
        )

        return constraints
