import pytest
from pydantic import ValidationError

from odys.domain.entities.market import EnergyMarket, TradeDirection

MAX_TRADING_VOLUME = 100.0
MAX_TRADING_VOLUME_LARGE = 200.0


@pytest.fixture
def market_base_params() -> dict:
    return {"name": "test_market", "max_trading_volume_per_step": MAX_TRADING_VOLUME}


def test_market_creation_with_defaults(market_base_params: dict) -> None:
    market = EnergyMarket(**market_base_params)
    assert market.name == "test_market"
    assert market.max_trading_volume_per_step == MAX_TRADING_VOLUME
    assert market.trade_direction == TradeDirection.BUY_AND_SELL
    assert market.stage_fixed is False


@pytest.mark.parametrize(
    ("param_name", "invalid_value", "expected_match"),
    [
        ("max_trading_volume_per_step", 0.0, "Input should be greater than 0"),
        ("max_trading_volume_per_step", -10.0, "Input should be greater than 0"),
    ],
)
def test_market_creation_with_invalid_parameter_raises_error(
    param_name: str,
    invalid_value: float,
    expected_match: str,
    market_base_params: dict,
) -> None:
    params = dict(market_base_params)
    params[param_name] = invalid_value
    with pytest.raises(ValidationError, match=expected_match):
        EnergyMarket(**params)


def test_market_creation_with_all_options() -> None:
    market = EnergyMarket(
        name="stage_market",
        max_trading_volume_per_step=MAX_TRADING_VOLUME_LARGE,
        trade_direction=TradeDirection.BUY_ONLY,
        stage_fixed=True,
    )
    assert market.max_trading_volume_per_step == MAX_TRADING_VOLUME_LARGE
    assert market.trade_direction == TradeDirection.BUY_ONLY
    assert market.stage_fixed is True


@pytest.mark.parametrize(
    "trade_direction",
    [
        TradeDirection.BUY_ONLY,
        TradeDirection.SELL_ONLY,
        TradeDirection.BUY_AND_SELL,
    ],
)
def test_market_creation_with_all_trade_directions(
    trade_direction: TradeDirection,
    market_base_params: dict,
) -> None:
    params = dict(market_base_params)
    params["trade_direction"] = trade_direction
    market = EnergyMarket(**params)
    assert market.trade_direction == trade_direction


def test_market_stage_fixed_defaults_to_false(market_base_params: dict) -> None:
    market = EnergyMarket(**market_base_params)
    assert market.stage_fixed is False


def test_market_stage_fixed_can_be_set_true(market_base_params: dict) -> None:
    params = dict(market_base_params)
    params["stage_fixed"] = True
    market = EnergyMarket(**params)
    assert market.stage_fixed is True
