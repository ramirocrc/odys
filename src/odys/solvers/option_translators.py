"""Per-solver option translation for linopy solver backends.

Translates common option names (time_limit, presolve, etc.) into
the format each solver expects.
"""

from collections.abc import Callable
from typing import Any


def _translate_highs(common: dict[str, Any]) -> dict[str, Any]:
    """Translate common options to HiGHS option names."""
    options: dict[str, Any] = {}
    if "time_limit" in common:
        options["time_limit"] = common["time_limit"]
    if "mip_rel_gap" in common:
        options["mip_rel_gap"] = common["mip_rel_gap"]
    if "threads" in common:
        options["threads"] = common["threads"]
    options["presolve"] = "on" if common.get("presolve", True) else "off"
    options["output_flag"] = common.get("log_output", False)
    return options


def _translate_gurobi(common: dict[str, Any]) -> dict[str, Any]:
    """Translate common options to Gurobi option names."""
    options: dict[str, Any] = {}
    if "time_limit" in common:
        options["TimeLimit"] = common["time_limit"]
    if "mip_rel_gap" in common:
        options["MIPGap"] = common["mip_rel_gap"]
    if "threads" in common:
        options["Threads"] = common["threads"]
    options["Presolve"] = 1 if common.get("presolve", True) else 0
    options["OutputFlag"] = 1 if common.get("log_output", False) else 0
    return options


def _translate_cplex(common: dict[str, Any]) -> dict[str, Any]:
    """Translate common options to CPLEX option names."""
    options: dict[str, Any] = {}
    if "time_limit" in common:
        options["timelimit"] = common["time_limit"]
    if "mip_rel_gap" in common:
        options["mip.tolerances.mipgap"] = common["mip_rel_gap"]
    if "threads" in common:
        options["threads"] = common["threads"]
    options["preprocessing.presolve"] = 1 if common.get("presolve", True) else 0
    options["output.clonelog"] = 1 if common.get("log_output", False) else 0
    return options


def _translate_scip(common: dict[str, Any]) -> dict[str, Any]:
    """Translate common options to SCIP option names."""
    options: dict[str, Any] = {}
    if "time_limit" in common:
        options["limits/time"] = common["time_limit"]
    if "mip_rel_gap" in common:
        options["limits/gap"] = common["mip_rel_gap"]
    if "threads" in common:
        options["parallel/maxnthreads"] = common["threads"]
    options["presolving/maxrounds"] = -1 if common.get("presolve", True) else 0
    options["display/verblevel"] = 4 if common.get("log_output", False) else 0
    return options


def _translate_glpk(common: dict[str, Any]) -> dict[str, Any]:
    """Translate common options to GLPK option names."""
    options: dict[str, Any] = {}
    if "time_limit" in common:
        options["tmlim"] = common["time_limit"]
    if "mip_rel_gap" in common:
        options["mipgap"] = common["mip_rel_gap"]
    options["presolve"] = common.get("presolve", True)
    return options


_TRANSLATORS: dict[str, Callable[[dict[str, Any]], dict[str, Any]]] = {
    "highs": _translate_highs,
    "gurobi": _translate_gurobi,
    "cplex": _translate_cplex,
    "scip": _translate_scip,
    "glpk": _translate_glpk,
}


def translate_options(solver_name: str, common: dict[str, Any]) -> dict[str, Any]:
    """Translate common option names to solver-specific option names.

    For known solvers (HiGHS, Gurobi, CPLEX, SCIP, GLPK), applies the
    appropriate translation. For unknown solvers, passes common options
    through unchanged -- the user should use ``solver_options`` for full control.

    Args:
        solver_name: The linopy solver name.
        common: Common option dict with keys like time_limit, presolve, etc.

    Returns:
        Solver-specific options dict ready for linopy's ``Model.solve(**kwargs)``.

    """
    translator = _TRANSLATORS.get(solver_name)
    if translator is not None:
        return translator(common)
    return common
