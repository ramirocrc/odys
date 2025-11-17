from optimes._math_model.milp_model import EnergyMILPModel
from optimes._math_model.model_components.constraints.model_constraint import ModelConstraint


class MarketConstraints:
    def __init__(self, milp_model: EnergyMILPModel) -> None:
        self.model = milp_model
        self.params = milp_model.parameters.markets

    def _validate_market_parameters_exist(self) -> None:
        if self.params is None:
            msg = "No  parameters specified."
            raise ValueError(msg)

    @property
    def all(self) -> tuple[ModelConstraint, ...]:
        if self.params is None:
            return ()
        return (
            self._get_market_max_volume_sold_constraint(),
            self._get_market_min_volume_sold_constraint(),
        )

    def _get_market_max_volume_sold_constraint(self) -> ModelConstraint:
        constraint = self.model.market_volume_sold <= self.params.max_volume  # pyright: ignore reportOperatorIssue
        return ModelConstraint(
            constraint=constraint,
            name="market_max_volume_sold_constraint",
        )

    def _get_market_min_volume_sold_constraint(self) -> ModelConstraint:
        constraint = self.model.market_volume_sold >= -self.params.max_volume  # pyright: ignore reportOperatorIssue
        return ModelConstraint(
            constraint=constraint,
            name="market_min_volume_sold_constraint",
        )
