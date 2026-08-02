"""Kernel helpers that collect contribution terms from the asset registry."""

from __future__ import annotations

from typing import TYPE_CHECKING

from odys.optimization.model.registry import AssetRegistry

if TYPE_CHECKING:
    from collections.abc import Iterator

    import linopy

    from odys.optimization.model.milp_model import EnergyMILPModel


def iter_power_balance_contributions(model: EnergyMILPModel) -> Iterator[linopy.LinearExpression]:
    """Yield power-balance terms from registered asset contributors."""
    params = model.parameters
    for asset in AssetRegistry:
        spec = asset.spec
        if spec.power_balance_terms is None:
            continue
        if not spec.is_present(params):
            continue
        term = spec.power_balance_terms(model, params)
        if term is not None:
            yield term


def iter_profit_contributions(model: EnergyMILPModel) -> Iterator[linopy.LinearExpression]:
    """Yield per-scenario profit terms from registered asset contributors."""
    params = model.parameters
    for asset in AssetRegistry:
        spec = asset.spec
        if spec.profit_terms is None:
            continue
        if not spec.is_present(params):
            continue
        term = spec.profit_terms(model, params)
        if term is not None:
            yield term
