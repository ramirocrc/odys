"""Odys domain layer.

Entities, scenarios, objectives, validation, and exceptions.

Dependency rule (enforced by ``scripts/architecture_metrics.py --check``):
this package must not import ``odys.optimization``, ``odys.results``,
``odys.solvers``, or ``odys.energy_system``.
"""
