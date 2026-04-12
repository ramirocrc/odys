import logging
from datetime import timedelta

import linopy
import pytest
from linopy.testing import assert_conequal

from odys.domain.entities.generator import Generator
from odys.domain.entities.load import Load
from odys.domain.entities.market import EnergyMarket, TradeDirection
from odys.domain.entities.portfolio import AssetPortfolio
from odys.domain.scenarios import Scenario
from odys.energy_system import EnergySystem
from odys.optimization.model.model_builder import build_model
from odys.optimization.parameters.parameters import EnergySystemParameters

logger = logging.getLogger(__name__)


@pytest.fixture
def market_buy_only() -> EnergyMarket:
    return EnergyMarket(
        name="market_buy",
        max_trading_volume_per_step=100.0,
        trade_direction=TradeDirection.BUY_ONLY,
    )


@pytest.fixture
def market_sell_only() -> EnergyMarket:
    return EnergyMarket(
        name="market_sell",
        max_trading_volume_per_step=150.0,
        trade_direction=TradeDirection.SELL_ONLY,
    )


@pytest.fixture
def market_buy_and_sell() -> EnergyMarket:
    return EnergyMarket(
        name="market_both",
        max_trading_volume_per_step=200.0,
        trade_direction=TradeDirection.BUY_AND_SELL,
    )


@pytest.fixture
def generator1() -> Generator:
    return Generator(name="gen1", nominal_power=100.0, variable_cost=20.0)


@pytest.fixture
def load1() -> Load:
    return Load(name="load1")


@pytest.fixture
def demand_profile_sample() -> list[float]:
    return [80.0, 100.0, 90.0]


@pytest.fixture
def time_index(demand_profile_sample: list[float]) -> list[int]:
    return list(range(len(demand_profile_sample)))


@pytest.fixture
def asset_portfolio_single_market(
    generator1: Generator,
    load1: Load,
) -> AssetPortfolio:
    return AssetPortfolio(assets=[generator1, load1])


@pytest.fixture
def asset_portfolio_mixed_markets(
    generator1: Generator,
    load1: Load,
) -> AssetPortfolio:
    return AssetPortfolio(assets=[generator1, load1])


@pytest.fixture
def energy_system_single_market(
    asset_portfolio_single_market: AssetPortfolio,
    demand_profile_sample: list[float],
    market_buy_and_sell: EnergyMarket,
) -> EnergySystem:
    return EnergySystem(
        portfolio=asset_portfolio_single_market,
        number_of_steps=len(demand_profile_sample),
        timestep=timedelta(hours=1),
        markets=market_buy_and_sell,
        scenarios=Scenario(
            available_capacity_profiles={},
            load_profiles={"load1": demand_profile_sample},
            market_prices={"market_both": [10, 20, 30]},
        ),
    )


@pytest.fixture
def energy_system_mixed_markets(
    asset_portfolio_mixed_markets: AssetPortfolio,
    demand_profile_sample: list[float],
    market_buy_only: EnergyMarket,
    market_sell_only: EnergyMarket,
    market_buy_and_sell: EnergyMarket,
) -> EnergySystem:
    return EnergySystem(
        portfolio=asset_portfolio_mixed_markets,
        number_of_steps=len(demand_profile_sample),
        timestep=timedelta(hours=1),
        markets=[market_buy_only, market_sell_only, market_buy_and_sell],
        scenarios=Scenario(
            available_capacity_profiles={},
            load_profiles={"load1": demand_profile_sample},
            market_prices={
                "market_buy": [10, 20, 30],
                "market_sell": [10, 20, 30],
                "market_both": [10, 20, 30],
            },
        ),
    )


@pytest.fixture
def params_single_market(energy_system_single_market: EnergySystem) -> EnergySystemParameters:
    return energy_system_single_market.build_parameters()


@pytest.fixture
def params_mixed_markets(energy_system_mixed_markets: EnergySystem) -> EnergySystemParameters:
    return energy_system_mixed_markets.build_parameters()


@pytest.fixture
def linopy_model_single_market(params_single_market: EnergySystemParameters) -> linopy.Model:
    return build_model(params_single_market).linopy_model


@pytest.fixture
def linopy_model_mixed_markets(params_mixed_markets: EnergySystemParameters) -> linopy.Model:
    return build_model(params_mixed_markets).linopy_model


class TestMarketConstraints:
    @pytest.fixture(autouse=True)
    def setup(
        self,
        linopy_model_single_market: linopy.Model,
        time_index: list[int],
    ) -> None:
        self.model = linopy_model_single_market
        self.time_index = time_index

    def test_market_max_sell_volume_constraint(self) -> None:
        constraint = self.model.constraints["market_max_sell_volume_constraint"]

        sell_volume = self.model.variables["market_sell_volume"]
        max_volume = 200.0

        expected_expr = sell_volume <= max_volume
        assert_conequal(expected_expr, constraint.lhs <= constraint.rhs)

    def test_market_max_buy_volume_constraint(self) -> None:
        constraint = self.model.constraints["market_max_buy_volume_constraint"]

        buy_volume = self.model.variables["market_buy_volume"]
        max_volume = 200.0

        expected_expr = buy_volume <= max_volume
        assert_conequal(expected_expr, constraint.lhs <= constraint.rhs)

    def test_market_mutual_exclusivity_sell_constraint(self) -> None:
        constraint = self.model.constraints["market_mutual_exclusivity_sell_constraint"]

        sell_volume = self.model.variables["market_sell_volume"]
        trade_mode = self.model.variables["market_trade_mode"]
        max_volume = 200.0

        expected_expr = sell_volume <= trade_mode * max_volume
        assert_conequal(expected_expr, constraint.lhs <= constraint.rhs)

    def test_market_mutual_exclusivity_buy_constraint(self) -> None:
        constraint = self.model.constraints["market_mutual_exclusivity_buy_constraint"]

        buy_volume = self.model.variables["market_buy_volume"]
        trade_mode = self.model.variables["market_trade_mode"]
        max_volume = 200.0

        expected_expr = buy_volume + trade_mode * max_volume <= max_volume
        assert_conequal(expected_expr, constraint.lhs <= constraint.rhs)


class TestTradeDirectionConstraints:
    @pytest.fixture(autouse=True)
    def setup(
        self,
        linopy_model_mixed_markets: linopy.Model,
        time_index: list[int],
    ) -> None:
        self.model = linopy_model_mixed_markets
        self.time_index = time_index

    def test_market_buy_only_constraint(self) -> None:
        constraint = self.model.constraints["market_buy_only_constraint"]

        self.model.variables["market_sell_volume"]
        assert "market_buy" in constraint.coords["market"]

        assert constraint.lhs.coords["market"].values == "market_buy"

    def test_market_sell_only_constraint(self) -> None:
        constraint = self.model.constraints["market_sell_only_constraint"]

        self.model.variables["market_buy_volume"]
        assert "market_sell" in constraint.coords["market"]

        assert constraint.lhs.coords["market"].values == "market_sell"


class TestMultipleMarketsWithDifferentDirections:
    def test_all_constraints_present_for_mixed_markets(
        self,
        linopy_model_mixed_markets: linopy.Model,
    ) -> None:
        expected_constraints = [
            "market_max_sell_volume_constraint",
            "market_max_buy_volume_constraint",
            "market_mutual_exclusivity_sell_constraint",
            "market_mutual_exclusivity_buy_constraint",
            "market_buy_only_constraint",
            "market_sell_only_constraint",
        ]

        for constraint_name in expected_constraints:
            assert constraint_name in linopy_model_mixed_markets.constraints

    def test_market_variables_created_for_each_market(
        self,
        linopy_model_mixed_markets: linopy.Model,
    ) -> None:
        sell_volume = linopy_model_mixed_markets.variables["market_sell_volume"]
        buy_volume = linopy_model_mixed_markets.variables["market_buy_volume"]
        trade_mode = linopy_model_mixed_markets.variables["market_trade_mode"]

        assert "market_buy" in sell_volume.coords["market"]
        assert "market_sell" in sell_volume.coords["market"]
        assert "market_both" in sell_volume.coords["market"]

        assert "market_buy" in buy_volume.coords["market"]
        assert "market_sell" in buy_volume.coords["market"]
        assert "market_both" in buy_volume.coords["market"]

        assert "market_buy" in trade_mode.coords["market"]
        assert "market_sell" in trade_mode.coords["market"]
        assert "market_both" in trade_mode.coords["market"]


class TestMarketConstraintsEdgeCases:
    def test_empty_markets_no_constraints(
        self,
        generator1: Generator,
        load1: Load,
        demand_profile_sample: list[float],
    ) -> None:
        portfolio = AssetPortfolio(assets=[generator1, load1])

        energy_system = EnergySystem(
            portfolio=portfolio,
            number_of_steps=len(demand_profile_sample),
            timestep=timedelta(hours=1),
            scenarios=Scenario(
                available_capacity_profiles={},
                load_profiles={"load1": demand_profile_sample},
            ),
        )

        params = energy_system.build_parameters()
        linopy_model = build_model(params).linopy_model

        market_constraints = [c for c in linopy_model.constraints.labels if "market" in c]
        assert len(market_constraints) == 0
