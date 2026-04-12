"""Tests for per-solver option translators."""

from dataclasses import dataclass
from typing import Any

import pytest

from odys.domain.exceptions import OdysValidationError
from odys.solvers.config_translators import translate_solver_config
from odys.solvers.solver_config import SolverConfig, SolverName

COMMON_OPTS = SolverConfig(
    solver_name=SolverName.HIGHS,
    time_limit=120.0,
    mip_rel_gap=0.05,
    presolve=False,
    threads=8,
    log_output=True,
)

GLPK_OPTS = SolverConfig(
    solver_name=SolverName.GLPK,
    time_limit=120.0,
    mip_rel_gap=0.05,
    presolve=False,
    threads=None,
    log_output=False,
)


@dataclass
class SolverTestCase:
    solver_name: SolverName
    expected_output: dict[str, Any]
    config: SolverConfig | None = None


SOLVER_CASES = [
    SolverTestCase(
        solver_name=SolverName.HIGHS,
        expected_output={
            "time_limit": COMMON_OPTS.time_limit,
            "mip_rel_gap": COMMON_OPTS.mip_rel_gap,
            "presolve": "off",
            "threads": COMMON_OPTS.threads,
            "output_flag": COMMON_OPTS.log_output,
        },
    ),
    SolverTestCase(
        solver_name=SolverName.GUROBI,
        expected_output={
            "TimeLimit": COMMON_OPTS.time_limit,
            "MIPGap": COMMON_OPTS.mip_rel_gap,
            "Presolve": 0,
            "Threads": COMMON_OPTS.threads,
            "OutputFlag": 1,
        },
    ),
    SolverTestCase(
        solver_name=SolverName.CPLEX,
        expected_output={
            "timelimit": COMMON_OPTS.time_limit,
            "mip.tolerances.mipgap": COMMON_OPTS.mip_rel_gap,
            "preprocessing.presolve": 0,
            "threads": COMMON_OPTS.threads,
            "output.clonelog": 1,
        },
    ),
    SolverTestCase(
        solver_name=SolverName.SCIP,
        expected_output={
            "limits/time": COMMON_OPTS.time_limit,
            "limits/gap": COMMON_OPTS.mip_rel_gap,
            "presolving/maxrounds": 0,
            "parallel/maxnthreads": COMMON_OPTS.threads,
            "display/verblevel": 4,
        },
    ),
    SolverTestCase(
        solver_name=SolverName.GLPK,
        expected_output={
            "tmlim": GLPK_OPTS.time_limit,
            "mipgap": GLPK_OPTS.mip_rel_gap,
            "presolve": GLPK_OPTS.presolve,
        },
        config=GLPK_OPTS,
    ),
]


@pytest.mark.parametrize("case", SOLVER_CASES)
def test_solver_all_options(case: SolverTestCase) -> None:
    config = case.config or COMMON_OPTS.model_copy(update={"solver_name": case.solver_name})
    result = translate_solver_config(config)
    assert result == case.expected_output


def test_glpk_rejects_threads() -> None:
    """GLPK does not support threads option."""
    config = SolverConfig(solver_name=SolverName.GLPK, threads=4)
    with pytest.raises(OdysValidationError, match="does not support 'threads'"):
        translate_solver_config(config)


def test_glpk_rejects_log_output() -> None:
    """GLPK does not support log_output option."""
    config = SolverConfig(solver_name=SolverName.GLPK, log_output=True)
    with pytest.raises(OdysValidationError, match="does not support 'log_output'"):
        translate_solver_config(config)
