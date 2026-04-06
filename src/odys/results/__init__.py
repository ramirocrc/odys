"""Odys results layer.

Contains optimization results and data structures:
- OptimizationResults: Main results container
- Result containers: Generator, Storage, Market, CVaR results
- SolvedModelData: Frozen snapshot of solution
"""

from odys.results.optimization_results import OptimizationResults
from odys.results.result_containers import (
    CVaRResults,
    GeneratorResults,
    MarketResults,
    StorageResults,
)
from odys.results.solved_model_data import SolvedModelData

__all__ = [
    "CVaRResults",
    "GeneratorResults",
    "MarketResults",
    "OptimizationResults",
    "SolvedModelData",
    "StorageResults",
]
