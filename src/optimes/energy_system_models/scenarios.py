"""Scenario definitions for energy system optimization models."""

from collections.abc import Sequence
from typing import Annotated

from pydantic import BaseModel, Field


class Scenario(BaseModel):
    """Stochastic scenario conditions."""

    probability: Sequence[Annotated[float, Field(ge=0, le=0)]]
