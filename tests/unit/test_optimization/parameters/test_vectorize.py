"""Unit tests for generic vectorization of entity fields into typed arrays."""

import pytest
import xarray as xr
from pydantic import BaseModel

from odys.domain.entities.battery import Battery
from odys.domain.entities.charger import Charger
from odys.domain.entities.flexible_load import FlexibleLoad
from odys.domain.entities.generator import Generator
from odys.domain.entities.market import EnergyMarket
from odys.domain.exceptions import OdysError
from odys.parameters.coordinates import Coordinates
from odys.parameters.dimensions import ModelDimension
from odys.parameters.entity_arrays import (
    BatteryArrays,
    ChargerArrays,
    FlexibleLoadArrays,
    GeneratorArrays,
    MarketArrays,
)
from odys.parameters.vectorize import EntityArrays, vectorize

FIRST_POWER = 10.0
SECOND_POWER = 20.0
GENERATORS = [
    Generator(name="gen_b", nominal_power=SECOND_POWER, variable_cost=2.0),
    Generator(name="gen_a", nominal_power=FIRST_POWER, variable_cost=1.0),
]


class _ArraysWithUnknownField(EntityArrays):
    nominal_power: xr.DataArray
    not_a_generator_field: xr.DataArray


def test_vectorize_follows_model_order_along_the_dimension() -> None:
    arrays = vectorize(GeneratorArrays, GENERATORS, Coordinates.of_entities(ModelDimension.Generators, GENERATORS))

    expected = xr.DataArray([SECOND_POWER, FIRST_POWER], coords={"generator": ["gen_b", "gen_a"]})
    xr.testing.assert_equal(arrays.nominal_power, expected)


def test_vectorize_rejects_a_field_the_models_lack() -> None:
    with pytest.raises(OdysError, match=r"_ArraysWithUnknownField reads fields the models do not have: \['not_a"):
        vectorize(_ArraysWithUnknownField, GENERATORS, Coordinates.of_entities(ModelDimension.Generators, GENERATORS))


def test_vectorize_rejects_a_label_count_mismatch() -> None:
    one_label = Coordinates(dimension=ModelDimension.Generators, labels=("gen_a",))
    with pytest.raises(OdysError, match="Cannot vectorize 2 models along 1 labels of 'generator'"):
        vectorize(GeneratorArrays, GENERATORS, one_label)


@pytest.mark.parametrize(
    ("arrays_type", "model_type"),
    [
        (GeneratorArrays, Generator),
        (BatteryArrays, Battery),
        (FlexibleLoadArrays, FlexibleLoad),
        (MarketArrays, EnergyMarket),
        (ChargerArrays, Charger),
    ],
    ids=lambda value: value.__name__,
)
def test_arrays_fields_are_fields_of_their_model(arrays_type: type[EntityArrays], model_type: type[BaseModel]) -> None:
    assert set(arrays_type.model_fields) <= set(model_type.model_fields)
