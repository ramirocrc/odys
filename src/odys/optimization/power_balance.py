"""The power balance: at every scenario and timestep, the net power into the bus is zero."""

from functools import reduce
from operator import add
from typing import assert_never

import linopy
import xarray as xr

from odys.domain.exceptions import OdysError
from odys.optimization.constraints.constraints_group import ConstraintGroup, constraint
from odys.optimization.constraints.model_constraint import ModelConstraint
from odys.optimization.model.milp_model import EnergyMILPModel


class PowerBalance(ConstraintGroup):
    """Builds the power balance from every entity type's net power injection.

    Every formulation contributes its `power_injection()`, in `FORMULATIONS` order;
    formulations outside the balance (charging) return None and are skipped.
    """

    def __init__(self, milp_model: EnergyMILPModel) -> None:
        """Initialize with the MILP model, whose problem holds the formulations."""
        self.model = milp_model

    @constraint
    def _get_power_balance_constraint(self) -> ModelConstraint:
        """Net power into the bus equals zero: supply equals demand."""
        variable_injections: list[linopy.LinearExpression] = []
        fixed_injections: list[xr.DataArray] = []
        for formulation in self.model.problem.formulations:
            match injection := formulation.power_injection():
                case linopy.LinearExpression():
                    variable_injections.append(injection)
                case xr.DataArray():
                    fixed_injections.append(injection)
                case None:
                    pass
                case _:
                    assert_never(injection)
        if not variable_injections:
            msg = "The power balance has no decision variable to balance."
            raise OdysError(msg)
        net_injection: linopy.LinearExpression = reduce(add, variable_injections)
        if fixed_injections:
            net_injection += reduce(add, fixed_injections)
        return ModelConstraint(
            name="power_balance_constraint",
            constraint=net_injection.to_constraint("=", 0),
        )
