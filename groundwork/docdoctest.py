"""Doc-example doctest exercise (type 32, F-9).

The learner writes a ``>>>`` example for the concept's function — call plus
expected output — that passes as a real doctest run against the shown code.
Grading uses the stdlib doctest runner with ELLIPSIS on, so documented
outputs, exceptions, and ``...`` abbreviations all behave like real doctests.
No sandbox runner is needed: the code under test is the lesson snippet
itself, executed in a fresh namespace.

Plugin API: ``generate(ex_id, concept, snippet, ctx)``,
``render(exercise) -> html``, ``grade(exercise, submission, runner)``.
Import-safe standalone: stdlib only (``ast``/``doctest``/``html``/``io``),
no groundwork imports. Registration lives in ``groundwork/exercises.py``
(TYPES, GENERATORS, BLOOM_TYPES); see ===WIRES===.
"""
from __future__ import annotations

import ast
import doctest
import html
import io

TYPE_NUM = 32
TYPE_NAME = "doc-example"
BLOOM = "apply"

FLAGS = doctest.ELLIPSIS


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


def _hints(concept_name: str, call: str, file: str, line: int) -> list[str]:
    where = f"{file}:{line}" if file and line else (file or "the linked file")
    return [
        f"Call `{concept_name}` in a `>>>` line, then write exactly what it prints or returns.",
        f"Look at {where}: `{call}` is a starting point — fix the arguments to fit the signature.",
        f"Worked step: `>>> {call}` followed by its real output passes. Trace the code once, then write it down.",
    ]


def generate(ex_id, concept, snippet, ctx) -> dict:
    """Build a doc-example exercise: write a passing doctest for the concept."""
    ctx = ctx or {}
    snippet = list(snippet or [])
    code = _code_for(concept, snippet, ctx)
    fname = _func_name(concept, code)
    call = f"{fname}()"
    expected = str(ctx.get("expected_output", "") or "").strip()
    if expected:
        reference = f">>> {call}\n{expected}"
    else:
        reference = f">>> {call}\n<expected output>"
    front = (
        f"Write a doctest example for `{fname}` that passes as a real "
        f"doctest run (`...` abbreviations allowed):\n"
        f"```python\n{code[:600]}\n```\n"
        f"Reply with `>>>` lines plus the exact expected output."
    )
    back = reference + "  (model answer — any passing example calling it counts)."
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
        "hints": _hints(fname, call, file, line),
        "front": front, "back": back,
        "payload": {"code": code, "func": fname, "call": call,
                    "reference": reference, "expected": expected,
                    "grounded": bool(expected)},
    }


def _fail(msg: str) -> dict:
    return {"pass": False, "score": 0.0, "feedback": msg}


def grade(exercise: dict, submission: str, runner=None) -> dict:
    """Run the submission as doctest against the payload code.

    Passes when at least one ``>>>`` example is attempted, every example
    passes, and one ``>>>`` line calls the payload function. ``runner`` is
    accepted for API symmetry and ignored — grading is pure stdlib.
    """
    _ = runner
    payload = (exercise or {}).get("payload", {})
    code = str(payload.get("code", "") or "")
    func = str(payload.get("func", "") or "")
    text = str(submission or "").strip()
    if not text or ">>>" not in text:
        return _fail("Submit doctest lines starting with `>>>` plus the expected output.")
    if func and not any(
        ln.lstrip().startswith(">>>") and func in ln
        for ln in text.splitlines()
    ):
        return _fail(f"Your example must call `{func}` in a `>>>` line.")
    globs: dict = {}
    try:
        exec(compile(code, "<exercise>", "exec"), globs)
    except Exception as exc:  # noqa: BLE001 — the snippet itself is on trial
        return _fail(f"The shown code does not run here: {exc}")
    parser = doctest.DocTestParser()
    try:
        test = parser.get_doctest(text, globs, func or "example", None, 0)
    except ValueError:
        return _fail("No doctest example found — start a line with `>>>`.")
    buf = io.StringIO()
    doc_runner = doctest.DocTestRunner(optionflags=FLAGS, verbose=False)
    doc_runner.run(test, out=buf.write)
    attempted, failed = doc_runner.tries, doc_runner.failures
    if attempted == 0:
        return _fail("No doctest example found — start a line with `>>>`.")
    if failed:
        detail = buf.getvalue().strip().splitlines()
        excerpt = " ".join(detail[-3:])[:200] if detail else ""
        return {
            "pass": False, "score": (attempted - failed) / attempted,
            "feedback": f"{failed}/{attempted} examples failed — re-check the expected output. {excerpt}".strip(),
        }
    return {"pass": True, "score": 1.0,
            "feedback": f"Doctest green: {attempted}/{attempted} examples pass."}


def render(exercise: dict) -> str:
    """Exercise widget: instructions plus a textarea seeded with the call."""
    payload = (exercise or {}).get("payload", {})
    front = html.escape(str(exercise.get("front", "")))
    concept = html.escape(str(exercise.get("concept", "")))
    type_name = html.escape(str(exercise.get("type_name", TYPE_NAME)))
    seed = html.escape(f">>> {payload.get('call', 'func()')}\n")
    file_line = f"{exercise.get('file', '')}:{exercise.get('line', 0)}"
    hints = "".join(
        f"<details><summary>Hint {i + 1}</summary>{html.escape(h)}</details>"
        for i, h in enumerate(exercise.get("hints", []))
    )
    return (
        f"<article><h3>{concept} · {type_name}</h3>"
        f"<p>{front}</p>"
        f"<details><summary>How grading works</summary>"
        f"<p><small>Your `>>>` example must run green as a doctest "
        f"(`...` allowed) and call the function.</small></p></details>"
        f"<form method='post'><textarea name='answer' rows='6' cols='70'>{seed}</textarea>"
        f"<br><button>Run doctest</button></form>{hints}"
        f"<p><small>{html.escape(file_line)}</small></p></article>"
    )


def section_html() -> str:
    """Anchored status subsection; wired into the status page by the parent."""
    return (
        "<h3 id='status-b6-docdoctest'>Doc-example doctest <small>(feature)</small></h3>"
        "<p>Write a <code>&gt;&gt;&gt;</code> example that passes as a real "
        "doctest run — graded by the stdlib runner, no sandbox. "
        "<code>groundwork/docdoctest.py</code>.</p>"
    )
