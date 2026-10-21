import pytest
from pydantic import ValidationError

from odys.domain.entities.flexible_load import FlexibleLoad
from odys.domain.exceptions import OdysValidationError

MIN_LOAD = 20.0
MAX_LOAD = 100.0
VALUE_OF_CONSUMPTION = 100.0


def test_flexible_load_creation() -> None:
    load = FlexibleLoad(name="test_flexible_load", value_of_consumption=VALUE_OF_CONSUMPTION)
    assert load.name == "test_flexible_load"
    assert load.value_of_consumption == VALUE_OF_CONSUMPTION
    assert load.min_load is None
    assert load.max_load is None


def test_flexible_load_requires_name() -> None:
    with pytest.raises(ValidationError):
        FlexibleLoad.model_validate({"value_of_consumption": VALUE_OF_CONSUMPTION})


@pytest.mark.parametrize("field", ["max_increase", "max_decrease"], ids=["max_increase", "max_decrease"])
def test_flexible_load_rejects_relative_bounds(field: str) -> None:
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        FlexibleLoad.model_validate({"name": "test_load", "value_of_consumption": VALUE_OF_CONSUMPTION, field: 10.0})


def test_flexible_load_limits() -> None:
    load = FlexibleLoad(
        name="test_load",
        min_load=MIN_LOAD,
        max_load=MAX_LOAD,
        value_of_consumption=VALUE_OF_CONSUMPTION,
    )
    assert load.min_load == MIN_LOAD
    assert load.max_load == MAX_LOAD


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
        FlexibleLoad.model_validate({"name": "test_load"})


def test_flexible_load_value_of_consumption_must_be_non_negative() -> None:
    with pytest.raises(ValidationError):
        FlexibleLoad(name="test_load", value_of_consumption=-1.0)


def test_flexible_load_zero_value_of_consumption_allowed() -> None:
    load = FlexibleLoad(name="test_load", value_of_consumption=0.0)
    assert load.value_of_consumption == 0.0
