import pytest
from pydantic import ValidationError

from odys.domain.entities.flexible_load import FlexibleLoad

MAX_INCREASE = 50.0
MAX_DECREASE = 30.0
VALUE_OF_CONSUMPTION = 100.0


def test_flexible_load_creation() -> None:
    load = FlexibleLoad(
        name="test_flexible_load",
        max_increase=MAX_INCREASE,
        max_decrease=MAX_DECREASE,
        value_of_consumption=VALUE_OF_CONSUMPTION,
    )
    assert load.name == "test_flexible_load"
    assert load.max_increase == MAX_INCREASE
    assert load.max_decrease == MAX_DECREASE
    assert load.value_of_consumption == VALUE_OF_CONSUMPTION


def test_flexible_load_requires_name() -> None:
    with pytest.raises(ValidationError):
        FlexibleLoad(  # ty: ignore [missing-argument] # pyrefly: ignore [missing-argument]
            max_increase=MAX_INCREASE,
            max_decrease=MAX_DECREASE,
            value_of_consumption=VALUE_OF_CONSUMPTION,
        )


def test_flexible_load_requires_max_increase() -> None:
    with pytest.raises(ValidationError):
        FlexibleLoad(  # ty: ignore [missing-argument]# pyrefly: ignore [missing-argument]
            name="test_load",
            max_decrease=MAX_DECREASE,
            value_of_consumption=VALUE_OF_CONSUMPTION,
        )


def test_flexible_load_requires_max_decrease() -> None:
    with pytest.raises(ValidationError):
        FlexibleLoad(  # ty: ignore [missing-argument]# pyrefly: ignore [missing-argument]
            name="test_load",
            max_increase=MAX_INCREASE,
            value_of_consumption=VALUE_OF_CONSUMPTION,
        )


def test_flexible_load_requires_value_of_consumption() -> None:
    with pytest.raises(ValidationError):
        FlexibleLoad(  # ty: ignore [missing-argument]# pyrefly: ignore [missing-argument]
            name="test_load",
            max_increase=MAX_INCREASE,
            max_decrease=MAX_DECREASE,
        )


def test_flexible_load_max_increase_must_be_positive() -> None:
    with pytest.raises(ValidationError):
        FlexibleLoad(
            name="test_load",
            max_increase=0.0,
            max_decrease=MAX_DECREASE,
            value_of_consumption=VALUE_OF_CONSUMPTION,
        )


def test_flexible_load_max_decrease_must_be_positive() -> None:
    with pytest.raises(ValidationError):
        FlexibleLoad(
            name="test_load",
            max_increase=MAX_INCREASE,
            max_decrease=0.0,
            value_of_consumption=VALUE_OF_CONSUMPTION,
        )


def test_flexible_load_value_of_consumption_must_be_non_negative() -> None:
    with pytest.raises(ValidationError):
        FlexibleLoad(
            name="test_load",
            max_increase=MAX_INCREASE,
            max_decrease=MAX_DECREASE,
            value_of_consumption=-1.0,
        )


def test_flexible_load_zero_value_of_consumption_allowed() -> None:
    load = FlexibleLoad(
        name="test_load",
        max_increase=MAX_INCREASE,
        max_decrease=MAX_DECREASE,
        value_of_consumption=0.0,
    )
    assert load.value_of_consumption == 0.0
