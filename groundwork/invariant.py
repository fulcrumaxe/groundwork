"""Invariant stating (type 89, F-85, bloom: analyse).

The card shows a loop and asks for its invariant — the bound the
loop maintains. Two shapes, both statically derivable, no sandbox,
deterministic:

1. for-range loops — ``for i in range(a, b)`` (``range(n)`` counts
   as ``range(0, n)``). Answer: ``a<=i<=b`` (variable and bound
   sources as written).
2. while loops — the guard condition as written (``while i < n``
   answers ``i<n``). The first loop in source order wins.

``generate`` never returns None and never raises: no qualifying loop
yields an ungrounded card the pipeline skips. Grading is exact-match
over normalized text (lowercase, whitespace-free): the reference
passes 1.0, anything else fails 0.0 with the shape as hint.

Plugin API: ``generate(ex_id, concept, snippet, ctx)``,
``grade(exercise, submission, runner)`` (runner accepted, ignored),
``render(exercise) -> html``.
Import-safe standalone: stdlib only, no groundwork imports.
Registration lives in ``groundwork/exercises.py``
(TYPES, GENERATORS, BLOOM_TYPES, grade/render branches),
``groundwork/grading.py`` (disclosure 89),
``groundwork/pipeline.py`` (BLOOM_DEFAULT_TYPES) and
``groundwork/__main__.py`` (cmd_e2e fixture); status section and
tour entry live below.
"""
from __future__ import annotations

import ast
import html

TYPE_NUM = 89
TYPE_NAME = "invariant-state"
BLOOM = "analyse"
STATUS_ANCHOR = "status-b20-invariant"


def _concept_field(concept, name: str, default: str = "") -> str:
    return str(getattr(concept, name, default) or default)


def _sites(code: str) -> list:
    """(kind, quoted, reference) loop sites in source order."""
    out = []
    try:
        tree = ast.parse(code)
    except (SyntaxError, ValueError):
        return out
    try:
        for node in ast.walk(tree):
            if isinstance(node, ast.For):
                target = (node.target.id if isinstance(node.target, ast.Name)
                          else None)
                call = node.iter
                if target is None or not (
                        isinstance(call, ast.Call)
                        and isinstance(call.func, ast.Name)
                        and call.func.id == "range"
                        and not call.keywords
                        and 1 <= len(call.args) <= 3):
                    continue
                args = [ast.get_source_segment(code, a) or "?"
                        for a in call.args]
                start = args[0] if len(args) > 1 else "0"
                stop = args[1] if len(args) > 1 else args[0]
                try:
                    quoted = ast.get_source_segment(code, node) or "<loop>"
                except Exception:  # noqa: BLE001
                    quoted = "<loop>"
                out.append(("for-range", quoted, f"{start}<={target}<={stop}"))
            elif isinstance(node, ast.While):
                try:
                    cond = ast.get_source_segment(code, node.test) or "<cond>"
                except Exception:  # noqa: BLE001
                    cond = "<cond>"
                try:
                    quoted = ast.get_source_segment(code, node) or "<loop>"
                except Exception:  # noqa: BLE001
                    quoted = "<loop>"
                out.append(("while", quoted, "".join(cond.split())))
        return out
    except Exception:  # noqa: BLE001 -- scanning never raises
        return out


def _hints(reference: str) -> list:
    return [
        f"State the bound the loop maintains, like {reference}.",
        "Name the variable and both edges — no extra words needed.",
        "for-range keeps start<=var<=stop; while keeps its guard.",
    ]


def generate(ex_id, concept, snippet, ctx):
    """Build an invariant-state card; never None, never raises."""
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
        code = "\n".join(str(l) for l in snippet)
        found = _sites(code)
        if not found:
            return _ungrounded(ex_id, name, file, line, commit)
        kind, quoted, reference = found[0]
        if kind == "for-range":
            question = "State the loop invariant — the bound it maintains."
        else:
            question = "State the guard the while loop maintains."
        return {
            "id": ex_id, "type": TYPE_NUM, "type_name": TYPE_NAME,
            "bloom": BLOOM,
            "concept_id": node_id or "invariant",
            "concept": name or "invariant", "file": file, "line": line,
            "commit": commit,
            "hints": _hints(reference),
            "front": (f"{question} Reply with the bound, e.g. `{reference}`.\n"
                      f"```python\n{code[:600]}\n```"),
            "back": (f"{reference}: the loop maintains this bound on every "
                     "pass — check it before and after the body."),
            "payload": {"answer": reference, "site": quoted, "kind": kind,
                        "reference": reference, "grounded": True},
        }
    except Exception:
        return _ungrounded(ex_id, "", "app.py", 0, "")


def _ungrounded(ex_id, name, file, line, commit) -> dict:
    return {
        "id": ex_id, "type": TYPE_NUM, "type_name": TYPE_NAME,
        "bloom": BLOOM, "concept_id": "invariant",
        "concept": name or "invariant", "file": file, "line": line,
        "commit": commit, "hints": _hints("a<=i<=b"),
        "front": "No loop with a statable invariant found here.",
        "back": "Skipped by the pipeline.",
        "payload": {"answer": "", "site": "", "kind": "",
                    "reference": "", "grounded": False},
    }


def _fail(msg: str) -> dict:
    return {"pass": False, "score": 0.0, "feedback": msg}


def normalize(text) -> str:
    """Lowercase, whitespace-free comparison form; never raises."""
    try:
        return "".join(str(text or "").lower().split())
    except Exception:  # noqa: BLE001
        return ""


def grade(exercise: dict, submission: str, runner=None) -> dict:
    """Exact normalized-text match; no partial credit."""
    _ = runner
    try:
        return _grade(exercise, submission)
    except Exception as exc:  # noqa: BLE001 -- grading never raises
        return _fail(f"Grader hiccup ({exc}) — resubmit.")


def _grade(exercise: dict, submission: str) -> dict:
    p = (exercise or {}).get("payload", {}) or {}
    want = normalize(p.get("reference", ""))
    if not want:
        return _fail("No invariant recorded on this card.")
    text = str(submission if submission is not None else "")
    if not text.strip():
        return _fail("State the bound first — then check it.")
    if normalize(text) == want:
        return {"pass": True, "score": 1.0,
                "feedback": "Bound holds — the invariant is yours."}
    return {"pass": False, "score": 0.0,
            "feedback": f"Not the maintained bound — restate it like {want}."}


def disclosure() -> str:
    """One-line grading contract (also copied into the grading table)."""
    return ("State the loop invariant — the exact bound wins; "
            "anything else fails.")


def render(exercise: dict) -> str:
    """Exercise widget: invariant question plus a bound input."""
    p = (exercise or {}).get("payload", {}) or {}
    front = html.escape(str(exercise.get("front", "")))
    type_name = html.escape(str(exercise.get("type_name", TYPE_NAME)))
    file_line = f"{exercise.get('file', '')}:{exercise.get('line', 0)}"
    hints = "".join(
        f"<details><summary>Hint {i + 1}</summary>{html.escape(h)}</details>"
        for i, h in enumerate(exercise.get("hints", [])))
    _ = p
    return (
        f"<article><h3>{type_name}</h3>"
        f"<p>{front}</p>"
        f"<details><summary>How grading works</summary>"
        f"<p><small>{html.escape(disclosure())}</small></p>"
        f"</details>"
        f"<form method='post'>"
        f"<label>Invariant: <input name='answer' size='30'></label> "
        f"<button>State it</button></form>"
        f"{hints}<p><small>{html.escape(file_line)}</small></p></article>")


def section_html() -> str:
    """Anchored status subsection; wired into the status page by the parent."""
    return (
        f"<h3 id='{STATUS_ANCHOR}'>Invariant stating <small>(feature)</small></h3>"
        "<p>Write the loop invariant; the verifier checks your claim. "
        "Type 89 drills for-range bounds and while guards on the Due "
        "queue — <code>groundwork/invariant.py</code> derives the "
        "reference statically, grades exact normalized text.</p>"
    )


def tour_entry() -> dict:
    """Feature-tour registry entry (appended to tour.ENTRIES by parent)."""
    return {"id": "invariant-state", "kind": "feature",
            "title": "Invariant stating",
            "blurb": "Write the loop invariant; the verifier checks your claim.",
            "path": "/due", "anchor": "up-next"}
