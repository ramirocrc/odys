"""Scenario definitions for energy system optimization models."""

from collections.abc import Mapping, Sequence
from typing import Annotated

from pydantic import AfterValidator, BaseModel, Field


class Scenario(BaseModel):
    """Scenario conditions."""

    available_capacity_profiles: Annotated[
        Mapping[str, Sequence[float]],
        Field(description="Available capacity for each asset."),
    ]


class SctochasticScenario(BaseModel):
    """Stochastic scenario conditions."""

    name: str
    probability: Annotated[float, Field(ge=0, le=1, description="Probability (0-1) of the scenario.")]
    available_capacity_profiles: Annotated[
        Mapping[str, Sequence[float]],
        Field(description="Available capacity scenario for each stochatic asset."),
    ]


def validate_sequence_of_scenarios(scenarios: Sequence[SctochasticScenario]) -> Sequence[SctochasticScenario]:
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

    scenario_names = [scenario.name for scenario in scenarios]
    duplicated_scenario_names = {scenario for scenario in scenario_names if scenario_names.count(scenario) > 1}
    if duplicated_scenario_names:
        msg = (
            f"Scenarios must have a unique name. The following names appear more than once: {duplicated_scenario_names}"
        )
        raise ValueError(msg)
    return scenarios


ScenariosSequence = Annotated[Sequence[SctochasticScenario], AfterValidator(validate_sequence_of_scenarios)]
