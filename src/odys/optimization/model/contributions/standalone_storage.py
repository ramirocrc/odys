"""Standalone storage contributions to power balance and per-scenario profit."""

from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING

from odys.optimization.model.sets import ModelDimension

if TYPE_CHECKING:
    import linopy

    from odys.optimization.model.milp_model import EnergyMILPModel
    from odys.optimization.parameters.parameters import EnergySystemParameters


def standalone_storage_power_balance_terms(
    model: EnergyMILPModel,
    params: EnergySystemParameters,
) -> linopy.LinearExpression:
    """Net power injection from standalone storage, reduced to (scenario, time)."""
    del params
    return model.vars.standalone_storage_power_out.sum(
        ModelDimension.StandaloneStorages,
    ) - model.vars.standalone_storage_power_in.sum(ModelDimension.StandaloneStorages)


def standalone_storage_profit_terms(
    model: EnergyMILPModel,
    params: EnergySystemParameters,
) -> linopy.LinearExpression:
    """Storage degradation cost as negative profit, reduced to (scenario,)."""
    timestep_hours = params.timestep / timedelta(hours=1)
    return -(
        (model.vars.standalone_storage_power_in + model.vars.standalone_storage_power_out)
        * timestep_hours
        * params.standalone_storages.degradation_cost
    ).sum([ModelDimension.Time, ModelDimension.StandaloneStorages])
