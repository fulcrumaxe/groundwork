"""Issue-reproduction exercise (type 44, F-21, bloom: apply).

The learner gets a bug report synthesized from the verified-breaking
mutation (``ctx["buggy"]``/``ctx["bug_line"]`` when present, else the
snippet) and must write a minimal repro script that reproduces the
failure. Grading RUNS the submission via the sandbox runner against
the shown code — pass needs a failure signal (non-zero exit / FAIL or
error output) within a line budget. With ``runner=None`` (or a runner
error) grading is a failing grade, never a pass and never a raise:
execution is the proof, so there is no offline fallback.

Plugin API: ``generate(ex_id, concept, snippet, ctx)``,
``render(exercise) -> html``, ``grade(exercise, submission, runner)``,
plus ``emits(ctx) -> bool`` (pipeline emission guard predicate).
Import-safe standalone: stdlib only (``ast``/``html``/``re``), no
groundwork imports. Registration lives in ``groundwork/exercises.py``
(TYPES, GENERATORS, BLOOM_TYPES); see ===WIRES===.

BLOOM bucket: apply — the learner executes the reported scenario,
like predict-output (8) and property-test (33). Emission guard:
fault-gated, skip when "buggy" not in ctx — a repro of healthy code
has no failure to reproduce, so the card would be unwinnable.
"""
from __future__ import annotations

import ast
import html
import re

TYPE_NUM = 44
TYPE_NAME = "issue-repro"
BLOOM = "apply"
AREA = "repro"

MAX_LINES = 20
MAX_CHARS = 2000


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
    code = str(ctx.get("buggy") or ctx.get("runnable")
              or "\n".join(snippet or []) or "").strip()
    if not code:
        code = f"def {_concept_field(concept, 'name', 'func') or 'func'}(x):\n    return x"
    return code


def _hints(fname: str, file: str, line: int) -> list[str]:
    where = f"{file}:{line}" if file and line else (file or "the linked file")
    return [
        f"Read the report, then call `{fname}` with the smallest input that still fails.",
        f"Look at {where}: your script must exercise `{fname}` itself, not just crash on its own.",
        f"Worked step: one failing call plus an `assert`, e.g. `assert {fname}(...) == ...` — under {MAX_LINES} lines.",
    ]


def emits(ctx: dict | None) -> bool:
    """Emission guard predicate: only emit from a verified-breaking mutation."""
    return bool((ctx or {}).get("buggy"))


def generate(ex_id, concept, snippet, ctx) -> dict:
    """Build an issue-repro card: bug report + shown code, learner writes the repro."""
    ctx = ctx or {}
    snippet = list(snippet or [])
    code = _code_for(concept, snippet, ctx)
    fname = _func_name(concept, code)
    try:
        bug_line = int(ctx.get("bug_line", 0) or 0)
    except (TypeError, ValueError):
        bug_line = 0
    fault = str(ctx.get("fault") or ("the injected defect" if ctx.get("buggy")
                                     else "a reported failure"))
    grounded = bool(ctx.get("buggy"))
    if bug_line:
        report = (f"Bug report: `{fname}` fails ({fault}). "
                  f"Suspected line: {bug_line}.")
    else:
        report = f"Bug report: `{fname}` fails ({fault})."
    reference = f"assert {fname}(...)  # minimal failing call"
    front = (
        f"{report}\n"
        f"```python\n{code[:600]}\n```\n"
        f"Write a minimal repro script (at most {MAX_LINES} lines) that "
        f"exercises `{fname}` and fails because of this bug."
    )
    back = f"Model repro: `{reference}` — any script under {MAX_LINES} lines that fails counts."
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
        "hints": _hints(fname, file, line),
        "front": front, "back": back,
        "payload": {"code": code, "func": fname, "bug_line": bug_line,
                    "report": report, "fault": fault, "grounded": grounded,
                    "max_lines": MAX_LINES},
    }


def _fail(msg: str) -> dict:
    return {"pass": False, "score": 0.0, "feedback": msg}


def _failed(res) -> bool:
    """True when a runner result carries a failure signal."""
    if not getattr(res, "ok", True):
        return True
    out = str(getattr(res, "stdout", "") or "") + str(getattr(res, "stderr", "") or "")
    return bool(re.search(r"FAIL|Traceback|Error|assert", out))


def grade(exercise: dict, submission: str, runner=None) -> dict:
    """Run the repro script; pass when it reproduces the failure, minimally.

    The submission must parse, CALL the target function (a bare crash
    or a comment merely mentioning it proves nothing), fit the line
    budget, and — when executed against the shown code — produce a
    failure signal. No runner, or a runner error, grades as fail,
    never raises.
    """
    try:
        payload = (exercise or {}).get("payload", {}) or {}
        code = str(payload.get("code", "") or "")
        func = str(payload.get("func", "") or "")
        try:
            budget = int(payload.get("max_lines", MAX_LINES) or MAX_LINES)
        except (TypeError, ValueError):
            budget = MAX_LINES
        text = str(submission or "").strip()
        if not text:
            return _fail("Submit a repro script that exercises the reported bug.")
        if len(text) > MAX_CHARS:
            return _fail(f"Keep the repro minimal — under {MAX_CHARS} characters.")
        if len(text.splitlines()) > budget:
            return _fail(f"Keep the repro minimal — at most {budget} lines.")
        try:
            ast.parse(text)
        except (SyntaxError, ValueError):
            return _fail("Submission does not parse — submit runnable Python.")
        flat = re.sub(r"\s+", " ", text)
        if func and func not in flat:
            return _fail(f"The repro must exercise `{func}` — a bare crash proves nothing.")
        if func and not re.search(r"\b" + re.escape(func) + r"\s*\(", text):
            return _fail(f"The repro must call `{func}(...)` — a comment or crash without a call proves nothing.")
        if runner is None or not code.strip():
            return _fail("No runner available — the repro cannot be verified.")
        try:
            res = runner.run(code + f"\n{text}\n")
        except Exception:
            return _fail("The runner could not execute the repro — try again.")
        if _failed(res):
            return {"pass": True, "score": 1.0,
                    "feedback": "Repro fails as reported — minimal and verified."}
        return _fail("The repro passes cleanly — it does not reproduce the reported failure.")
    except Exception:  # noqa: BLE001 — grading never raises
        return _fail("Grader could not read the submission — submit a repro script.")


def render(exercise: dict) -> str:
    """Exercise widget: bug report plus a repro-script answer box."""
    payload = (exercise or {}).get("payload", {}) or {}
    front = html.escape(str(exercise.get("front", "")))
    concept = html.escape(str(exercise.get("concept", "")))
    type_name = html.escape(str(exercise.get("type_name", TYPE_NAME)))
    seed = html.escape(f"assert {payload.get('func', 'func')}(...)")
    file_line = f"{exercise.get('file', '')}:{exercise.get('line', 0)}"
    hints = "".join(
        f"<details><summary>Hint {i + 1}</summary>{html.escape(h)}</details>"
        for i, h in enumerate(exercise.get("hints", []))
    )
    return (
        f"<article><h3>{concept} · {type_name}</h3>"
        f"<p>{front}</p>"
        f"<details><summary>How grading works</summary>"
        f"<p><small>Your script runs in the sandbox against the shown code. "
        f"It passes when the run reproduces the failure (non-zero exit, "
        f"FAIL marker, or error output) within the line budget — a script "
        f"that passes cleanly, or never calls the reported function, fails."
        f"</small></p></details>"
        f"<form method='post'><textarea name='answer' rows='6' cols='70'>{seed}</textarea>"
        f"<br><button>Run repro</button></form>{hints}"
        f"<p><small>{html.escape(file_line)}</small></p></article>"
    )


def section_html() -> str:
    """Anchored status subsection; wired into the status page by the parent."""
    return (
        "<h3 id='status-b8-repro'>Issue reproduction <small>(feature)</small></h3>"
        "<p>Write a minimal repro script from a bug report — graded by "
        "running it in the sandbox and checking it reproduces the failure "
        "within a line budget. "
        "<code>groundwork/repro.py</code>.</p>"
    )


def tour_entry() -> dict:
    """Feature-tour registry entry for the parent to append."""
    return {"id": "repro-type", "kind": "feature",
            "title": "Issue reproduction",
            "blurb": "Write a minimal repro script from a bug report; the sandbox confirms it fails.",
            "path": "/status", "anchor": "status-b8-repro"}
