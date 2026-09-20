"""Error-handling retrofit: add the missing branch (F-6, type 28).

The learner gets working code with no error branch plus a fault-injection
harness (hidden tests feeding an exceptional input). They add the missing
guard/try-except so the fault is handled and normal behavior keeps working.

Sibling contrast: fix-bug (14) repairs a wrong line; this type adds a
branch that was never there. Grading proves both halves live in the
sandbox: the shown code must FAIL the harness (fault reproduces) and the
submission must go GREEN on the same harness.

Plugin API: generate(ex_id, concept, snippet, ctx), render(exercise)->html,
grade(exercise, submission, runner). Pure functions, stdlib only, no DB,
no schema changes, no web.py edits. Import-safe standalone: this module
never imports sibling area modules, so exercises.py can import it for
registration without a cycle.
"""
from __future__ import annotations

import html

TYPE_NUM = 28
TYPE_NAME = "error-branch"
BLOOM = "analyse"

DEFAULT_FAULT = "an exceptional input (None, empty, zero, or out-of-range)"


def _hints(question: str, answer: str, snippet: list[str],
           file: str = "", line: int = 0) -> list[str]:
    """Three hints mirroring exercises._hints (local copy: no cycle)."""
    if snippet and file:
        where = f"{file}:{line}" if line else file
        pointer = f"Look at {where}: `{snippet[0].strip()}`"
    elif snippet:
        pointer = f"Re-read this snippet: `{snippet[0].strip()}`"
    else:
        pointer = "Re-read the linked file."
    return [f"Recall what {question} must do on bad input before answering.",
            pointer,
            f"Worked step: the fix involves `{answer[:80]}`. Now say why."]


def _base(ex_id: str, concept, commit: str) -> dict:
    """Exercise envelope mirroring exercises._base for type 28."""
    snippet = [getattr(concept, "name", "") or ""]
    return {
        "id": ex_id, "type": TYPE_NUM, "type_name": TYPE_NAME,
        "bloom": BLOOM,
        "concept_id": getattr(concept, "node_id", ""),
        "concept": getattr(concept, "name", ""),
        "file": getattr(concept, "file", ""),
        "line": getattr(concept, "line", 0), "commit": commit,
        "hints": _hints(getattr(concept, "name", ""),
                        getattr(concept, "name", ""), snippet,
                        getattr(concept, "file", ""),
                        getattr(concept, "line", 0)),
    }


def generate(ex_id, concept, snippet, ctx) -> dict:
    """Build the retrofit card: unguarded code + fault harness.

    Pipeline cards show the verified-breaking mutation (ctx "buggy"):
    the harness demonstrably fails on the shown code, so the card is
    live. Plain runnable code passes its own harness, which would make
    every card stale — those stay ungrounded.
    """
    ctx = ctx or {}
    buggy = ctx.get("buggy", "")
    code = buggy or ctx.get("runnable") or "\n".join(snippet or []) or "pass"
    tests = ctx.get("tests", "")
    reference = ctx.get("fixed", "")
    fault = ctx.get("fault", "") or ("the injected defect" if buggy
                                     else DEFAULT_FAULT)
    ex = _base(ex_id, concept, ctx.get("commit", ""))
    ex.update(
        front=(f"Add the missing error-handling branch to "
               f"`{concept.name}`: it currently fails on {fault}. "
               f"Handle the fault without changing normal behavior.\n"
               f"```python\n{code[:600]}\n```"),
        back=reference or f"Guard `{concept.name}` against {fault}.",
        payload={"code": code, "tests": tests, "reference": reference,
                 "fault": fault, "grounded": bool(tests) and bool(buggy)})
    return ex


def grade(exercise: dict, submission: str, runner=None) -> dict:
    """Grade: base must FAIL the harness, submission must go GREEN."""
    p = exercise.get("payload", {}) if isinstance(exercise, dict) else {}
    tests = p.get("tests", "")
    if not tests:
        return {"pass": False, "score": 0.0,
                "feedback": "No fault harness available."}
    if runner is None:
        return {"pass": False, "score": 0.0,
                "feedback": "No sandbox available for grading."}
    submission = str(submission)
    if not submission.strip():
        return {"pass": False, "score": 0.0,
                "feedback": "Empty submission — add the missing branch."}
    try:
        compile(submission, "<submission>", "exec")
    except (SyntaxError, ValueError) as exc:
        return {"pass": False, "score": 0.0,
                "feedback": f"Submission does not parse: {exc}."}
    base = p.get("code", "")
    if base.strip():
        ref = runner.run(base + "\n" + tests)
        if ref.ok and "FAIL" not in ref.stdout:
            return {"pass": False, "score": 0.0,
                    "feedback": "Fault no longer reproduces; flagged stale."}
    res = runner.run(submission + "\n" + tests)
    ok = res.ok and "FAIL" not in res.stdout
    if ok:
        return {"pass": True, "score": 1.0,
                "feedback": "Fault handled and old behavior holds."}
    detail = (res.stdout[:300] + " " + res.stderr[:300]).strip()
    return {"pass": False, "score": 0.0,
            "feedback": f"Still failing: {detail or 'no output'}"}


def render(exercise: dict) -> str:
    """Card HTML: prompt, code textarea, submit, hints, file:line."""
    p = exercise.get("payload", {})
    front = html.escape(exercise.get("front", ""))
    code = html.escape(p.get("code", ""))
    body = (f"<p>{front}</p>"
            f"<form method='post'><textarea name='answer' rows='12' "
            f"cols='70'>{code}</textarea><br>"
            f"<button>Run fault tests</button></form>")
    hints = "".join(
        f"<details><summary>Hint {i + 1}</summary>{html.escape(h)}</details>"
        for i, h in enumerate(exercise.get("hints", [])))
    return (f"<article><h3>{html.escape(exercise.get('concept', ''))} "
            f"· {html.escape(exercise.get('type_name', TYPE_NAME))}</h3>"
            f"{body}{hints}"
            f"<p><small>{html.escape(exercise.get('file', ''))}:"
            f"{exercise.get('line', 0)}</small></p></article>")


def section_html(db_path: str = "") -> str:
    """Status-page home for this area (never in web.py)."""
    _ = db_path  # pure section: no DB read needed
    return ("<h3 id='status-b6-errbranch'>Error-handling retrofit "
            "<small>(feature)</small></h3>"
            "<p>Type-28 exercises hand you code with no error branch plus a "
            "fault-injection harness; add the missing guard so the fault is "
            "handled and old behavior stays green. "
            "<code>groundwork/errbranch.py</code>.</p>")
