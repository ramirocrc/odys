"""Tests for the automatic collection of @constraint methods."""

from typing import ClassVar

import linopy

from odys.optimization.constraints.constraints_group import ConstraintGroup, constraint
from odys.optimization.constraints.model_constraint import ModelConstraint

CONSTRAINT_NAME = "x_nonnegative_constraint"
VARIABLE_NAME = "x"


class _GroupWithUnhashableClassAttribute(ConstraintGroup):
    limits: ClassVar[dict[str, float]] = {"x": 1.0}

    def __init__(self, model: linopy.Model) -> None:
        self.model = model

    @constraint
    def x_nonnegative_constraint(self) -> ModelConstraint:
        expression = self.model.variables[VARIABLE_NAME].to_linexpr()
        return ModelConstraint(constraint=expression.to_constraint(">=", 0), name=CONSTRAINT_NAME)


def test_constraint_group_with_an_unhashable_class_attribute_collects_its_constraints() -> None:
    model = linopy.Model()
    model.add_variables(name=VARIABLE_NAME)

    constraints = _GroupWithUnhashableClassAttribute(model).collect_constraints()

    assert [collected.name for collected in constraints] == [CONSTRAINT_NAME]
