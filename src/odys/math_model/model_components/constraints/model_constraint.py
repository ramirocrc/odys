"""Named constraint wrapper for linopy constraints."""

import linopy
from pydantic import BaseModel, ConfigDict


class ModelConstraint(BaseModel):
    """A named linopy constraint ready to be added to the model."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    constraint: linopy.Constraint
    name: str
