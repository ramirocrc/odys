"""Tests for the SolverConfig class."""

from odys.solvers.solver_config import SolverConfig


def test_default_solver_config() -> None:
    """Default SolverConfig matches expected defaults."""
    config = SolverConfig()
    assert config.time_limit is None
    assert config.mip_rel_gap is None
    assert config.presolve is True
    assert config.threads is None
    assert config.log_output is False


def test_to_solver_options_defaults() -> None:
    """Default config produces correct solver options dict."""
    options = SolverConfig().to_solver_options()
    assert options == {"presolve": "on", "output_flag": False}


def test_to_solver_options_all_set() -> None:
    """Fully configured SolverConfig produces complete solver options dict."""
    config = SolverConfig(
        time_limit=120.0,
        mip_rel_gap=0.05,
        presolve=False,
        threads=8,
        log_output=True,
    )
    options = config.to_solver_options()
    assert options == {
        "time_limit": 120.0,
        "mip_rel_gap": 0.05,
        "presolve": "off",
        "threads": 8,
        "output_flag": True,
    }
