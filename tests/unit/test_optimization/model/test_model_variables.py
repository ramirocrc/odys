"""G12: ModelVariables typed view stays in sync with ModelVariable specs."""

from odys.optimization.model.milp_model import ModelVariables
from odys.optimization.model.variables import ModelVariable


def test_linopy_names_are_unique() -> None:
    names = [member.var_name for member in ModelVariable]
    assert len(names) == len(set(names))


def test_typed_fields_match_linopy_names() -> None:
    assert set(ModelVariables.__annotations__) == {member.var_name for member in ModelVariable}
