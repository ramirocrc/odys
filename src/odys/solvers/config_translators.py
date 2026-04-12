"""Per-solver option translation for linopy solver backends.

Translates common option names (time_limit, presolve, etc.) into
the format each solver expects.
"""

from typing import Any, Protocol

from odys.solvers.solver_config import SolverConfig, SolverName


class SolverOptionTranslator(Protocol):
    """Protocol for translating common options to solver-specific format."""

    def translate(self, config: SolverConfig) -> dict[str, Any]:
        """Translate common options to solver-specific format."""
        ...


class HiGHSOptionTranslator:
    """Option translator for HiGHS solver."""

    def translate(self, config: SolverConfig) -> dict[str, Any]:
        """Translate common options to HiGHS solver format."""
        result: dict[str, Any] = {}
        if config.time_limit is not None:
            result["time_limit"] = config.time_limit
        if config.mip_rel_gap is not None:
            result["mip_rel_gap"] = config.mip_rel_gap
        if config.threads is not None:
            result["threads"] = config.threads
        result["presolve"] = "on" if config.presolve else "off"
        result["output_flag"] = config.log_output
        return result


class GurobiOptionTranslator:
    """Option translator for Gurobi solver."""

    def translate(self, config: SolverConfig) -> dict[str, Any]:
        """Translate common options to Gurobi solver format."""
        result: dict[str, Any] = {}
        if config.time_limit is not None:
            result["TimeLimit"] = config.time_limit
        if config.mip_rel_gap is not None:
            result["MIPGap"] = config.mip_rel_gap
        if config.threads is not None:
            result["Threads"] = config.threads
        result["Presolve"] = 1 if config.presolve else 0
        result["OutputFlag"] = 1 if config.log_output else 0
        return result


class CPLEXOptionTranslator:
    """Option translator for CPLEX solver."""

    def translate(self, config: SolverConfig) -> dict[str, Any]:
        """Translate common options to CPLEX solver format."""
        result: dict[str, Any] = {}
        if config.time_limit is not None:
            result["timelimit"] = config.time_limit
        if config.mip_rel_gap is not None:
            result["mip.tolerances.mipgap"] = config.mip_rel_gap
        if config.threads is not None:
            result["threads"] = config.threads
        result["preprocessing.presolve"] = 1 if config.presolve else 0
        result["output.clonelog"] = 1 if config.log_output else 0
        return result


class SCIPOptionTranslator:
    """Option translator for SCIP solver."""

    def translate(self, config: SolverConfig) -> dict[str, Any]:
        """Translate common options to SCIP solver format."""
        result: dict[str, Any] = {}
        if config.time_limit is not None:
            result["limits/time"] = config.time_limit
        if config.mip_rel_gap is not None:
            result["limits/gap"] = config.mip_rel_gap
        if config.threads is not None:
            result["parallel/maxnthreads"] = config.threads
        result["presolving/maxrounds"] = -1 if config.presolve else 0
        result["display/verblevel"] = 4 if config.log_output else 0
        return result


class GLPKOptionTranslator:
    """Option translator for GLPK solver."""

    def translate(self, config: SolverConfig) -> dict[str, Any]:
        """Translate common options to GLPK solver format."""
        result: dict[str, Any] = {}
        if config.time_limit is not None:
            result["tmlim"] = config.time_limit
        if config.mip_rel_gap is not None:
            result["mipgap"] = config.mip_rel_gap
        result["presolve"] = config.presolve
        return result


def translate_solver_config(solver_config: SolverConfig) -> dict[str, Any]:
    """Translate common option names to solver-specific option names.

    For known solvers (HiGHS, Gurobi, CPLEX, SCIP, GLPK), applies the
    appropriate translation. For unknown solvers, passes common options
    through unchanged -- the user should use ``solver_options`` for full control.

    Args:
        solver_config: Solver config

    Returns:
        Solver-specific options dict ready for linopy's ``Model.solve(**kwargs)``.

    Raises:
        OdysValidationError: If solver_name is empty.
    """
    translator = {
        SolverName.HIGHS: HiGHSOptionTranslator(),
        SolverName.GUROBI: GurobiOptionTranslator(),
        SolverName.CPLEX: CPLEXOptionTranslator(),
        SolverName.SCIP: SCIPOptionTranslator(),
        SolverName.GLPK: GLPKOptionTranslator(),
    }[solver_config.solver_name]
    return translator.translate(solver_config)
