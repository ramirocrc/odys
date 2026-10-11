import pytest
from pydantic import ValidationError

from odys.domain.entities.flexible_load import FlexibleLoad
from odys.domain.exceptions import OdysValidationError

MAX_INCREASE = 50.0
MAX_DECREASE = 30.0
MIN_LOAD = 20.0
MAX_LOAD = 100.0
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
        FlexibleLoad.model_validate(
            {
                "max_increase": MAX_INCREASE,
                "max_decrease": MAX_DECREASE,
                "value_of_consumption": VALUE_OF_CONSUMPTION,
            },
        )


def test_flexible_load_requires_upper_bound() -> None:
    with pytest.raises(OdysValidationError, match="needs an upper bound: set max_increase or max_load"):
        FlexibleLoad(name="test_load", max_decrease=MAX_DECREASE, value_of_consumption=VALUE_OF_CONSUMPTION)


def test_flexible_load_requires_lower_bound() -> None:
    with pytest.raises(OdysValidationError, match="needs a lower bound: set max_decrease or min_load"):
        FlexibleLoad(name="test_load", max_increase=MAX_INCREASE, value_of_consumption=VALUE_OF_CONSUMPTION)


def test_flexible_load_absolute_bounds_only() -> None:
    load = FlexibleLoad(
        name="test_load",
        min_load=MIN_LOAD,
        max_load=MAX_LOAD,
        value_of_consumption=VALUE_OF_CONSUMPTION,
    )
    assert load.min_load == MIN_LOAD
    assert load.max_load == MAX_LOAD
    assert load.max_increase is None
    assert load.max_decrease is None


def test_flexible_load_mixed_bounds_per_side() -> None:
    load = FlexibleLoad(
        name="test_load",
        min_load=MIN_LOAD,
        max_increase=MAX_INCREASE,
        value_of_consumption=VALUE_OF_CONSUMPTION,
    )
    assert load.min_load == MIN_LOAD
    assert load.max_increase == MAX_INCREASE


def test_flexible_load_absolute_and_relative_on_same_side_allowed() -> None:
    load = FlexibleLoad(
        name="test_load",
        max_increase=MAX_INCREASE,
        max_decrease=MAX_DECREASE,
        min_load=MIN_LOAD,
        max_load=MAX_LOAD,
        value_of_consumption=VALUE_OF_CONSUMPTION,
    )
    assert load.min_load == MIN_LOAD
    assert load.max_decrease == MAX_DECREASE


def test_flexible_load_min_load_must_not_exceed_max_load() -> None:
    with pytest.raises(OdysValidationError, match=r"min_load \(101.0\) must be ≤ max_load \(100.0\)"):
        FlexibleLoad(
            name="test_load",
            min_load=MAX_LOAD + 1.0,
            max_load=MAX_LOAD,
            value_of_consumption=VALUE_OF_CONSUMPTION,
        )


def test_flexible_load_min_load_equal_to_max_load_allowed() -> None:
    load = FlexibleLoad(
        name="test_load",
        min_load=MAX_LOAD,
        max_load=MAX_LOAD,
        value_of_consumption=VALUE_OF_CONSUMPTION,
    )
    assert load.min_load == load.max_load


def test_flexible_load_min_load_must_be_non_negative() -> None:
    with pytest.raises(ValidationError):
        FlexibleLoad(name="test_load", min_load=-1.0, max_load=MAX_LOAD, value_of_consumption=VALUE_OF_CONSUMPTION)


def test_flexible_load_zero_min_load_allowed() -> None:
    load = FlexibleLoad(name="test_load", min_load=0.0, max_load=MAX_LOAD, value_of_consumption=VALUE_OF_CONSUMPTION)
    assert load.min_load == 0.0


def test_flexible_load_max_load_must_be_positive() -> None:
    with pytest.raises(ValidationError):
        FlexibleLoad(name="test_load", min_load=0.0, max_load=0.0, value_of_consumption=VALUE_OF_CONSUMPTION)


def test_flexible_load_requires_value_of_consumption() -> None:
    with pytest.raises(ValidationError):
        FlexibleLoad.model_validate(
            {
                "name": "test_load",
                "max_increase": MAX_INCREASE,
                "max_decrease": MAX_DECREASE,
            },
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
