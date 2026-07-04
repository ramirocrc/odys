"""Scenario definitions for deterministic and stochastic optimization.

A scenario represents one possible realization of the energy system's
exogenous inputs (load demand, generator availability, market prices).
When multiple scenarios are provided with associated probabilities
(stochastic optimization), the optimizer finds decisions that perform
well in expectation across all possible futures.
"""

from collections.abc import Mapping, Sequence

from pydantic import BaseModel, ConfigDict, Field

from odys.domain.exceptions import OdysValidationError


class Scenario(BaseModel):
    """One possible realization of the energy system's exogenous inputs.

    A scenario defines the time-series profiles for load demand, available
    generator capacity, and market prices that describe one possible future
    of the operating environment. All fields are keyed by asset name, and
    each sequence must have a length equal to the number of optimization
    timesteps.

    A single ``Scenario`` is used for deterministic optimization. For stochastic
    optimization, use :class:`StochasticScenario` instead.
    """

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
    """A scenario with an associated probability for stochastic optimization.

    A stochastic scenario represents one possible future of the energy system,
    with a unique name and a probability of occurrence. When multiple
    stochastic scenarios are provided, their probabilities must sum to 1.0
    and their names must be unique. The optimizer maximizes expected profit
    across all scenarios, weighted by probability.

    Attributes:
        name: Unique identifier for this scenario.
        probability: Probability of this scenario occurring, between 0 and 1.
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
