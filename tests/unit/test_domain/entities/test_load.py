import pytest

from odys.domain.entities.load import Load, LoadType
from odys.domain.exceptions import OdysValidationError

VARIABLE_COST_TO_INCREASE = 10.0
VARIABLE_COST_TO_DECREASE = 5.0


@pytest.fixture
def fixed_load_base_params() -> dict:
    return {"name": "test_load"}


def test_load_creation_fixed_load_default(fixed_load_base_params: dict) -> None:
    load = Load(**fixed_load_base_params)
    assert load.name == "test_load"
    assert load.type == LoadType.Fixed
    assert load.variable_cost_to_increase is None
    assert load.variable_cost_to_decrease is None


def test_load_creation_flexible_load_with_costs() -> None:
    load = Load(
        name="flexible_load",
        type=LoadType.Flexible,
        variable_cost_to_increase=VARIABLE_COST_TO_INCREASE,
        variable_cost_to_decrease=VARIABLE_COST_TO_DECREASE,
    )
    assert load.type == LoadType.Flexible
    assert load.variable_cost_to_increase == VARIABLE_COST_TO_INCREASE
    assert load.variable_cost_to_decrease == VARIABLE_COST_TO_DECREASE


def test_load_creation_flexible_load_requires_explicit_type() -> None:
    load = Load(
        name="flexible_load",
        type=LoadType.Flexible,
        variable_cost_to_increase=VARIABLE_COST_TO_INCREASE,
        variable_cost_to_decrease=VARIABLE_COST_TO_DECREASE,
    )
    assert load.type == LoadType.Flexible


def test_fixed_load_with_variable_cost_to_increase_raises(
    fixed_load_base_params: dict,
) -> None:
    fixed_load_base_params["variable_cost_to_increase"] = VARIABLE_COST_TO_INCREASE
    with pytest.raises(
        OdysValidationError,
        match="`variable_cost_to_decrease` and `variable_cost_to_increase` are fields valid only for Flexible loads",
    ):
        Load(**fixed_load_base_params)


def test_fixed_load_with_variable_cost_to_decrease_raises(
    fixed_load_base_params: dict,
) -> None:
    fixed_load_base_params["variable_cost_to_decrease"] = VARIABLE_COST_TO_DECREASE
    with pytest.raises(
        OdysValidationError,
        match="`variable_cost_to_decrease` and `variable_cost_to_increase` are fields valid only for Flexible loads",
    ):
        Load(**fixed_load_base_params)


def test_flexible_load_missing_variable_cost_to_increase_raises() -> None:
    with pytest.raises(
        OdysValidationError,
        match="`variable_cost_to_decrease` and `variable_cost_to_increase` must be specified for Flexible loads",
    ):
        Load(
            name="flex_load",
            type=LoadType.Flexible,
            variable_cost_to_decrease=VARIABLE_COST_TO_DECREASE,
        )


def test_flexible_load_missing_variable_cost_to_decrease_raises() -> None:
    with pytest.raises(
        OdysValidationError,
        match="`variable_cost_to_decrease` and `variable_cost_to_increase` must be specified for Flexible loads",
    ):
        Load(
            name="flex_load",
            type=LoadType.Flexible,
            variable_cost_to_increase=VARIABLE_COST_TO_INCREASE,
        )


def test_flexible_load_with_only_one_cost_raises() -> None:
    with pytest.raises(
        OdysValidationError,
        match="`variable_cost_to_decrease` and `variable_cost_to_increase` must be specified for Flexible loads",
    ):
        Load(
            name="flex_load",
            type=LoadType.Flexible,
            variable_cost_to_increase=VARIABLE_COST_TO_INCREASE,
            variable_cost_to_decrease=None,
        )
