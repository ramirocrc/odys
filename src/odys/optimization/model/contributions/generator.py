"""Generator contributions to power balance and per-scenario profit."""

from __future__ import annotations

from typing import TYPE_CHECKING

from odys.optimization.model.sets import ModelDimension

if TYPE_CHECKING:
    import linopy

    from odys.optimization.model.milp_model import EnergyMILPModel
    from odys.optimization.parameters.parameters import EnergySystemParameters


def generator_power_balance_terms(
    model: EnergyMILPModel,
    params: EnergySystemParameters,
) -> linopy.LinearExpression:
    """Net power injection from generators, reduced to (scenario, time)."""
    del params  # asset emptiness is gated by the kernel
    return model.vars.generator_power.sum(ModelDimension.Generators)


def generator_profit_terms(
    model: EnergyMILPModel,
    params: EnergySystemParameters,
) -> linopy.LinearExpression:
    """Generator operating costs as negative profit, reduced to (scenario,)."""
    return -(
        model.vars.generator_power * params.generators.variable_cost
        + model.vars.generator_startup * params.generators.startup_cost
        + model.vars.generator_shutdown * params.generators.shutdown_cost
    ).sum([ModelDimension.Time, ModelDimension.Generators])
