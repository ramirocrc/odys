import pytest
from pydantic import ValidationError

from odys.domain.entities.market import AllowedTradeDirection, EnergyMarket

MAX_TRADING_VOLUME = 100.0
MAX_TRADING_VOLUME_LARGE = 200.0


@pytest.fixture
def market_base_params() -> dict[str, object]:
    return {"name": "test_market", "max_trading_volume_per_step": MAX_TRADING_VOLUME}


def test_market_creation_with_defaults(market_base_params: dict[str, object]) -> None:
    market = EnergyMarket.model_validate(market_base_params)
    assert market.name == "test_market"
    assert market.max_trading_volume_per_step == MAX_TRADING_VOLUME
    assert market.allowed_trade_direction == AllowedTradeDirection.BUY_AND_SELL
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
    market_base_params: dict[str, object],
) -> None:
    params = dict(market_base_params)
    params[param_name] = invalid_value
    with pytest.raises(ValidationError, match=expected_match):
        EnergyMarket.model_validate(params)


def test_market_creation_with_all_options() -> None:
    market = EnergyMarket(
        name="stage_market",
        max_trading_volume_per_step=MAX_TRADING_VOLUME_LARGE,
        allowed_trade_direction=AllowedTradeDirection.BUY_ONLY,
        stage_fixed=True,
    )
    assert market.max_trading_volume_per_step == MAX_TRADING_VOLUME_LARGE
    assert market.allowed_trade_direction == AllowedTradeDirection.BUY_ONLY
    assert market.stage_fixed is True


@pytest.mark.parametrize(
    "allowed_trade_direction",
    [
        AllowedTradeDirection.BUY_ONLY,
        AllowedTradeDirection.SELL_ONLY,
        AllowedTradeDirection.BUY_AND_SELL,
    ],
)
def test_market_creation_with_all_trade_directions(
    allowed_trade_direction: AllowedTradeDirection,
    market_base_params: dict[str, object],
) -> None:
    params = dict(market_base_params)
    params["allowed_trade_direction"] = allowed_trade_direction
    market = EnergyMarket.model_validate(params)
    assert market.allowed_trade_direction == allowed_trade_direction


def test_market_stage_fixed_defaults_to_false(market_base_params: dict[str, object]) -> None:
    market = EnergyMarket.model_validate(market_base_params)
    assert market.stage_fixed is False


def test_market_stage_fixed_can_be_set_true(market_base_params: dict[str, object]) -> None:
    params = dict(market_base_params)
    params["stage_fixed"] = True
    market = EnergyMarket.model_validate(params)
    assert market.stage_fixed is True
