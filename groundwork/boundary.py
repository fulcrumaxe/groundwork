"""Boundary-value drills (type 88, F-84, bloom: analyse).

Off-by-one bootcamp. The card shows the concept's code with the
boundary site quoted and asks for the ONE edge integer to probe
first. Two site kinds, both statically derivable — no sandbox,
deterministic:

1. compare sites — integer comparison against a literal
   (`x < L`, `x <= L`, `x > L`, `x >= L`, `x == L`, `x != L`; either
   operand the literal; `len(xs)` counts as the non-literal side).
   Answer: the literal `L` itself.
2. range sites — `range(L)` / `range(a, L)` / `range(a, L, s)` with
   literal stop `L`. Answer: `L` (first value the loop never takes).

The first site in source order wins. Distractors are `L-1` and `L+1`
(seeded shuffle); the back teaches the triple habit. Grading follows
the type-13 shape: first integer token wins, no partial credit (an
off-by-one answer IS the bug being drilled).

``generate`` never returns None and never raises: no qualifying site
yields an ungrounded card the pipeline skips.

Plugin API: ``generate(ex_id, concept, snippet, ctx)``,
``grade(exercise, submission, runner)`` (runner accepted, ignored),
``render(exercise) -> html``.
Import-safe standalone: stdlib only, no groundwork imports.
Registration lives in ``groundwork/exercises.py``
(TYPES, GENERATORS, BLOOM_TYPES, grade/render branches),
``groundwork/grading.py`` (disclosure 88),
``groundwork/pipeline.py`` (BLOOM_DEFAULT_TYPES) and
``groundwork/__main__.py`` (cmd_e2e fixture); status section and
tour entry live below.
"""
from __future__ import annotations

import ast
import hashlib
import html
import random
import re

TYPE_NUM = 88
TYPE_NAME = "boundary-drill"
BLOOM = "analyse"
STATUS_ANCHOR = "status-b19-boundary"

_INT = re.compile(r"[+-]?\d+")


def _concept_field(concept, name: str, default: str = "") -> str:
    return str(getattr(concept, name, default) or default)


def _seed(ex_id) -> int:
    try:
        return int(hashlib.sha256(str(ex_id).encode()).hexdigest(), 16)
    except Exception:  # noqa: BLE001 -- seeding must never raise
        return 0


def _litnum(node) -> int | None:
    try:
        if isinstance(node, ast.Constant) and isinstance(node.value, int) \
                and not isinstance(node.value, bool):
            return node.value
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub) \
                and isinstance(node.operand, ast.Constant) \
                and isinstance(node.operand.value, int):
            return -node.operand.value
        return None
    except Exception:  # noqa: BLE001
        return None


def _is_lenish(node) -> bool:
    try:
        return (isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == "len")
    except Exception:  # noqa: BLE001
        return False


def _sites(code: str) -> list:
    """(kind, quoted, literal) boundary sites in source order."""
    out = []
    try:
        tree = ast.parse(code)
    except (SyntaxError, ValueError):
        return out
    try:
        for node in ast.walk(tree):
            if isinstance(node, ast.Compare) and len(node.ops) == 1 \
                    and len(node.comparators) == 1:
                op = node.ops[0]
                if not isinstance(op, (ast.Lt, ast.LtE, ast.Gt, ast.GtE,
                                       ast.Eq, ast.NotEq)):
                    continue
                left, right = node.left, node.comparators[0]
                lit = _litnum(left)
                other = right
                if lit is None:
                    lit = _litnum(right)
                    other = left
                if lit is None:
                    continue
                if not (_is_lenish(other) or isinstance(other, ast.Name)):
                    continue
                try:
                    quoted = ast.get_source_segment(code, node) or "<expr>"
                except Exception:  # noqa: BLE001
                    quoted = "<expr>"
                out.append(("compare", quoted, lit))
            elif isinstance(node, ast.Call) \
                    and isinstance(node.func, ast.Name) \
                    and node.func.id == "range" \
                    and not node.keywords \
                    and 1 <= len(node.args) <= 3 \
                    and all(isinstance(a, (ast.Constant, ast.UnaryOp, ast.Name))
                            for a in node.args):
                lit = _litnum(node.args[-1])
                if lit is None and len(node.args) > 1:
                    continue
                if lit is None:
                    continue
                try:
                    quoted = ast.get_source_segment(code, node) or "<expr>"
                except Exception:  # noqa: BLE001
                    quoted = "<expr>"
                out.append(("range", quoted, lit))
        return out
    except Exception:  # noqa: BLE001 -- scanning never raises
        return out


def _choices(edge: int, ex_id) -> list[str]:
    opts = [str(edge), str(edge - 1), str(edge + 1)]
    rng = random.Random(_seed(ex_id) & 0xFFFFFFFF)
    rng.shuffle(opts)
    return opts


def _hints(site: str) -> list[str]:
    return [
        f"Look at {site}: the literal is the edge.",
        "Probe the triple: L-1, L, L+1.",
        "Off-by-one bugs live exactly at the literal.",
    ]


def generate(ex_id, concept, snippet, ctx):
    """Build a boundary-drill card; never None, never raises."""
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
        kind, quoted, edge = found[0]
        choices = _choices(edge, ex_id)
        if kind == "compare":
            question = (f"Which value must you probe first at `{quoted}`?")
        else:
            question = (f"Which value first steps outside `{quoted}`?")
        return {
            "id": ex_id, "type": TYPE_NUM, "type_name": TYPE_NAME,
            "bloom": BLOOM,
            "concept_id": node_id or "boundary",
            "concept": name or "boundary", "file": file, "line": line,
            "commit": commit,
            "hints": _hints(quoted),
            "front": (f"{question} Reply with the edge integer.\n"
                      f"```python\n{code[:600]}\n```"),
            "back": (f"{edge}: probe {edge - 1} / {edge} / {edge + 1} — "
                     "the literal itself is the edge."),
            "payload": {"choices": choices, "answer": str(edge),
                        "site": quoted, "kind": kind,
                        "reference": str(edge), "grounded": True},
        }
    except Exception:
        return _ungrounded(ex_id, "", "app.py", 0, "")


def _ungrounded(ex_id, name, file, line, commit) -> dict:
    return {
        "id": ex_id, "type": TYPE_NUM, "type_name": TYPE_NAME,
        "bloom": BLOOM, "concept_id": "boundary",
        "concept": name or "boundary", "file": file, "line": line,
        "commit": commit, "hints": _hints("<expr>"),
        "front": "No boundary site found here.",
        "back": "Skipped by the pipeline.",
        "payload": {"choices": [], "answer": "", "site": "", "kind": "",
                    "reference": "", "grounded": False},
    }


def _fail(msg: str) -> dict:
    return {"pass": False, "score": 0.0, "feedback": msg}


def first_int(text: str):
    """First integer token; None when absent. Never raises."""
    try:
        m = _INT.search(str(text or ""))
        return int(m.group(0)) if m else None
    except Exception:  # noqa: BLE001
        return None


def grade(exercise: dict, submission: str, runner=None) -> dict:
    """First-integer-token match; no partial credit."""
    _ = runner
    try:
        return _grade(exercise, submission)
    except Exception as exc:  # noqa: BLE001 -- grading never raises
        return _fail(f"Grader hiccup ({exc}) — resubmit.")


def _grade(exercise: dict, submission: str) -> dict:
    p = (exercise or {}).get("payload", {}) or {}
    try:
        want = int(str(p.get("answer", "") or "").strip())
    except (TypeError, ValueError):
        return _fail("No edge recorded on this card.")
    text = str(submission if submission is not None else "")
    if not text.strip():
        return _fail("Name the edge integer first — then check the triple.")
    got = first_int(text)
    if got is None:
        return _fail("No integer found — reply with the edge value.")
    if got == want:
        return {"pass": True, "score": 1.0,
                "feedback": "Edge nailed — the triple habit holds."}
    return {"pass": False, "score": 0.0,
            "feedback": f"Off by {got - want}: the edge is {want}, not {got}."}


def disclosure() -> str:
    """One-line grading contract (also copied into the grading table)."""
    return ("Name the boundary value — the exact edge integer wins; "
            "neighbours are off by one.")


def render(exercise: dict) -> str:
    """Exercise widget: site question, three choice buttons, type-it input."""
    p = (exercise or {}).get("payload", {}) or {}
    front = html.escape(str(exercise.get("front", "")))
    type_name = html.escape(str(exercise.get("type_name", TYPE_NAME)))
    file_line = f"{exercise.get('file', '')}:{exercise.get('line', 0)}"
    buttons = "".join(
        f"<button name='answer' value='{html.escape(c, quote=True)}'>"
        f"{html.escape(c)}</button> "
        for c in p.get("choices", []))
    hints = "".join(
        f"<details><summary>Hint {i + 1}</summary>{html.escape(h)}</details>"
        for i, h in enumerate(exercise.get("hints", [])))
    return (
        f"<article><h3>{type_name}</h3>"
        f"<p>{front}</p>"
        f"<details><summary>How grading works</summary>"
        f"<p><small>{html.escape(disclosure())}</small></p>"
        f"</details>"
        f"<form method='post'>{buttons}<br>"
        f"<label>Or type it: <input name='answer' size='10'></label> "
        f"<button>Probe it</button></form>"
        f"{hints}<p><small>{html.escape(file_line)}</small></p></article>")


def section_html() -> str:
    """Anchored status subsection; wired into the status page by the parent."""
    return (
        f"<h3 id='{STATUS_ANCHOR}'>Boundary-value drills <small>(feature)</small></h3>"
        "<p>Name the ONE edge integer to probe first — off-by-one bootcamp "
        "for comparisons and ranges. <code>groundwork/boundary.py</code>.</p>"
    )


def tour_entry() -> dict:
    """Feature-tour registry entry (appended to tour.ENTRIES by parent)."""
    return {"id": "boundary-drill", "kind": "feature",
            "title": "Boundary-value drills",
            "blurb": "Name the ONE edge integer to probe first — off-by-one bootcamp.",
            "path": "/due", "anchor": "up-next"}
