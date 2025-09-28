"""Scenario definitions for energy system optimization models."""

from collections.abc import Mapping, Sequence
from typing import Annotated

from pydantic import BaseModel, Field


class Scenario(BaseModel):
    """Stochastic scenario conditions."""

    probability: Annotated[float, Field(ge=0, le=0, description="Probability (0-1) of the scenario.")]
    available_capacity_profiles: Annotated[
        Mapping[str, Sequence[float]],
        Field(description="Mapping with available capacity scenario for each stochatic asset."),
    ]
