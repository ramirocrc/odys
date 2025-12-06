import linopy
from pydantic import BaseModel


class ModelConstraint(BaseModel, arbitrary_types_allowed=True):
    constraint: linopy.Constraint
    name: str
