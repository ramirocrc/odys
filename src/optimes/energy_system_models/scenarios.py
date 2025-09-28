"""Scenario definitions for energy system optimization models."""

from collections.abc import Mapping, Sequence
from typing import Annotated

from pydantic import AfterValidator, BaseModel, Field


class Scenario(BaseModel):
    """Stochastic scenario conditions."""

    probability: Annotated[float, Field(ge=0, le=1, description="Probability (0-1) of the scenario.")]
    available_capacity_profiles: Annotated[
        Mapping[str, Sequence[float]],
        Field(description="Available capacity scenario for each stochatic asset."),
    ]


def validate_scenarios_probability_sum(scenarios: Sequence[Scenario]) -> Sequence[Scenario]:
    """Validate that scenarios probabilities add up to 1.

    Args:
        scenarios: Sequence of scenarios.

    Raises:
        ValueError: If sum of probabilities is different than 1.
    """
    sum_of_probabilities = sum(scenario.probability for scenario in scenarios)
    if sum_of_probabilities != 1.0:
        msg = f"Scenarios should add up to 1, but got sum = {sum_of_probabilities} instead."
        raise ValueError(msg)
    return scenarios


ScenariosVector = Annotated[Sequence[Scenario], AfterValidator(validate_scenarios_probability_sum)]
