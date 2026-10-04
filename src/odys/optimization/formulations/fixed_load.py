"""Model formulation of fixed loads."""

from collections.abc import Sequence
from typing import Self

import xarray as xr

from odys.domain.entities.fixed_load import FixedLoad
from odys.domain.profiles import LoadProfile
from odys.optimization.formulations.base import Formulation, FormulationInputs
from odys.parameters.context import ModelContext
from odys.parameters.dimensions import ModelDimension


class FixedLoadFormulation(Formulation):
    """Fixed loads: inelastic demand that must be met, with no decision variables or constraints."""

    def __init__(self, fixed_loads: Sequence[FixedLoad], context: ModelContext) -> None:
        """Initialize with the fixed loads of the system.

        Args:
            fixed_loads: The fixed loads, at least one.
            context: The shared indexing of the problem.
        """
        super().__init__(context)
        self.demand = context.profiles(LoadProfile, fixed_loads, ModelDimension.FixedLoads)

    @classmethod
    def build(cls, inputs: FormulationInputs) -> Self | None:
        """Return the formulation of the fixed loads, or None if there are none."""
        fixed_loads = inputs.of_type(FixedLoad)
        return cls(fixed_loads, inputs.context) if fixed_loads else None

    def power_injection(self) -> xr.DataArray:
        """Return minus the total fixed-load demand, per scenario and time."""
        injection: xr.DataArray = -self.demand.sum(ModelDimension.FixedLoads)
        return injection
