"""Set definitions for energy system optimization models.

This module defines set names and types used in energy system
optimization models.
"""

from enum import Enum, unique

import pyomo.environ as pyo
from pydantic import BaseModel


@unique
class EnergyModelSetName(Enum):
    """Enumeration of set names used in the energy model."""

    TIME = "time"
    GENERATORS = "generators"
    BATTERIES = "batteries"


class SystemSet(BaseModel, arbitrary_types_allowed=True, extra="forbid"):
    """Container for Pyomo set components in the energy system model.

    This class wraps Pyomo sets with their corresponding names for
    organized model construction and management.
    """

    name: EnergyModelSetName
    component: pyo.Set
