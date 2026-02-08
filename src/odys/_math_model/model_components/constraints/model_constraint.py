import linopy
from pydantic import BaseModel, ConfigDict


class ModelConstraint(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    constraint: linopy.Constraint
    name: str
