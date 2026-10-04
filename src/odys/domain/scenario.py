"""Scenarios for deterministic and stochastic optimization.

A scenario represents one possible realization of the energy system's
exogenous inputs (load demand, generator availability, market prices),
given as typed profiles. A single scenario gives a deterministic problem.
Several weighted scenarios give a stochastic problem, where the optimizer
finds decisions that perform well in expectation across all of them.
"""

import math
from collections import Counter
from typing import Self, TypeVar

from pydantic import BaseModel, ConfigDict, Field, model_validator

from odys.domain.entities.base import EnergyEntity
from odys.domain.exceptions import OdysValidationError
from odys.domain.profiles import AnyProfile, Profile

ProfileT = TypeVar("ProfileT", bound=Profile)


class Scenario(BaseModel):
    """One possible realization of the energy system's exogenous inputs.

    A scenario holds the profiles (demand, available capacity, prices) of
    one possible future. Each entity has at most one profile of each kind,
    and every profile must have one value per optimization timestep.

    For deterministic optimization, pass a single scenario; its name and
    probability keep their defaults. For stochastic optimization, pass
    several scenarios with unique names and probabilities that sum to 1.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str = Field(default="base", description="Unique identifier of the scenario.")
    probability: float = Field(default=1.0, ge=0, le=1, description="Probability (0-1) of the scenario.")
    profiles: tuple[AnyProfile, ...] = Field(
        default=(),
        description="Time series of the scenario's entities.",
    )

    @model_validator(mode="after")
    def _validate_one_profile_per_entity_and_kind(self) -> Self:
        counts = Counter((type(profile).__name__, profile.entity.name) for profile in self.profiles)
        duplicates = sorted(f"{kind} for '{name}'" for (kind, name), count in counts.items() if count > 1)
        if duplicates:
            msg = f"Scenario '{self.name}' has more than one profile: {', '.join(duplicates)}."
            raise OdysValidationError(msg)
        return self

    def profiles_of(self, kind: type[ProfileT]) -> tuple[ProfileT, ...]:
        """Return all profiles of the given kind, in the order they were given.

        Args:
            kind: The profile type to select, such as `LoadProfile` or `PriceProfile`.

        Returns:
            The profiles that are instances of `kind`.

        """
        return tuple(profile for profile in self.profiles if isinstance(profile, kind))

    def profile_for(self, entity: EnergyEntity) -> Profile | None:
        """Return the profile that references the given entity, if the scenario has one.

        Args:
            entity: The asset or market to look up.

        Returns:
            The entity's profile, or None if the scenario has no profile for it.

        """
        return next((profile for profile in self.profiles if profile.entity == entity), None)


class ScenarioSet(BaseModel):
    """The scenarios of one optimization problem.

    Owns the rules that span scenarios: their probabilities sum to 1 (within
    floating-point tolerance) and their names are unique.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    scenarios: tuple[Scenario, ...]

    @model_validator(mode="after")
    def _validate_probabilities_sum_to_one(self) -> Self:
        sum_of_probabilities = sum(scenario.probability for scenario in self.scenarios)
        if not math.isclose(sum_of_probabilities, 1.0):
            msg = f"Scenarios should add up to 1, but got sum = {sum_of_probabilities} instead."
            raise OdysValidationError(msg)
        return self

    @model_validator(mode="after")
    def _validate_unique_names(self) -> Self:
        counts = Counter(scenario.name for scenario in self.scenarios)
        duplicated_scenario_names = {name for name, count in counts.items() if count > 1}
        if duplicated_scenario_names:
            msg = (
                "Scenarios must have a unique name. "
                f"The following names appear more than once: {duplicated_scenario_names}"
            )
            raise OdysValidationError(msg)
        return self

    @property
    def names(self) -> tuple[str, ...]:
        """Return the scenario names, in order."""
        return tuple(scenario.name for scenario in self.scenarios)
