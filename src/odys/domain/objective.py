"""Objective function configuration for energy system optimization.

Provides composable objective terms that users combine into an Objective.
The final objective is: maximize Σ weight_i * term_i(model).
"""

from typing import Self, TypeVar

from pydantic import BaseModel, ConfigDict, Field, model_validator

from odys.domain.exceptions import OdysValidationError


class ObjectiveTerm(BaseModel):
    """Base class for all objective terms used in the optimization objective.

    Each objective term contributes to the final objective function through
    its associated weight. Subclasses define the specific metric or penalty
    that should be optimized.

    Attributes:
        weight: Relative importance of this objective term in the overall
            objective function. Must be non-negative; a weight of 0 keeps the
            term in the config while excluding it from the objective.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    weight: float = Field(
        ge=0,
        description="Relative importance of this objective term in the overall objective function.",
    )


class ProfitTerm(ObjectiveTerm):
    """Represents the expected profit objective across all scenarios.

    This objective term maximizes the expected profit of the optimization
    model. No additional configuration is required beyond the inherited
    weight attribute.
    """


class CVaRTerm(ObjectiveTerm):
    """Represents a Conditional Value at Risk (CVaR) penalty term.

    CVaR is used to reduce exposure to low-probability, high-impact losses.
    The confidence level determines the portion of the distribution used
    when evaluating risk.

    Attributes:
        confidence_level: Confidence level used for the CVaR calculation.
            Must be greater than 0 and less than 1.
    """

    confidence_level: float = Field(
        gt=0,
        lt=1,
        description="Confidence level used for the CVaR calculation. Must be greater than 0 and less than 1.",
    )


TermT = TypeVar("TermT", bound=ObjectiveTerm)


class Objective(BaseModel):
    """Configuration for the optimization objective.

    Combines objective terms into a single objective function to maximize:
    Σ weight_i * term_i. A `ProfitTerm` is required; a `CVaRTerm` is optional
    and balances expected profit against risk. Each term type appears at
    most once. The default maximizes expected profit.

    Example:
        >>> Objective(terms=(ProfitTerm(weight=1.0), CVaRTerm(weight=0.5, confidence_level=0.95)))

    Attributes:
        terms: The objective terms, at most one of each type.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    terms: tuple[ProfitTerm | CVaRTerm, ...] = Field(
        default=(ProfitTerm(weight=1.0),),
        description="The objective terms, at most one of each type. A ProfitTerm is required.",
    )

    @model_validator(mode="after")
    def _validate_one_term_per_type(self) -> Self:
        duplicates = [kind.__name__ for kind in (ProfitTerm, CVaRTerm) if len(self._terms_of(kind)) > 1]
        if duplicates:
            msg = f"Objective has more than one term of type: {duplicates}."
            raise OdysValidationError(msg)
        return self

    @model_validator(mode="after")
    def _validate_profit_term_present(self) -> Self:
        if self.term_of(ProfitTerm) is None:
            msg = "Objective must include a ProfitTerm."
            raise OdysValidationError(msg)
        return self

    def _terms_of(self, kind: type[TermT]) -> tuple[TermT, ...]:
        return tuple(term for term in self.terms if isinstance(term, kind))

    def term_of(self, kind: type[TermT]) -> TermT | None:
        """Return the term of the given type, if the objective has one.

        Args:
            kind: The term type to look up, such as `CVaRTerm`.

        Returns:
            The term, or None if the objective has no term of that type.

        """
        return next(iter(self._terms_of(kind)), None)
