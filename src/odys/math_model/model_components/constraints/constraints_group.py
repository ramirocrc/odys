"""Constraint group base class with auto-registration of constraint methods."""

from collections.abc import Callable
from typing import Any, ClassVar

from linopy import Model

from odys.math_model.model_components.constraints.model_constraint import ModelConstraint


def constraint(
    fn: Callable[..., ModelConstraint | list[ModelConstraint]],
) -> Callable[..., ModelConstraint | list[ModelConstraint]]:
    """Mark a method as a constraint producer. Discovered automatically by ConstraintGroup."""
    fn._is_model_constraint = True  # type: ignore[attr-defined]  # noqa: SLF001
    return fn


class ConstraintGroup:
    """Base class for grouping related model constraints.

    Subclasses decorate constraint-producing methods with @constraint.
    These are collected at class definition time via __init_subclass__
    and invoked automatically by collect_constraints() / add_to_model().
    """

    _constraint_methods: ClassVar[tuple[str, ...]] = ()

    def __init_subclass__(cls, **kwargs: Any) -> None:  # noqa: ANN401
        """Register @constraint-decorated methods defined on this subclass."""
        super().__init_subclass__(**kwargs)
        cls._constraint_methods = tuple(
            name for name, attr in cls.__dict__.items() if getattr(attr, "_is_model_constraint", False)
        )

    def collect_constraints(self) -> list[ModelConstraint]:
        """Collect all @constraint-decorated methods. Preserves definition order."""
        results: list[ModelConstraint] = []
        for name in self._constraint_methods:
            result = getattr(self, name)()
            if isinstance(result, list):
                results.extend(result)
            else:
                results.append(result)
        return results

    def add_to_model(self, linopy_model: Model) -> None:
        """Collect all constraints and add them to the linopy model."""
        for c in self.collect_constraints():
            linopy_model.add_constraints(c.constraint, name=c.name)
