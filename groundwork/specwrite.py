"""Spec-writing exercise (type 41, F-18, bloom: create).

The learner writes acceptance criteria — a short checklist-style spec —
for the concept's function, anchored on its real definition (parameter
names, return behavior, error/branch edge cases) plus its callers from
the context graph. Grading is a deterministic keyword/phrase checklist:
every acceptance point must appear in the prose (case-insensitive
substring; some points accept any of several phrases). Partial credit
is recorded, no execution, no sandbox runner. Stdlib only
(``ast``/``html``/``re``), import-safe standalone: no groundwork imports.

Plugin API: ``generate(ex_id, concept, snippet, ctx)``,
``render(exercise) -> html``, ``grade(exercise, submission, runner)``.
Registration lives in ``groundwork/exercises.py``
(TYPES, GENERATORS, BLOOM_TYPES); see ===WIRES=== below.
"""
from __future__ import annotations

import ast
import html
import re

TYPE_NUM = 41
TYPE_NAME = "spec-writing"
BLOOM = "create"

_SKIP_PARAMS = ("self", "cls")
_MAX_PARAM_POINTS = 3


def _concept_field(concept, name: str, default: str = "") -> str:
    return str(getattr(concept, name, default) or default)


def _find_fn(code: str, name: str):
    """FunctionDef named `name`, else the first def; None if unparseable."""
    try:
        tree = ast.parse(code)
    except (SyntaxError, ValueError):
        return None
    fns = [n for n in ast.walk(tree)
           if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    if not fns:
        return None
    return next((f for f in fns if f.name == name), fns[0])


def _params_of(fn) -> list[str]:
    args = list(getattr(fn.args, "posonlyargs", [])) + list(fn.args.args)
    return [a.arg for a in args + list(fn.args.kwonlyargs)
            if a.arg not in _SKIP_PARAMS]


def _returns_value(fn) -> bool:
    return any(isinstance(n, ast.Return) and n.value is not None
               for n in ast.walk(fn))


def _has_raise(fn) -> bool:
    return any(isinstance(n, ast.Raise) for n in ast.walk(fn))


def _has_branch(fn) -> bool:
    return any(isinstance(n, (ast.If, ast.For, ast.AsyncFor, ast.While))
               for n in ast.walk(fn))


def _callers(ctx: dict, concept) -> list[str]:
    """Display names calling into this concept; [] on any odd input."""
    try:
        lesson = (ctx or {}).get("lesson") or {}
        if lesson.get("callers"):
            return [str(c) for c in lesson["callers"][:3]]
        graph = (ctx or {}).get("graph")
        if graph is None:
            return []
        node_id = _concept_field(concept, "node_id")
        name = _concept_field(concept, "name")
        out = sorted({s for s, d, k in graph.edges
                      if d in (node_id, name) and k == "calls"
                      and s != node_id})
        names = []
        for s in out[:3]:
            node = graph.nodes.get(s)
            names.append(getattr(node, "name", "") or s)
        return names
    except Exception:  # noqa: BLE001 — caller list is decorative
        return []


def _derive_points(func: str, fn) -> list[dict]:
    """Acceptance checklist: each point is {id, label, needles, any_of}."""
    points = [{"id": "names", "label": f"Names `{func}` as the subject",
               "needles": [func.lower()], "any_of": False}]
    if fn is not None:
        for p in _params_of(fn)[:_MAX_PARAM_POINTS]:
            points.append({"id": f"param-{p}",
                           "label": f"Documents parameter `{p}`",
                           "needles": [p.lower()], "any_of": False})
        if _returns_value(fn):
            points.append({"id": "returns",
                           "label": "States what is returned",
                           "needles": ["return"], "any_of": False})
        if _has_raise(fn):
            points.append({"id": "edge",
                           "label": "States the error/invalid-input behavior",
                           "needles": ["error", "raise", "exception", "invalid"],
                           "any_of": True})
        elif _has_branch(fn):
            points.append({"id": "edge",
                           "label": "States the conditional/edge-case behavior",
                           "needles": ["if", "when", "otherwise", "empty", "none"],
                           "any_of": True})
        else:
            points.append({"id": "edge", "label": "Gives a concrete example",
                           "needles": ["example", "e.g.", "for example", "given"],
                           "any_of": True})
    else:
        points.append({"id": "edge", "label": "Gives a concrete example",
                       "needles": ["example", "e.g.", "given", "when"],
                       "any_of": True})
    return points


def generate(ex_id, concept, snippet, ctx) -> dict:
    """Build a spec-writing card: acceptance criteria for the concept."""
    ctx = ctx or {}
    snippet = list(snippet or [])
    code = str(ctx.get("runnable") or "\n".join(snippet) or "").strip()
    name = _concept_field(concept, "name", "func") or "func"
    kind = _concept_field(concept, "kind", "function")
    file = _concept_field(concept, "file")
    try:
        line = int(getattr(concept, "line", 0) or 0)
    except (TypeError, ValueError):
        line = 0
    commit = str(ctx.get("commit", "") or "")
    fn = _find_fn(code, name) if code else None
    func = fn.name if fn is not None else re.sub(r"\W+", "_", name).strip("_") or "func"
    grounded = fn is not None
    callers = _callers(ctx, concept)
    points = _derive_points(func, fn)
    lines = [f"Write acceptance criteria for `{func}` ({kind}"
             f"{f' in {file}' if file else ''}): a short checklist a "
             f"reviewer could verify against an implementation."]
    if callers:
        lines.append("It is used by " + ", ".join(f"`{c}`" for c in callers)
                     + " — say what those callers may rely on.")
    lines.append("Cover every checkbox: " + "; ".join(p["label"] for p in points) + ".")
    front = "\n".join(lines)
    back = "; ".join(p["label"] for p in points) + "."
    hints = [
        f"Name `{func}` and each of its inputs — one criterion per input.",
        ("Say what it hands back (`return ...`) and what happens on "
         "bad input or edge cases — those are the criteria reviewers check first."),
        "Write one concrete example (`Given ...`) so the spec is testable.",
    ]
    return {
        "id": ex_id, "type": TYPE_NUM, "type_name": TYPE_NAME, "bloom": BLOOM,
        "concept_id": _concept_field(concept, "node_id", name),
        "concept": name, "file": file, "line": line, "commit": commit,
        "hints": hints,
        "front": front, "back": back,
        "payload": {"func": func, "points": points, "callers": callers,
                    "reference": back, "grounded": grounded},
    }


def _fail(msg: str) -> dict:
    return {"pass": False, "score": 0.0, "feedback": msg}


def _point_hit(text_l: str, point: dict) -> bool:
    try:
        needles = [str(n).lower() for n in point.get("needles", [])]
    except (AttributeError, TypeError):
        return False
    if not needles:
        return False
    if point.get("any_of"):
        return any(n and n in text_l for n in needles)
    return all(n and n in text_l for n in needles)


def grade(exercise: dict, submission: str, runner=None) -> dict:
    """Checklist grade: every acceptance point must appear in the prose.

    Pass needs every point; the score still records partial credit.
    ``runner`` is accepted for API symmetry and ignored. Never raises:
    malformed input yields a failing grade, not an error.
    """
    _ = runner
    try:
        payload = (exercise or {}).get("payload", {})
        points = list(payload.get("points", []) or [])
        if not points:
            return _fail("No acceptance checklist on this card.")
        text = str(submission or "").strip()
        if not text:
            return _fail("Submit acceptance criteria covering every checkbox.")
        text_l = text.lower()
        missing = [p.get("label", p.get("id", "?")) for p in points
                   if not _point_hit(text_l, p)]
        earned = len(points) - len(missing)
        score = earned / max(1, len(points))
        detail = f"{earned}/{len(points)} acceptance points."
        if not missing:
            return {"pass": True, "score": 1.0 if score == 1.0 else score,
                    "feedback": f"Spec accepted. {detail}"}
        return {"pass": False, "score": score,
                "feedback": f"Not yet. {detail} Missing: {'; '.join(missing)[:200]}."}
    except Exception:  # noqa: BLE001 — grading must never raise
        return _fail("Grader could not read the submission — submit prose criteria.")


def render(exercise: dict) -> str:
    """Exercise widget: requirement plus a textarea for the criteria."""
    payload = (exercise or {}).get("payload", {})
    front = html.escape(str(exercise.get("front", "")))
    concept = html.escape(str(exercise.get("concept", "")))
    type_name = html.escape(str(exercise.get("type_name", TYPE_NAME)))
    checks = "".join(
        f"<li>{html.escape(str(p.get('label', '')))}</li>"
        for p in payload.get("points", []))
    file_line = f"{exercise.get('file', '')}:{exercise.get('line', 0)}"
    hints = "".join(
        f"<details><summary>Hint {i + 1}</summary>{html.escape(h)}</details>"
        for i, h in enumerate(exercise.get("hints", [])))
    return (
        f"<article><h3>{concept} · {type_name}</h3>"
        f"<p>{front}</p>"
        f"<ul>{checks}</ul>"
        f"<details><summary>How grading works</summary>"
        f"<p><small>Checklist, not hidden tests: each acceptance point must "
        f"appear in your criteria as the named keyword or phrase. Every "
        f"point is required to pass; partial credit is recorded, no "
        f"sandbox.</small></p></details>"
        f"<form method='post'><textarea name='answer' rows='8' cols='70'></textarea>"
        f"<br><button>Check spec</button></form>{hints}"
        f"<p><small>{html.escape(file_line)}</small></p></article>")


def section_html() -> str:
    """Anchored status subsection; wired into the status page by the parent."""
    return (
        "<h3 id='status-b8-specwrite'>Spec writing <small>(feature)</small></h3>"
        "<p>Write acceptance criteria — a verifiable checklist — for a "
        "function and its callers. Graded by a deterministic keyword/phrase "
        "checklist with partial credit, no sandbox. "
        "<code>groundwork/specwrite.py</code>.</p>"
    )


def tour_entry() -> dict:
    """Feature-tour registry entry for the parent to append."""
    return {"id": "specwrite-type", "kind": "feature",
            "title": "Spec writing",
            "blurb": "Write acceptance criteria for a function: every "
                     "checkbox — inputs, returns, edge cases — must appear.",
            "path": "/status", "anchor": "status-b8-specwrite"}
