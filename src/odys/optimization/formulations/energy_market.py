"""Model formulation of energy markets."""

from collections.abc import Sequence
from typing import ClassVar, Self

import linopy
from pydantic import BaseModel, ConfigDict

from odys.domain.entities.market import AllowedTradeDirection, EnergyMarket
from odys.domain.profiles import PriceProfile
from odys.optimization.constraints.constraints_group import constraint
from odys.optimization.constraints.model_constraint import ModelConstraint
from odys.optimization.formulations.base import FormulationInputs, VariableFormulation
from odys.parameters.context import ModelContext
from odys.parameters.dimensions import ModelDimension
from odys.parameters.entity_arrays import MarketArrays
from odys.parameters.vectorize import vectorize


class EnergyMarketVariables(BaseModel):
    """Decision variables of the energy markets."""

    model_config = ConfigDict(frozen=True, extra="forbid", arbitrary_types_allowed=True)

    sell_volume: linopy.Variable
    buy_volume: linopy.Variable
    trade_mode: linopy.Variable


class EnergyMarketFormulation(VariableFormulation[EnergyMarketVariables]):
    """Energy markets: volume limits, buy-or-sell exclusivity, trade direction and non-anticipativity."""

    sell_volume_name: ClassVar[str] = "market_sell_volume"
    buy_volume_name: ClassVar[str] = "market_buy_volume"
    trade_mode_name: ClassVar[str] = "market_trade_mode"

    def __init__(self, markets: Sequence[EnergyMarket], context: ModelContext) -> None:
        """Initialize with the energy markets of the system.

        Args:
            markets: The energy markets, at least one.
            context: The shared indexing of the problem.
        """
        super().__init__(context)
        self.coordinates = context.coordinates_of(ModelDimension.Markets)
        self.arrays = vectorize(MarketArrays, markets, self.coordinates)
        self.prices = context.profiles(PriceProfile, markets, ModelDimension.Markets)

    @classmethod
    def build(cls, inputs: FormulationInputs) -> Self | None:
        """Return the formulation of the energy markets, or None if there are none."""
        markets = inputs.of_type(EnergyMarket)
        return cls(markets, inputs.context) if markets else None

    def _create_variables(self, model: linopy.Model) -> EnergyMarketVariables:
        """Add the sell and buy volumes (MW, non-negative) and the binary trade mode (1 = selling)."""
        coords = self.context.variable_coords(self.coordinates)
        return EnergyMarketVariables(
            sell_volume=model.add_variables(name=self.sell_volume_name, coords=coords, lower=0.0),
            buy_volume=model.add_variables(name=self.buy_volume_name, coords=coords, lower=0.0),
            trade_mode=model.add_variables(name=self.trade_mode_name, coords=coords, binary=True),
        )

    @constraint
    def _get_market_max_sell_volume_constraint(self) -> ModelConstraint:
        """Sales per step are limited by the market's maximum trading volume."""
        return ModelConstraint(
            constraint=self.variables.sell_volume <= self.arrays.max_trading_volume_per_step,
            name="market_max_sell_volume_constraint",
        )

    @constraint
    def _get_market_max_buy_volume_constraint(self) -> ModelConstraint:
        """Purchases per step are limited by the market's maximum trading volume."""
        return ModelConstraint(
            constraint=self.variables.buy_volume <= self.arrays.max_trading_volume_per_step,
            name="market_max_buy_volume_constraint",
        )

    @constraint
    def _get_market_mutual_exclusivity_sell_constraint(self) -> ModelConstraint:
        """Selling requires `trade_mode` = 1, so a market cannot buy and sell in the same step."""
        return ModelConstraint(
            constraint=self.variables.sell_volume
            <= self.variables.trade_mode * self.arrays.max_trading_volume_per_step,
            name="market_mutual_exclusivity_sell_constraint",
        )

    @constraint
    def _get_market_mutual_exclusivity_buy_constraint(self) -> ModelConstraint:
        """Buying requires `trade_mode` = 0, the counterpart of the sell exclusivity constraint."""
        return ModelConstraint(
            constraint=self.variables.buy_volume + self.variables.trade_mode * self.arrays.max_trading_volume_per_step
            <= self.arrays.max_trading_volume_per_step,
            name="market_mutual_exclusivity_buy_constraint",
        )

    @constraint
    def _get_trade_direction_constraints(self) -> list[ModelConstraint]:
        """Forbid selling on buy-only markets and buying on sell-only markets."""
        buy_only = self.arrays.allowed_trade_direction == AllowedTradeDirection.BUY_ONLY
        sell_only = self.arrays.allowed_trade_direction == AllowedTradeDirection.SELL_ONLY
        return [
            ModelConstraint(
                constraint=(1 * self.variables.sell_volume.where(buy_only, drop=True)).to_constraint("=", 0),
                name="market_buy_only_constraint",
            ),
            ModelConstraint(
                constraint=(1 * self.variables.buy_volume.where(sell_only, drop=True)).to_constraint("=", 0),
                name="market_sell_only_constraint",
            ),
        ]

    @constraint
    def _get_non_anticipativity_constraint(self) -> list[ModelConstraint]:
        """On stage-fixed markets, every variable takes its first scenario's value in all scenarios.

        Stage-fixed markets (such as day-ahead) are committed before uncertainty is revealed.
        """
        variables = (
            (self.sell_volume_name, self.variables.sell_volume),
            (self.buy_volume_name, self.variables.buy_volume),
            (self.trade_mode_name, self.variables.trade_mode),
        )
        constraints = []
        for name, variable in variables:
            stage_fixed = variable.where(self.arrays.stage_fixed, drop=True)
            first_scenario = stage_fixed.isel({ModelDimension.Scenarios: 0})
            constraints.append(
                ModelConstraint(
                    name=f"non_anticipativity_{name}_constraint",
                    constraint=(stage_fixed - first_scenario).to_constraint("=", 0),
                ),
            )
        return constraints

    def power_injection(self) -> linopy.LinearExpression:
        """Return the net purchase (buy minus sell volume), summed over markets."""
        bought = self.variables.buy_volume.sum(ModelDimension.Markets)
        injection: linopy.LinearExpression = bought - self.variables.sell_volume.sum(ModelDimension.Markets)
        return injection

    def profit(self) -> linopy.LinearExpression:
        """Return the trading revenue per scenario: (sell minus buy volume) times step length times price."""
        energy_price = self.context.timestep_hours * self.prices
        revenue = self.variables.sell_volume * energy_price - self.variables.buy_volume * energy_price
        profit: linopy.LinearExpression = revenue.sum([ModelDimension.Time, ModelDimension.Markets])
        return profit
