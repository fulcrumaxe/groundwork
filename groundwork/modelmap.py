"""Mental-model mapping drills (type 82, F-78, bloom: analyse).

Draw the data flow from memory: the front names the concept and shows
its code but lists no neighbours. The learner replies with the ordered
data-flow edges, one per line (`caller -> concept -> callee` style).
Grading is a graph diff: normalized submitted edges as a set against
the reference edge set from the repo graph; exact set match passes,
partial credit per correct edge, feedback naming missing and extra
edges.

The reference chain mirrors ``exercises._call_chain`` (first caller,
concept, first callee, display names, deduped; ``[concept]`` when
isolated). Edges are the adjacent pairs, capped at 2 edges.

``generate`` never returns None and never raises: an isolated concept
(no caller and no callee) yields an ungrounded card the pipeline skips.

Plugin API: ``generate(ex_id, concept, snippet, ctx)``,
``gen_model_map`` (alias), ``render(exercise) -> html``,
``grade(exercise, submission, runner)``.
Import-safe standalone: stdlib only, no groundwork imports.
Registration lives in ``groundwork/exercises.py``
(TYPES, GENERATORS, BLOOM_TYPES, grade/render branches),
``groundwork/grading.py`` (disclosure 82),
``groundwork/pipeline.py`` (BLOOM_DEFAULT_TYPES) and
``groundwork/__main__.py`` (cmd_e2e fixture); status section and
tour entry live below.
"""
from __future__ import annotations

import html
import re

TYPE_NUM = 82
TYPE_NAME = "model-map"
BLOOM = "analyse"
STATUS_ANCHOR = "status-b19-modelmap"

_EDGE_SEP = re.compile(r"\s*(?:->|>|=>|:)\s*")


def _concept_field(concept, name: str, default: str = "") -> str:
    return str(getattr(concept, name, default) or default)


def _disp(graph, node_id: str) -> str:
    try:
        node = (graph.nodes or {}).get(node_id) if graph is not None else None
        if node is not None and getattr(node, "name", ""):
            return str(node.name)
        return str(node_id)
    except Exception:  # noqa: BLE001 -- display never raises
        return str(node_id)


def _chain(graph, node_id: str, name: str) -> list[str]:
    """[caller, name, callee] display names; [name] when isolated."""
    try:
        if graph is None:
            return [name]
        edges = list(getattr(graph, "edges", []) or [])
        callers = sorted({s for s, d, k in edges
                          if d in (node_id, name) and k == "calls"
                          and s != node_id})
        callees = sorted({d for s, d, k in edges
                          if s == node_id and k == "calls"
                          and d != node_id})
        if not callees:
            try:
                node = (graph.nodes or {}).get(node_id)
                callees = [c for c in (getattr(node, "calls", []) or [])
                           if c != node_id and c != name]
            except Exception:  # noqa: BLE001 -- fallback never raises
                callees = []
        callers = [_disp(graph, n) for n in callers]
        callees = [_disp(graph, n) for n in callees]
        callers = [c for c in dict.fromkeys(callers) if c != name]
        callees = [c for c in dict.fromkeys(callees) if c != name]
        if callers and callees:
            chain = [callers[0], name, callees[0]]
        elif callers:
            chain = [callers[0], name]
        elif callees:
            chain = [name, callees[0]]
        else:
            chain = [name]
        if len(chain) < 2 or len(set(chain)) != len(chain):
            return [name]
        return chain[:3]
    except Exception:  # noqa: BLE001 -- chaining never raises
        return [name]


def _edges_of(chain: list[str]) -> list[list[str]]:
    try:
        return [[chain[i], chain[i + 1]] for i in range(len(chain) - 1)][:2]
    except Exception:  # noqa: BLE001
        return []


def _norm_edge(text: str):
    try:
        parts = [p.strip().lower() for p in _EDGE_SEP.split(str(text or ""))]
        parts = [p for p in parts if p]
        if len(parts) != 2:
            # Bare "A B" pair.
            words = str(text or "").split()
            if len(words) != 2:
                return None
            parts = [words[0].strip().lower(), words[1].strip().lower()]
        if not all(parts):
            return None
        return (parts[0], parts[1])
    except Exception:  # noqa: BLE001
        return None


def _hints() -> list[str]:
    return [
        "Who calls it? That is your first edge source.",
        "What does it feed? That is your last edge target.",
        "One edge per line: caller -> concept.",
    ]


def generate(ex_id, concept, snippet, ctx):
    """Build a model-map card; never None, never raises."""
    try:
        ctx = ctx if isinstance(ctx, dict) else {}
        snippet = list(snippet or [])
        name = _concept_field(concept, "name", "")
        node_id = _concept_field(concept, "node_id", name)
        file = _concept_field(concept, "file", "") or "app.py"
        try:
            line = int(getattr(concept, "line", 0) or 0)
        except (TypeError, ValueError):
            line = 0
        commit = str(ctx.get("commit", "") or "")
        chain = _chain(ctx.get("graph"), node_id, name or "modelmap")
        edges = _edges_of(chain)
        if not edges:
            return _ungrounded(ex_id, name, file, line, commit)
        code = "\n".join(str(l) for l in snippet)[:600]
        return {
            "id": ex_id, "type": TYPE_NUM, "type_name": TYPE_NAME,
            "bloom": BLOOM,
            "concept_id": node_id or "modelmap",
            "concept": name or chain[0], "file": file, "line": line,
            "commit": commit,
            "hints": _hints(),
            "front": (f"Draw the data flow through `{name}` from memory — "
                      "one edge per line, like \"caller -> concept\".\n"
                      f"```python\n{code}\n```"),
            "back": " -> ".join(chain),
            "payload": {"nodes": chain, "edges": edges,
                        "key": " -> ".join(chain), "grounded": True},
        }
    except Exception:
        return _ungrounded(ex_id, "", "app.py", 0, "")


def gen_model_map(ex_id, concept, snippet, ctx):
    """Alias under the card-type name; never None, never raises."""
    return generate(ex_id, concept, snippet, ctx)


def _ungrounded(ex_id, name, file, line, commit) -> dict:
    return {
        "id": ex_id, "type": TYPE_NUM, "type_name": TYPE_NAME,
        "bloom": BLOOM, "concept_id": "modelmap",
        "concept": name or "modelmap", "file": file, "line": line,
        "commit": commit, "hints": _hints(),
        "front": "Draw the data flow from memory. (No neighbours found.)",
        "back": "Isolated concept — skipped by the pipeline.",
        "payload": {"nodes": [], "edges": [], "key": "",
                    "grounded": False},
    }


def _fail(msg: str) -> dict:
    return {"pass": False, "score": 0.0, "feedback": msg}


def grade(exercise: dict, submission: str, runner=None) -> dict:
    """Graph diff: set match passes, partial credit per correct edge."""
    _ = runner
    try:
        return _grade(exercise, submission)
    except Exception as exc:  # noqa: BLE001 -- grading never raises
        return _fail(f"Grader hiccup ({exc}) — resubmit.")


def _grade(exercise: dict, submission: str) -> dict:
    p = (exercise or {}).get("payload", {}) or {}
    ref = {(str(a).lower(), str(b).lower())
           for a, b in (p.get("edges", []) or []) if a and b}
    if not ref:
        return _fail("No data-flow recorded on this card.")
    text = str(submission if submission is not None else "")
    if not text.strip():
        return _fail("Sketch the edges first — one per line, then submit.")
    got = set()
    for line in text.strip().splitlines():
        e = _norm_edge(line)
        if e is not None:
            got.add(e)
    if not got:
        return _fail("No edges parsed — write one per line: caller -> concept.")
    correct = got & ref
    score = len(correct) / len(ref)
    if got == ref:
        return {"pass": True, "score": 1.0,
                "feedback": "Flow matches — model verified."}
    missing = [f"{a} -> {b}" for a, b in sorted(ref - got)]
    extra = [f"{a} -> {b}" for a, b in sorted(got - ref)]
    bits = []
    if missing:
        bits.append("missing: " + ", ".join(missing[:4]))
    if extra:
        bits.append("extra: " + ", ".join(extra[:4]))
    return {"pass": False, "score": round(score, 2),
            "feedback": "Partial flow — " + "; ".join(bits) if bits else "No overlap."}


def render(exercise: dict) -> str:
    """Exercise widget: concept, code context, edge textarea."""
    p = (exercise or {}).get("payload", {}) or {}
    front = html.escape(str(exercise.get("front", "")))
    type_name = html.escape(str(exercise.get("type_name", TYPE_NAME)))
    file_line = f"{exercise.get('file', '')}:{exercise.get('line', 0)}"
    hints = "".join(
        f"<details><summary>Hint {i + 1}</summary>{html.escape(h)}</details>"
        for i, h in enumerate(exercise.get("hints", [])))
    return (
        f"<article><h3>{type_name}</h3>"
        f"<p>{front}</p>"
        f"<details><summary>How grading works</summary>"
        f"<p><small>Draw the edges from memory — exact set match passes, "
        f"partial credit per correct edge.</small></p>"
        f"</details>"
        f"<form method='post'><textarea name='answer' rows='3' cols='40' "
        f"placeholder='caller -> concept'></textarea><br>"
        f"<button>Check my flow</button></form>"
        f"{hints}<p><small>{html.escape(file_line)}</small></p></article>")


def section_html() -> str:
    """Anchored status subsection; wired into the status page by the parent."""
    return (
        f"<h3 id='{STATUS_ANCHOR}'>Mental-model mapping <small>(feature)</small></h3>"
        "<p>Draw the data flow through a concept from memory — graph-diff "
        "graded with partial credit per edge. "
        "<code>groundwork/modelmap.py</code>.</p>"
    )


def tour_entry() -> dict:
    """Feature-tour registry entry (appended to tour.ENTRIES by parent)."""
    return {"id": "model-map", "kind": "feature",
            "title": "Mental-model mapping",
            "blurb": "Draw the data flow from memory — graph-diff graded, partial credit per edge.",
            "path": "/due", "anchor": "up-next"}
