"""Electric vehicle contributions to power balance and per-scenario profit."""

from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING

from odys.optimization.model.sets import ModelDimension

if TYPE_CHECKING:
    import linopy

    from odys.optimization.model.milp_model import EnergyMILPModel
    from odys.optimization.parameters.parameters import EnergySystemParameters


def electric_vehicle_power_balance_terms(
    model: EnergyMILPModel,
    params: EnergySystemParameters,
) -> linopy.LinearExpression:
    """Net power injection from EVs, reduced to (scenario, time)."""
    del params
    return model.vars.ev_power_out.sum(ModelDimension.EVs) - model.vars.ev_power_in.sum(ModelDimension.EVs)


def electric_vehicle_profit_terms(
    model: EnergyMILPModel,
    params: EnergySystemParameters,
) -> linopy.LinearExpression:
    """EV degradation cost as negative profit, reduced to (scenario,)."""
    timestep_hours = params.timestep / timedelta(hours=1)
    return -(
        (model.vars.ev_power_in + model.vars.ev_power_out) * timestep_hours * params.electric_vehicles.degradation_cost
    ).sum([ModelDimension.Time, ModelDimension.EVs])
