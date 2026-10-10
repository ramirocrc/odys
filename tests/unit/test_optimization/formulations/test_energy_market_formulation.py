"""Unit tests for the energy market formulation: variables, constraints, power injection and profit."""

import logging
from datetime import timedelta

import linopy
import pytest
import xarray as xr
from linopy.testing import assert_conequal, assert_linequal

from odys.domain.entities.fixed_load import FixedLoad
from odys.domain.entities.generator import Generator
from odys.domain.entities.market import AllowedTradeDirection, EnergyMarket
from odys.domain.entities.portfolio import AssetPortfolio
from odys.domain.exceptions import OdysError
from odys.domain.profiles import LoadProfile, PriceProfile
from odys.domain.scenario import Scenario
from odys.energy_system import EnergySystem
from odys.optimization.formulations.energy_market import EnergyMarketFormulation
from odys.optimization.model.model_builder import build_model
from odys.optimization.problem import OptimizationProblem

logger = logging.getLogger(__name__)


SINGLE_MARKET_PRICES = [10.0, 20.0, 30.0]
HOURS_PER_STEP = 1.0


@pytest.fixture
def market_buy_only() -> EnergyMarket:
    return EnergyMarket(
        name="market_buy",
        max_trading_volume_per_step=100.0,
        allowed_trade_direction=AllowedTradeDirection.BUY_ONLY,
    )


@pytest.fixture
def market_sell_only() -> EnergyMarket:
    return EnergyMarket(
        name="market_sell",
        max_trading_volume_per_step=150.0,
        allowed_trade_direction=AllowedTradeDirection.SELL_ONLY,
    )


@pytest.fixture
def market_buy_and_sell() -> EnergyMarket:
    return EnergyMarket(
        name="market_both",
        max_trading_volume_per_step=200.0,
        allowed_trade_direction=AllowedTradeDirection.BUY_AND_SELL,
    )


@pytest.fixture
def generator1() -> Generator:
    return Generator(name="gen1", nominal_power=100.0, variable_cost=20.0)


@pytest.fixture
def load1() -> FixedLoad:
    return FixedLoad(name="load1")


@pytest.fixture
def demand_profile_sample() -> list[float]:
    return [80.0, 100.0, 90.0]


@pytest.fixture
def time_index(demand_profile_sample: list[float]) -> list[int]:
    return list(range(len(demand_profile_sample)))


@pytest.fixture
def asset_portfolio_single_market(
    generator1: Generator,
    load1: FixedLoad,
) -> AssetPortfolio:
    return AssetPortfolio(assets=[generator1, load1])


@pytest.fixture
def asset_portfolio_mixed_markets(
    generator1: Generator,
    load1: FixedLoad,
) -> AssetPortfolio:
    return AssetPortfolio(assets=[generator1, load1])


@pytest.fixture
def energy_system_single_market(
    asset_portfolio_single_market: AssetPortfolio,
    demand_profile_sample: list[float],
    market_buy_and_sell: EnergyMarket,
    load1: FixedLoad,
) -> EnergySystem:
    return EnergySystem(
        portfolio=asset_portfolio_single_market,
        number_of_steps=len(demand_profile_sample),
        timestep=timedelta(hours=1),
        markets=market_buy_and_sell,
        scenarios=Scenario(
            profiles=(
                LoadProfile(load=load1, values=demand_profile_sample),
                PriceProfile(market=market_buy_and_sell, values=SINGLE_MARKET_PRICES),
            ),
        ),
    )


@pytest.fixture
def mixed_markets(
    market_buy_only: EnergyMarket,
    market_sell_only: EnergyMarket,
    market_buy_and_sell: EnergyMarket,
) -> tuple[EnergyMarket, ...]:
    return (market_buy_only, market_sell_only, market_buy_and_sell)


@pytest.fixture
def energy_system_mixed_markets(
    asset_portfolio_mixed_markets: AssetPortfolio,
    demand_profile_sample: list[float],
    mixed_markets: tuple[EnergyMarket, ...],
    load1: FixedLoad,
) -> EnergySystem:
    return EnergySystem(
        portfolio=asset_portfolio_mixed_markets,
        number_of_steps=len(demand_profile_sample),
        timestep=timedelta(hours=1),
        markets=mixed_markets,
        scenarios=Scenario(
            profiles=(
                LoadProfile(load=load1, values=demand_profile_sample),
                *(PriceProfile(market=market, values=[10, 20, 30]) for market in mixed_markets),
            ),
        ),
    )


@pytest.fixture
def problem_single_market(energy_system_single_market: EnergySystem) -> OptimizationProblem:
    return energy_system_single_market.build_problem()


@pytest.fixture
def problem_mixed_markets(energy_system_mixed_markets: EnergySystem) -> OptimizationProblem:
    return energy_system_mixed_markets.build_problem()


@pytest.fixture
def linopy_model_single_market(problem_single_market: OptimizationProblem) -> linopy.Model:
    return build_model(problem_single_market)


@pytest.fixture
def linopy_model_mixed_markets(problem_mixed_markets: OptimizationProblem) -> linopy.Model:
    return build_model(problem_mixed_markets)


class TestEnergyMarketVolumeConstraints:
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
            assert constraint_name in linopy_model_mixed_markets.constraints.data

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


class TestEnergyMarketConstraintsEdgeCases:
    def test_empty_markets_no_constraints(
        self,
        generator1: Generator,
        load1: FixedLoad,
        demand_profile_sample: list[float],
    ) -> None:
        portfolio = AssetPortfolio(assets=[generator1, load1])

        energy_system = EnergySystem(
            portfolio=portfolio,
            number_of_steps=len(demand_profile_sample),
            timestep=timedelta(hours=1),
            scenarios=Scenario(profiles=(LoadProfile(load=load1, values=demand_profile_sample),)),
        )

        problem = energy_system.build_problem()
        linopy_model = build_model(problem)

        keys = set(linopy_model.constraints)
        market_constraints = [c for c in keys if "market" in str(c)]
        assert len(market_constraints) == 0


class TestEnergyMarketFormulation:
    @pytest.fixture
    def formulation(
        self,
        problem_single_market: OptimizationProblem,
        linopy_model_single_market: linopy.Model,
    ) -> EnergyMarketFormulation:
        assert linopy_model_single_market is not None
        markets = problem_single_market.formulation_of(EnergyMarketFormulation)
        assert markets is not None
        return markets

    def test_variable_names_match_the_model(self, formulation: EnergyMarketFormulation) -> None:
        variables = formulation.variables
        assert variables.sell_volume.name == EnergyMarketFormulation.sell_volume_name
        assert variables.buy_volume.name == EnergyMarketFormulation.buy_volume_name
        assert variables.trade_mode.name == EnergyMarketFormulation.trade_mode_name

    def test_power_injection_is_net_purchase(
        self,
        formulation: EnergyMarketFormulation,
        linopy_model_single_market: linopy.Model,
    ) -> None:
        variables = linopy_model_single_market.variables
        expected = variables["market_buy_volume"].sum("market") - variables["market_sell_volume"].sum("market")
        assert_linequal(formulation.power_injection(), expected)

    def test_profit_is_trading_revenue(
        self,
        formulation: EnergyMarketFormulation,
        linopy_model_single_market: linopy.Model,
        market_buy_and_sell: EnergyMarket,
    ) -> None:
        variables = linopy_model_single_market.variables
        prices = xr.DataArray(
            [[SINGLE_MARKET_PRICES]],
            coords={"scenario": ["base"], "market": [market_buy_and_sell.name], "time": ["0", "1", "2"]},
        )
        expected = ((variables["market_sell_volume"] - variables["market_buy_volume"]) * HOURS_PER_STEP * prices).sum([
            "time",
            "market",
        ])
        assert_linequal(formulation.profit(), expected)

    def test_variables_before_add_variables_raise(self, problem_single_market: OptimizationProblem) -> None:
        markets = problem_single_market.formulation_of(EnergyMarketFormulation)
        assert markets is not None
        with pytest.raises(OdysError, match=r"EnergyMarketFormulation\.add_variables must run before"):
            _ = markets.variables
