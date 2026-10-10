"""Model formulations, one per objective term type."""

from odys.optimization.objective_terms.base import ObjectiveTermFormulation
from odys.optimization.objective_terms.cvar import CVaRTermFormulation
from odys.optimization.objective_terms.profit import ProfitTermFormulation

OBJECTIVE_TERM_FORMULATIONS: tuple[type[ObjectiveTermFormulation], ...] = (
    ProfitTermFormulation,
    CVaRTermFormulation,
)
"""Every objective term type's formulation, in build order."""
