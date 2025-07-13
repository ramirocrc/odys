from enum import Enum, unique

import pyomo.environ as pyo
from pydantic import BaseModel


@unique
class EnergyModelSetName(Enum):
    TIME = "time"
    GENERATORS = "generators"
    BATTERIES = "batteries"


class PyomoSet(BaseModel, arbitrary_types_allowed=True, extra="forbid"):
    name: EnergyModelSetName
    component: pyo.Set
