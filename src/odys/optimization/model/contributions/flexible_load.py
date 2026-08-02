"""Flexible load contributions to power balance and per-scenario profit."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from odys.domain.exceptions import OdysValidationError
from odys.optimization.model.sets import ModelDimension

if TYPE_CHECKING:
    import linopy

    from odys.optimization.model.milp_model import EnergyMILPModel
    from odys.optimization.parameters.parameters import EnergySystemParameters


def flexible_load_power_balance_terms(
    model: EnergyMILPModel,
    params: EnergySystemParameters,
) -> linopy.LinearExpression:
    """Net withdrawal from flexible loads (base + adjustment), reduced to (scenario, time)."""
    base_profiles = params.scenarios.flexible_load_base_profiles
    if base_profiles is None:
        msg = "Flexible loads exist but base profiles are missing"
        raise OdysValidationError(msg)
    return cast(
        "linopy.LinearExpression",
        -(
            base_profiles.sum(ModelDimension.FlexibleLoads)
            + model.vars.load_adjustment.sum(ModelDimension.FlexibleLoads)
        ),
    )


def flexible_load_profit_terms(
    model: EnergyMILPModel,
    params: EnergySystemParameters,
) -> linopy.LinearExpression:
    """Value of flexible-load adjustment as profit, reduced to (scenario,)."""
    return (model.vars.load_adjustment * params.flexible_loads.value_of_consumption).sum(
        [ModelDimension.Time, ModelDimension.FlexibleLoads],
    )
