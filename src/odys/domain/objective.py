"""Objective function configuration for energy system optimization.

Provides composable objective terms that users combine into an Objective.
The final objective is: maximize Σ weight_i * term_i(model).
"""

from pydantic import BaseModel, ConfigDict, Field


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

    weight: float = Field(ge=0)


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

    confidence_level: float = Field(gt=0, lt=1)


class Objective(BaseModel):
    """Configuration for the optimization objective.

    Combines one or more objective terms into a single objective function.
    The profit term is required, while the CVaR term is optional and can be
    used to balance expected profit against risk.

    Attributes:
        profit: Objective term that maximizes expected profit.
        cvar: Optional CVaR objective term used to penalize risk.
    """

    profit: ProfitTerm
    cvar: CVaRTerm | None = None
