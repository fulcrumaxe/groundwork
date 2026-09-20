"""Property-based test authoring exercise (type 33, F-10).

The learner writes ``assert`` invariant lines for the concept's function
— properties that must hold for every valid input (determinism, bounds,
types, round-trips) — without any Hypothesis dependency (offline,
stdlib-only rule). Grading execs each invariant line against the lesson
snippet in a fresh namespace with a safe-builtins subset and reports
pass/fail per invariant with partial credit. No sandbox runner needed.

Plugin API: ``generate(ex_id, concept, snippet, ctx)``,
``render(exercise) -> html``, ``grade(exercise, submission, runner)``.
Import-safe standalone: stdlib only (``ast``/``html``), no groundwork
imports. Registration lives in ``groundwork/exercises.py``
(TYPES, GENERATORS, BLOOM_TYPES); see ===WIRES===.
"""
from __future__ import annotations

import ast
import html

TYPE_NUM = 33
TYPE_NAME = "property-test"
BLOOM = "apply"

MAX_INVARIANTS = 12

# Pipeline emission guard (mirrors type 8 in pipeline.py): invariants must
# execute real code, so the card is skipped when "runnable" not in ctx.
REQUIRES = ("runnable",)

SAFE_BUILTINS = {
    "abs": abs, "all": all, "any": any, "bool": bool, "dict": dict,
    "enumerate": enumerate, "filter": filter, "float": float,
    "frozenset": frozenset, "int": int, "isinstance": isinstance,
    "issubclass": issubclass, "iter": iter, "len": len, "list": list,
    "map": map, "max": max, "min": min, "next": next, "range": range,
    "repr": repr, "reversed": reversed, "round": round, "set": set,
    "slice": slice, "sorted": sorted, "str": str, "sum": sum,
    "tuple": tuple, "zip": zip, "Exception": Exception,
    "AssertionError": AssertionError, "ValueError": ValueError,
    "TypeError": TypeError, "IndexError": IndexError,
    "KeyError": KeyError, "AttributeError": AttributeError,
    "StopIteration": StopIteration,
}


def emits(ctx) -> bool:
    """True when ctx carries everything the pipeline guard requires."""
    ctx = ctx or {}
    return all(k in ctx for k in REQUIRES)


def _concept_field(concept, name: str, default: str = "") -> str:
    return str(getattr(concept, name, default) or default)


def _func_name(concept, code: str) -> str:
    """Def matching the concept, else the first def, else the concept name."""
    want = _concept_field(concept, "name", "func")
    try:
        tree = ast.parse(code)
    except (SyntaxError, ValueError):
        return want or "func"
    first = ""
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if not first:
                first = node.name
            if node.name == want:
                return want
    return want if want else (first or "func")


def _code_for(concept, snippet: list[str], ctx: dict) -> str:
    code = str(ctx.get("runnable") or "\n".join(snippet or []) or "").strip()
    if not code:
        name = _concept_field(concept, "name", "func")
        code = f"def {name}():\n    return None"
    return code


def _hints(concept_name: str, call: str, expected: str,
           file: str, line: int) -> list[str]:
    where = f"{file}:{line}" if file and line else (file or "the linked file")
    want = expected or "<real output>"
    return [
        f"Each line starts with `assert` and calls `{concept_name}` — "
        "state what must always hold, not one example's steps.",
        f"Look at {where}: try determinism first — "
        f"`assert {call} == {call}` always runs.",
        f"Worked step: `assert {call} == {want}` passes — then add a "
        "second property (bounds, type, round-trip).",
    ]


def generate(ex_id, concept, snippet, ctx) -> dict:
    """Build a property-test exercise: write invariants for the concept."""
    ctx = ctx or {}
    snippet = list(snippet or [])
    code = _code_for(concept, snippet, ctx)
    fname = _func_name(concept, code)
    call = str(ctx.get("call") or f"{fname}()")
    expected = str(ctx.get("expected_output", "") or "").strip()
    if expected:
        reference = [f"assert {call} == {expected}",
                     f"assert {call} == {call}  # deterministic"]
    else:
        reference = [f"assert {call} == <expected output>",
                     f"assert {call} == {call}  # deterministic"]
    front = (
        f"Write 2+ `assert` invariant lines for `{fname}` — properties "
        f"that hold for every valid input:\n"
        f"```python\n{code[:600]}\n```\n"
        f"Reply with `assert` lines only, each calling `{fname}`."
    )
    back = "\n".join(reference) + "  (model answer — any holding set counts)."
    name = _concept_field(concept, "name", fname)
    file = _concept_field(concept, "file")
    try:
        line = int(getattr(concept, "line", 0) or 0)
    except (TypeError, ValueError):
        line = 0
    return {
        "id": ex_id, "type": TYPE_NUM, "type_name": TYPE_NAME, "bloom": BLOOM,
        "concept_id": _concept_field(concept, "node_id", name),
        "concept": name,
        "file": file, "line": line,
        "commit": str(ctx.get("commit", "") or ""),
        "hints": _hints(fname, call, expected, file, line),
        "front": front, "back": back,
        "payload": {"code": code, "func": fname, "call": call,
                    "expected": expected, "reference": reference,
                    "grounded": bool(expected)},
    }


def _fail(msg: str) -> dict:
    return {"pass": False, "score": 0.0, "feedback": msg}


def _invariants_of(text: str) -> list[str]:
    """Submitted `assert` lines; blanks and `#` comments ignored."""
    out = []
    for ln in text.splitlines():
        s = ln.strip()
        if s and not s.startswith("#") and s.startswith("assert"):
            out.append(s)
    return out


def grade(exercise: dict, submission: str, runner=None) -> dict:
    """Run each invariant line against the payload code in a fresh namespace.

    Passes when at least one ``assert`` line is submitted, one mentions
    the payload function, and every line holds. ``runner`` is accepted
    for API symmetry and ignored — grading is pure stdlib. Never raises.
    """
    _ = runner
    payload = (exercise or {}).get("payload", {})
    code = str(payload.get("code", "") or "")
    func = str(payload.get("func", "") or "")
    text = str(submission or "").strip()
    if not text:
        what = f"`{func}`" if func else "the function"
        return _fail(f"Write at least one `assert` line stating a property of {what}.")
    invs = _invariants_of(text)
    if not invs:
        return _fail("Submit `assert` lines (e.g. `assert add(2, 3) == 5`).")
    if func and not any(func in ln for ln in invs):
        return _fail(f"At least one invariant must call `{func}`.")
    globs: dict = {"__builtins__": SAFE_BUILTINS}
    try:
        exec(compile(code, "<exercise>", "exec"), globs)
    except Exception as exc:  # noqa: BLE001 — the snippet itself is on trial
        return _fail(f"The shown code does not run here: {exc}")
    tried = invs[:MAX_INVARIANTS]
    bad = []
    for i, ln in enumerate(tried):
        try:
            exec(compile(ln, f"<invariant {i + 1}>", "exec"), globs)
        except AssertionError:
            bad.append(f"line {i + 1} failed: {ln[:80]}")
        except Exception as exc:  # noqa: BLE001 — a bad invariant is a grade, not a crash
            bad.append(f"line {i + 1} raised {type(exc).__name__}: {exc}"[:120])
    if bad:
        detail = "; ".join(bad[:3])
        return {
            "pass": False, "score": (len(tried) - len(bad)) / len(tried),
            "feedback": f"{len(bad)}/{len(tried)} invariants failed — {detail}",
        }
    return {"pass": True, "score": 1.0,
            "feedback": f"All {len(tried)} invariants hold."}


def render(exercise: dict) -> str:
    """Exercise widget: instructions plus a textarea seeded with invariants."""
    payload = (exercise or {}).get("payload", {})
    front = html.escape(str(exercise.get("front", "")))
    concept = html.escape(str(exercise.get("concept", "")))
    type_name = html.escape(str(exercise.get("type_name", TYPE_NAME)))
    ref = payload.get("reference", [])
    seed = html.escape("\n".join(ref[:2]) + ("\n" if ref else ""))
    file_line = f"{exercise.get('file', '')}:{exercise.get('line', 0)}"
    hints = "".join(
        f"<details><summary>Hint {i + 1}</summary>{html.escape(h)}</details>"
        for i, h in enumerate(exercise.get("hints", []))
    )
    return (
        f"<article><h3>{concept} · {type_name}</h3>"
        f"<p>{front}</p>"
        f"<details><summary>How grading works</summary>"
        f"<p><small>Each <code>assert</code> line runs against the shown code; "
        f"every line must hold and one must call the function.</small></p></details>"
        f"<form method='post'><textarea name='answer' rows='6' cols='70'>{seed}</textarea>"
        f"<br><button>Check invariants</button></form>{hints}"
        f"<p><small>{html.escape(file_line)}</small></p></article>"
    )


def section_html() -> str:
    """Anchored status subsection; wired into the status page by the parent."""
    return (
        "<h3 id='status-b7-proptest'>Property-based test authoring <small>(feature)</small></h3>"
        "<p>Write <code>assert</code> invariants for the concept function — "
        "graded per invariant in a fresh namespace, no Hypothesis needed. "
        "<code>groundwork/proptest.py</code>.</p>"
    )
