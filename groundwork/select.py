"""Concept selection: score touched nodes by novelty, centrality, risk.

Keeps top 3-5, ordered prerequisites-first (PRD pipeline step 2-3).
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ScoredConcept:
    node_id: str
    name: str
    kind: str
    file: str
    line: int
    score: float
    novelty: float
    centrality: float
    risk: float


def _prereqs_first(order: list[ScoredConcept], edges) -> list[ScoredConcept]:
    """Topo-ish order: a concept's callees/imports come before it.

    Cycle-breaking is deterministic (I-132): depcycle names the
    lexicographically-greatest in-cycle edge and it is dropped before
    the depth-first emit, so the same graph orders the same way every
    run. Acyclic graphs emit exactly the legacy order.
    """
    from . import depcycle as depcyclemod
    by_id = {c.node_id: c for c in order}
    deps: dict[str, set[str]] = {c.node_id: set() for c in order}
    try:
        edge_iter = list(edges or [])
    except TypeError:
        edge_iter = []
    for edge in edge_iter:
        try:
            s, d, _ = edge
        except (TypeError, ValueError):
            continue
        if s in by_id and d in by_id and s != d:
            deps[s].add(d)
    try:
        plan = depcyclemod.break_cycles(
            {nid: sorted(ds) for nid, ds in deps.items()})
        for src, dst in plan.get("dropped", []):
            if src in deps:
                deps[src].discard(dst)
    except Exception:  # noqa: BLE001 -- fallback is the legacy emit
        pass
    ranked: list[ScoredConcept] = []
    temp: set[str] = set()
    perm: set[str] = set()

    def visit(nid: str) -> None:
        if nid in perm:
            return
        if nid in temp:  # residual cycle: emit as-is
            return
        temp.add(nid)
        for dep in sorted(deps[nid]):
            visit(dep)
        temp.discard(nid)
        perm.add(nid)
        ranked.append(by_id[nid])

    for c in order:
        visit(c.node_id)
    return ranked


def select_concepts(graph, touched: list[str], mastery: dict[str, float] | None = None,
                    churn: dict[str, int] | None = None,
                    keep: int = 5,
                    w_novelty: float = 0.4,
                    w_centrality: float = 0.35,
                    w_risk: float = 0.25) -> list[ScoredConcept]:
    mastery = mastery or {}
    churn = churn or {}
    if not touched:
        # Fall back to highest-degree nodes so a module is never empty.
        touched = sorted(graph.nodes, key=lambda n: graph.out_degree(n),
                         reverse=True)[:keep]
    max_deg = max((graph.out_degree(n) for n in touched), default=1) or 1
    max_cx = max((graph.nodes[n].complexity for n in touched
                  if n in graph.nodes), default=1) or 1
    scored: list[ScoredConcept] = []
    for nid in touched:
        node = graph.nodes.get(nid)
        if node is None:
            continue
        novelty = 1.0 - mastery.get(nid, mastery.get(node.name, 0.0))
        centrality = graph.out_degree(nid) / max_deg
        risk = 0.5 * (node.complexity / max_cx) + \
            0.5 * min(1.0, churn.get(nid, churn.get(node.file, 0)) / 10.0)
        score = w_novelty * novelty + w_centrality * centrality + w_risk * risk
        scored.append(ScoredConcept(nid, node.name, node.kind, node.file,
                                    node.line, score, novelty, centrality, risk))
    scored.sort(key=lambda c: c.score, reverse=True)
    top = scored[:max(1, min(keep, len(scored)))]
    return _prereqs_first(top, graph.edges)


def plan_module(concepts: list[ScoredConcept], learner_level: str) -> dict:
    """Pick Bloom targets + exercise types per concept by learner level."""
    level_map = {
        "beginner": ["recall", "explain", "apply", "understand"],
        "intermediate": ["recall", "apply", "analyse"],
        "advanced": ["apply", "analyse", "modify", "evaluate", "create"],
    }
    blooms = level_map.get(learner_level, level_map["intermediate"])
    plan = []
    for i, c in enumerate(concepts):
        plan.append({
            "concept": c.node_id,
            "bloom": blooms[min(i, len(blooms) - 1)],
        })
    return {"concepts": plan, "learner_level": learner_level}
