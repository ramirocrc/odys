import pytest
from pydantic import ValidationError

from odys.domain.entities.fixed_load import FixedLoad


def test_fixed_load_creation() -> None:
    load = FixedLoad(name="test_load")
    assert load.name == "test_load"


def test_fixed_load_requires_name() -> None:
    with pytest.raises(ValidationError, match="name"):
        FixedLoad()  # ty: ignore [missing-argument] # pyrefly: ignore [missing-argument]
