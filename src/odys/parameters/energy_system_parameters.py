"""Parameter definitions for energy system optimization models.

This module defines EnergySystemParameters, which holds what the formulations
do not own yet: the shared context and the objective (until R3.5).
"""

from pydantic import BaseModel, ConfigDict

from odys.domain.objective import Objective
from odys.parameters.context import ModelContext


class EnergySystemParameters(BaseModel):
    """The shared context (coordinates, step length, probabilities) and the objective of the problem.

    Every entity type's parameters live in its formulation; this holds only what
    is not owned by one, until the objective terms become formulations (R3.5).
    """

    model_config = ConfigDict(frozen=True, extra="forbid", arbitrary_types_allowed=True)

    context: ModelContext
    objective: Objective
