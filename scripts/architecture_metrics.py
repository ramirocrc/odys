#!/usr/bin/env python3
"""Structural architecture metrics and layer-rule checks for src/odys.

Reports LOC, import fan-in/fan-out, layer coupling, instability, and SCCs.
With ``--check``, exits non-zero on forbidden dependency edges.

Stdlib only. Run:
  uv run python scripts/architecture_metrics.py
  uv run python scripts/architecture_metrics.py --check
"""

from __future__ import annotations

import argparse
import ast
import sys
from collections import defaultdict
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src" / "odys"

_PKG_DEPTH = 2  # odys.<top> has two path segments before subpackages
_LEAF_TOPS = frozenset({"results", "solvers", "utils", "energy_system"})


def module_name(path: Path) -> str:
    """Return dotted module name for a path under src/."""
    rel = path.relative_to(SRC.parent)
    parts = list(rel.with_suffix("").parts)
    if parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


def layer(mod: str) -> str:
    """Map a module to its architecture layer label."""
    parts = mod.split(".")
    if len(parts) <= 1:
        return mod
    top = parts[1]
    child = parts[_PKG_DEPTH] if len(parts) > _PKG_DEPTH else None
    if top == "domain":
        return "odys.domain.entities" if child == "entities" else "odys.domain"
    if top == "optimization" and child is not None:
        return f"odys.optimization.{child}"
    if top in _LEAF_TOPS:
        return f"odys.{top}"
    return mod if mod == "odys" else ".".join(parts[:_PKG_DEPTH])


def discover_modules() -> dict[str, Path]:
    """Discover all Python modules under src/odys."""
    return {module_name(p): p for p in SRC.rglob("*.py")}


def resolve_import(mod: str, path: Path, module: str | None, level: int) -> str | None:
    """Resolve an absolute or relative import to a dotted module name."""
    if level == 0:
        return module
    base_parts = mod.split(".")
    pkg_parts = base_parts if path.name == "__init__.py" else base_parts[:-1]
    up = level - 1
    if up:
        pkg_parts = pkg_parts[:-up] if up <= len(pkg_parts) else []
    if module:
        return ".".join([*pkg_parts, *module.split(".")]) if pkg_parts else module
    return ".".join(pkg_parts) if pkg_parts else None


def longest_known(name: str, modules: dict[str, Path]) -> str | None:
    """Longest module prefix of ``name`` that exists in ``modules``."""
    candidate = name
    while candidate:
        if candidate in modules:
            return candidate
        if "." not in candidate:
            break
        candidate = candidate.rsplit(".", 1)[0]
    return None


def build_graph(modules: dict[str, Path]) -> dict[str, set[str]]:
    """Build directed import graph among odys modules."""
    edges: dict[str, set[str]] = defaultdict(set)
    for mod, path in modules.items():
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError as exc:
            print(f"warn: skip {path}: {exc}", file=sys.stderr)
            continue
        for node in ast.walk(tree):
            targets: list[str] = []
            if isinstance(node, ast.Import):
                targets.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                resolved = resolve_import(mod, path, node.module, node.level)
                if resolved:
                    targets.append(resolved)
            for target in targets:
                if not target.startswith("odys"):
                    continue
                dst = longest_known(target, modules)
                if dst and dst != mod:
                    edges[mod].add(dst)
    return edges


class _TarjanScc:
    """Tarjan strongly connected components over a directed graph."""

    def __init__(self, graph: dict[str, set[str]], nodes: set[str]) -> None:
        self._graph = graph
        self._nodes = nodes
        self._index = 0
        self._stack: list[str] = []
        self._on_stack: set[str] = set()
        self._indices: dict[str, int] = {}
        self._lowlink: dict[str, int] = {}
        self._result: list[list[str]] = []

    def run(self) -> list[list[str]]:
        for node in sorted(self._nodes):
            if node not in self._indices:
                self._visit(node)
        return self._result

    def _visit(self, v: str) -> None:
        self._indices[v] = self._index
        self._lowlink[v] = self._index
        self._index += 1
        self._stack.append(v)
        self._on_stack.add(v)
        self._relax_successors(v)
        if self._lowlink[v] == self._indices[v]:
            self._pop_component(v)

    def _relax_successors(self, v: str) -> None:
        for w in self._graph.get(v, ()):
            if w not in self._nodes:
                continue
            if w not in self._indices:
                self._visit(w)
                self._lowlink[v] = min(self._lowlink[v], self._lowlink[w])
            elif w in self._on_stack:
                self._lowlink[v] = min(self._lowlink[v], self._indices[w])

    def _pop_component(self, root: str) -> None:
        comp: list[str] = []
        while True:
            w = self._stack.pop()
            self._on_stack.remove(w)
            comp.append(w)
            if w == root:
                break
        self._result.append(comp)


def strongly_connected_components(graph: dict[str, set[str]], nodes: set[str]) -> list[list[str]]:
    """Tarjan SCC; multi-node components are import cycles."""
    return _TarjanScc(graph, nodes).run()


def loc_by_file(modules: dict[str, Path]) -> list[tuple[int, str]]:
    """Return (line_count, module) pairs sorted by size descending."""
    rows: list[tuple[int, str]] = []
    for mod, path in modules.items():
        lines = path.read_text(encoding="utf-8").count("\n") + 1
        rows.append((lines, mod))
    return sorted(rows, key=lambda r: (-r[0], r[1]))


def _module_matches(mod: str, prefixes: Iterable[str]) -> bool:
    return any(mod == p or mod.startswith(f"{p}.") for p in prefixes)


def find_layer_violations(graph: dict[str, set[str]]) -> list[str]:
    """Return human-readable forbidden dependency edges."""
    violations: list[str] = []
    domain_forbidden = (
        "odys.optimization",
        "odys.results",
        "odys.solvers",
        "odys.energy_system",
    )
    results_forbidden = ("odys.optimization",)
    constraints_forbidden = ("odys.results",)

    for src, dsts in sorted(graph.items()):
        for dst in sorted(dsts):
            if _module_matches(src, ("odys.domain",)) and _module_matches(dst, domain_forbidden):
                violations.append(f"domain must not import outer layers: {src} -> {dst}")
            if _module_matches(src, ("odys.results",)) and _module_matches(dst, results_forbidden):
                violations.append(f"results must not import optimization: {src} -> {dst}")
            if _module_matches(src, ("odys.optimization.constraints",)) and _module_matches(
                dst,
                constraints_forbidden,
            ):
                violations.append(f"constraints must not import results: {src} -> {dst}")
    return violations


def _print_top_loc(modules: dict[str, Path]) -> None:
    print("=== LOC (top 25) ===")
    for n, mod in loc_by_file(modules)[:25]:
        print(f"{n:5d}  {mod}")


def _print_fan_metrics(modules: dict[str, Path], graph: dict[str, set[str]]) -> None:
    reverse: dict[str, set[str]] = defaultdict(set)
    for src, dsts in graph.items():
        for dst in dsts:
            reverse[dst].add(src)

    print("\n=== FAN-IN (imported by; top 25) ===")
    fan_in = {m: len(reverse.get(m, ())) for m in modules}
    for mod, n in sorted(fan_in.items(), key=lambda x: (-x[1], x[0]))[:25]:
        if n:
            print(f"{n:3d}  {mod}")

    print("\n=== FAN-OUT (imports; top 25) ===")
    fan_out = {m: len(graph.get(m, ())) for m in modules}
    for mod, n in sorted(fan_out.items(), key=lambda x: (-x[1], x[0]))[:25]:
        if n:
            print(f"{n:3d}  {mod}")


def _print_layer_matrix(graph: dict[str, set[str]]) -> dict[tuple[str, str], int]:
    layer_edges: dict[tuple[str, str], int] = defaultdict(int)
    for src, dsts in graph.items():
        for dst in dsts:
            sl, dl = layer(src), layer(dst)
            if sl != dl:
                layer_edges[(sl, dl)] += 1

    print("\n=== CROSS-LAYER EDGES ===")
    for (src, dst), n in sorted(layer_edges.items(), key=lambda x: (-x[1], x[0])):
        print(f"{n:3d}  {src}  ->  {dst}")

    print("\n=== LAYER INSTABILITY  I = Ce/(Ca+Ce) ===")
    layer_in: dict[str, int] = defaultdict(int)
    layer_out: dict[str, int] = defaultdict(int)
    for (src, dst), n in layer_edges.items():
        layer_out[src] += n
        layer_in[dst] += n
    for name in sorted(set(layer_in) | set(layer_out)):
        ca, ce = layer_in[name], layer_out[name]
        instability = ce / (ca + ce) if (ca + ce) else 0.0
        print(f"{name:40s}  Ca={ca:3d}  Ce={ce:3d}  I={instability:.2f}")
    return layer_edges


def report_metrics(modules: dict[str, Path], graph: dict[str, set[str]]) -> None:
    """Print the full metrics report to stdout."""
    _print_top_loc(modules)
    _print_fan_metrics(modules, graph)
    _print_layer_matrix(graph)

    print("\n=== STRONGLY CONNECTED COMPONENTS (size > 1) ===")
    sccs = [c for c in strongly_connected_components(graph, set(modules)) if len(c) > 1]
    if not sccs:
        print("(none)")
    else:
        for comp in sorted(sccs, key=len, reverse=True):
            print(f"  cycle[{len(comp)}]: {', '.join(sorted(comp))}")

    print("\n=== LAYER RULE VIOLATIONS ===")
    violations = find_layer_violations(graph)
    if not violations:
        print("(none)")
    else:
        for msg in violations:
            print(f"  {msg}")

    total_edges = sum(len(v) for v in graph.values())
    print(f"\nmodules={len(modules)}  internal_edges={total_edges}  multi_node_sccs={len(sccs)}")
    print(f"layer_violations={len(violations)}")


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit non-zero if forbidden layer edges exist (quiet on success).",
    )
    args = parser.parse_args(argv)

    modules = discover_modules()
    graph = build_graph(modules)
    violations = find_layer_violations(graph)

    if args.check:
        if violations:
            print("Architecture layer check failed:", file=sys.stderr)
            for msg in violations:
                print(f"  {msg}", file=sys.stderr)
            return 1
        print("Architecture layer check passed.")
        return 0

    report_metrics(modules, graph)
    return 1 if violations else 0


if __name__ == "__main__":
    raise SystemExit(main())
