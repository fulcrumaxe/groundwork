"""Circular lesson dependencies: detect cycles, break ties deterministically (I-132).

Prerequisite edges map a node to its prerequisites (``{Y: [X]}`` means learn
X before Y, same convention as ``quests.quest_path``). ``find_cycles``
reports every elementary cycle in canonical sorted form; ``break_cycles``
orders the nodes prerequisites-first (Kahn) and, whenever a cycle blocks
progress, drops the lexicographically greatest edge of the blocking
cycle set — so the same input always yields the same order and the same
dropped edge, regardless of dict insertion order. ``order_nodes`` is the
legacy-safe entry point: no edges (or hostile input) returns the input
order unchanged. Pure functions, stdlib only, never raise.

Caller path (real learner/reader, never a Status demo):
``select._prereqs_first`` drops depcycle's deterministic ``dropped``
edges before its depth-first emit, so cyclic concept graphs order the
same way every run while acyclic graphs keep their exact legacy order.
That order feeds lesson generation (``select.select_concepts``) and
through it the prereq chain and unlock quests.
"""
from __future__ import annotations

STATUS_ANCHOR = "status-b21-depcycle"

DEPCYCLE_ID = "depcycle-tiebreak"


def _name(value) -> str:
    """Clean node name; "" when unusable. Never raises."""
    try:
        if isinstance(value, str) and value.strip():
            return value.strip()
    except Exception:  # noqa: BLE001 -- coercion must never raise
        pass
    return ""


def normalize(edges) -> dict:
    """Clean edge map to ``{node: sorted-unique-prereq-list}``; never raises."""
    try:
        if not isinstance(edges, dict):
            return {}
        out: dict = {}
        for key, reqs in edges.items():
            node = _name(key)
            if not node:
                continue
            if not isinstance(reqs, (list, tuple)):
                out.setdefault(node, [])
                continue
            seen = sorted({_name(r) for r in reqs} - {""})
            out[node] = seen
            for req in seen:
                out.setdefault(req, [])
        return out
    except Exception:  # noqa: BLE001 -- normalize must never raise
        return {}


def _canon(cycle: list) -> tuple:
    """Rotate a cycle so its smallest element comes first."""
    i = cycle.index(min(cycle))
    return tuple(cycle[i:] + cycle[:i])


def find_cycles(edges) -> list:
    """All elementary cycles, canonicalised and sorted; never raises.

    Each cycle is a node list with the smallest name first (no repeated
    closing node). Self-loops report as ``[X]``. Result order is sorted,
    so identical graphs give identical output whatever the input order.
    """
    try:
        adj = normalize(edges)
        found: set = set()
        WHITE, GREY, BLACK = 0, 1, 2
        color = {n: WHITE for n in adj}
        stack: list = []

        def visit(node: str) -> None:
            color[node] = GREY
            stack.append(node)
            for req in adj.get(node, []):
                if color.get(req, BLACK) == GREY:
                    found.add(_canon(stack[stack.index(req):]))
                elif color.get(req, BLACK) == WHITE:
                    visit(req)
            stack.pop()
            color[node] = BLACK

        for node in sorted(adj):
            if color[node] == WHITE:
                visit(node)
        return [list(c) for c in sorted(found)]
    except Exception:  # noqa: BLE001 -- detection must never raise
        return []


def _cycle_edges(adj: dict, remaining: set) -> set:
    """Edge tuples participating in any cycle within ``remaining``.

    Each tuple is (src, dst) with src listing dst as a prerequisite:
    the canon list runs visited-prereq-visited, so consecutive pairs
    plus the wraparound are the true edge direction.
    """
    edges: set = set()
    for cyc in find_cycles({n: [r for r in adj.get(n, []) if r in remaining]
                            for n in remaining}):
        if len(cyc) == 1:
            edges.add((cyc[0], cyc[0]))
        else:
            for i, node in enumerate(cyc):
                edges.add((node, cyc[(i + 1) % len(cyc)]))
    return edges


def break_cycles(edges) -> dict:
    """Prerequisites-first order with deterministic cycle breaking.

    Returns ``{"order": [...], "dropped": [(src, dst), ...]}`` where
    ``src`` lists ``dst`` as a prerequisite (edge src -> dst dropped).
    Ready nodes (no unmet prereqs) always pop in lexicographic order;
    when no node is ready, the lexicographically greatest in-cycle edge
    is dropped and recorded. Never raises.
    """
    try:
        adj = normalize(edges)
        prereqs = {n: set(r for r in reqs) for n, reqs in adj.items()}
        remaining = set(adj)
        order: list = []
        dropped: list = []
        while remaining:
            ready = sorted(n for n in remaining
                           if not (prereqs[n] & remaining))
            if ready:
                order.append(ready[0])
                remaining.discard(ready[0])
                continue
            cands = _cycle_edges(adj, remaining)
            if not cands:  # defensive: cannot happen, but stay total
                order.extend(sorted(remaining))
                break
            src, dst = max(cands)  # deterministic tie-break
            dropped.append((src, dst))
            prereqs[src].discard(dst)
        return {"order": order, "dropped": dropped}
    except Exception:  # noqa: BLE001 -- ordering must never raise
        return {"order": [], "dropped": []}


def order_nodes(nodes, edges) -> list:
    """Order ``nodes`` prerequisites-first; legacy fallback keeps input order.

    Nodes absent from ``edges`` keep their relative input order among
    themselves; hostile or empty input returns ``list(nodes)`` unchanged.
    Never raises.
    """
    try:
        names = [_name(n) for n in (nodes or [])]
        names = [n for n in names if n]
        if not names:
            return []
        if not isinstance(edges, dict) or not edges:
            return list(names)  # legacy no-data fallback
        plan = break_cycles(edges)
        rank = {n: i for i, n in enumerate(plan["order"])}
        return sorted(names,
                      key=lambda n: (rank.get(n, len(rank)), names.index(n)))
    except Exception:  # noqa: BLE001 -- entry point must never raise
        try:
            return list(nodes or [])
        except Exception:  # noqa: BLE001 -- fallback must never raise
            return []


def tour_entry() -> dict:
    """Tour catalog entry for this item; the parent appends it to ENTRIES."""
    return {"id": DEPCYCLE_ID, "kind": "improvement",
            "title": "Deterministic cycle-breaking",
            "blurb": ("Circular lesson prerequisites are detected and "
                      "broken the same way every run, so study order "
                      "never flips."),
            "path": "/status", "anchor": STATUS_ANCHOR}


def section_html() -> str:
    """Anchored status subsection with a live cycle demo; db-free."""
    try:
        plan = break_cycles({"Serve": ["Grade"], "Grade": ["Read"],
                             "Read": ["Serve"]})
        demo = f"order={plan['order']}, dropped={plan['dropped']}"
        return (
            f"<h3 id='{STATUS_ANCHOR}'>Deterministic cycle-breaking "
            "<small>(improvement)</small></h3>"
            "<p>Circular lesson prerequisites freeze prerequisite-first "
            "ordering. "
            f"{demo} — "
            "<code>groundwork/depcycle.py</code> provides "
            "<code>find_cycles()</code> (canonical sorted cycles) and "
            "<code>break_cycles()</code> (Kahn order, lexicographically "
            "greatest in-cycle edge dropped); both never raise.</p>"
        )
    except Exception:  # noqa: BLE001 -- status must always render
        return f"<h3 id='{STATUS_ANCHOR}'>Deterministic cycle-breaking</h3>"
