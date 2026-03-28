"""Objective function configuration for energy system optimization.

Provides composable objective terms that users combine into an Objective.
The final objective is: maximize Σ weight_i * term_i(model).
"""

from pydantic import BaseModel, ConfigDict, Field


class ObjectiveTerm(BaseModel):
    """Base class for all objective terms."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    weight: float


class ProfitTerm(ObjectiveTerm):
    """Expected profit across scenarios. No extra config needed."""


class CVaRTerm(ObjectiveTerm):
    """Conditional Value at Risk penalty.

    Args:
        confidence_level: The alpha parameter (e.g. 0.95 means we care about the worst 5% of scenarios).
        weight: How much to weight CVaR relative to expected profit.

    """

    confidence_level: float = Field(gt=0, lt=1)


class Objective(BaseModel):
    """Objective function configuration.

    Args:
        profit: Expected profit term (always active).
        cvar: Optional CVaR risk penalty term.

    """

    profit: ProfitTerm = ProfitTerm(weight=1.0)
    cvar: CVaRTerm | None = None
