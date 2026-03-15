"""Configuration for CVaR (Conditional Value at Risk) risk measure."""

from pydantic import BaseModel, Field


class CVaRConfig(BaseModel):
    """Configuration for CVaR-augmented stochastic optimization.

    Adds a risk penalty to the objective: maximize E[profit] + weight * CVaR_alpha[profit].

    Args:
        confidence_level: The alpha parameter (e.g. 0.95 means we care about the worst 5% of scenarios).
        weight: How much to weight CVaR relative to expected profit. 0 = pure expected value.

    """

    confidence_level: float = Field(gt=0, lt=1)
    weight: float = Field(ge=0)
