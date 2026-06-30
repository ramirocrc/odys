"""
Represents the deterministic conditions used during optimization.

A scenario defines the input data required for an optimization run,
including optional capacity profiles, load profiles, and market prices.
These values describe the operating conditions for the energy system.

Attributes:
    available_capacity_profiles: Available capacity values for each asset.
    load_profiles: Load demand profiles for each load.
    market_prices: Market price profiles used during optimization.
"""
from collections.abc import Mapping, Sequence

from pydantic import BaseModel, ConfigDict, Field

from odys.domain.exceptions import OdysValidationError


class Scenario(BaseModel):
    """Scenario conditions."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
    )

    available_capacity_profiles: Mapping[str, Sequence[float]] | None = Field(
        default=None,
        description="Available capacity for each asset.",
    )
    load_profiles: Mapping[str, Sequence[float]] | None = Field(default=None, description="Load profiles")
    market_prices: Mapping[str, Sequence[float]] | None = Field(default=None, description="Market prices.")


class StochasticScenario(Scenario):
    """
Represents a stochastic scenario used in optimization.

A stochastic scenario extends the base scenario with a unique name and
an associated probability. Multiple stochastic scenarios can be combined
to model uncertainty in optimization problems.

Attributes:
    name: Unique identifier for the scenario.
    probability: Probability assigned to the scenario. Must be between
        0 and 1.
"""
    name: str
    probability: float = Field(ge=0, le=1, description="Probability (0-1) of the scenario.")


def validate_sequence_of_stochastic_scenarios(
    scenarios: Sequence[StochasticScenario],
) -> None:
    """Validate that scenarios probabilities add up to 1.

    Args:
        scenarios: Sequence of scenarios.

    Raises:
        OdysValidationError: If sum of probabilities is different than 1.
    """
    sum_of_probabilities = sum(scenario.probability for scenario in scenarios)
    if sum_of_probabilities != 1.0:
        msg = f"Scenarios should add up to 1, but got sum = {sum_of_probabilities} instead."
        raise OdysValidationError(msg)

    scenario_names = [scenario.name for scenario in scenarios]
    duplicated_scenario_names = {scenario for scenario in scenario_names if scenario_names.count(scenario) > 1}
    if duplicated_scenario_names:
        msg = (
            f"Scenarios must have a unique name. The following names appear more than once: {duplicated_scenario_names}"
        )
        raise OdysValidationError(msg)
