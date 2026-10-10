"""Generic vectorization of entity fields into typed arrays."""

from collections.abc import Sequence
from typing import TypeVar

import numpy as np
import xarray as xr
from pydantic import BaseModel, ConfigDict

from odys.domain.exceptions import OdysError
from odys.parameters.coordinates import Coordinates


class EntityArrays(BaseModel):
    """Base of the typed array collections: frozen, holding `xr.DataArray` fields."""

    model_config = ConfigDict(frozen=True, extra="forbid", arbitrary_types_allowed=True)


ArraysT = TypeVar("ArraysT", bound=EntityArrays)


def vectorize(arrays_type: type[ArraysT], models: Sequence[BaseModel], coordinates: Coordinates) -> ArraysT:
    """Build one array per field of `arrays_type` from the same-named field of every model.

    Each field of `arrays_type` is an `xr.DataArray` named exactly like a field
    of the models, so a quantity carries the same name in the domain and in the
    model. The models are labelled by `coordinates`, in order. An unset optional
    field (`None`) becomes `NaN`, so optional numeric fields give float arrays.

    Args:
        arrays_type: The typed collection of arrays to build, such as `GeneratorArrays`.
        models: The entities (or value objects such as batteries) to read, one per label.
        coordinates: The labels of the models along their dimension.

    Returns:
        An instance of `arrays_type` with one array per field, along `coordinates.dimension`.

    Raises:
        OdysError: If there are no models, a model lacks a field of `arrays_type`,
            or the number of models differs from the number of labels.

    """
    if not models:
        msg = f"{arrays_type.__name__} requires at least one model to vectorize."
        raise OdysError(msg)
    if len(models) != len(coordinates.labels):
        msg = (
            f"Cannot vectorize {len(models)} models along "
            f"{len(coordinates.labels)} labels of '{coordinates.dimension}'."
        )
        raise OdysError(msg)
    missing = sorted({
        field for model in models for field in arrays_type.model_fields if field not in type(model).model_fields
    })
    if missing:
        msg = f"{arrays_type.__name__} reads fields the models do not have: {missing}."
        raise OdysError(msg)
    arrays = {
        field: xr.DataArray(
            [np.nan if (value := getattr(model, field)) is None else value for model in models],
            dims=coordinates.dimension,
            coords=coordinates.dimension_coordinates_map,
        )
        for field in arrays_type.model_fields
    }
    return arrays_type.model_validate(arrays)
