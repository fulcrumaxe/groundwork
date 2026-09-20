"""Complexity golf: shrink nesting without breaking behavior (F-4).

New exercise plugin (proposed type 26, bloom analyse). The learner gets
a nested function plus its AST-measured max nesting depth and must
submit a rewrite that nests strictly less deeply while keeping the
hidden tests green. Pure functions, stdlib only (ast/html); no DB, no I/O.

Metric: branch-nesting depth = the largest number of enclosing
block-introducing nodes (if/for/while/with/try/except/match) around any
statement. A flat function body is depth 0; one `if` level is depth 1.
`def`/`class` lines add nothing, and comprehensions, boolean operators
and ternaries add nothing.

Plugin API: generate(ex_id, concept, snippet, ctx),
render(exercise) -> html, grade(exercise, submission, runner).
Import-safe standalone: imports nothing from groundwork, so
exercises.py can import this module without a cycle.
"""
from __future__ import annotations

import ast
import html

TYPE_NUM = 26
TYPE_NAME = "complexity-golf"
BLOOM = "analyse"
DISCLOSURE = (
    "Your rewrite must nest less deeply (AST-measured) "
    "and keep the hidden tests green."
)

_NEST_NAMES = ("If", "For", "AsyncFor", "While", "With", "AsyncWith",
               "Try", "ExceptHandler", "Match", "match_case")
_NEST_NODES = tuple(getattr(ast, n) for n in _NEST_NAMES if hasattr(ast, n))


def _parse(code: str) -> ast.AST | None:
    try:
        return ast.parse(str(code))
    except (SyntaxError, ValueError):
        return None


def max_nesting(code: str) -> int | None:
    """Deepest branch-nesting depth in code; None when it does not parse."""
    tree = _parse(code)
    if tree is None:
        return None

    def _walk(node: ast.AST, cur: int) -> int:
        best = cur
        for child in ast.iter_child_nodes(node):
            nxt = cur + 1 if isinstance(child, _NEST_NODES) else cur
            got = _walk(child, nxt)
            if got > best:
                best = got
        return best

    return _walk(tree, 0)


def _defined(code: str) -> set[str]:
    """Names of every defined function (nested counts; trivial pass fails)."""
    tree = _parse(code)
    if tree is None:
        return set()
    return {n.name for n in ast.walk(tree)
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}


def _hints(name: str, depth: int, target: int) -> list[str]:
    return [
        f"Flatten one level of `{name}` first — early return beats nesting.",
        f"Current max nesting is {depth}; your rewrite must reach "
        f"{target} or less without changing behavior.",
        f"Worked step: guard-clause the outer `if`, then dedent the rest. "
        f"Re-measure with max_nesting before submitting.",
    ]


def _base(ex_id: str, concept, snippet: list[str], commit: str) -> dict:
    return {
        "id": ex_id, "type": TYPE_NUM, "type_name": TYPE_NAME, "bloom": BLOOM,
        "concept_id": concept.node_id, "concept": concept.name,
        "file": concept.file, "line": concept.line, "commit": commit,
    }


def generate(ex_id, concept, snippet, ctx) -> dict:
    """Deal one golf card: nested code, measured depth, and a lower target."""
    ctx = ctx or {}
    code = ctx.get("runnable") or "\n".join(snippet or []) or "pass"
    depth = max_nesting(code)
    target = max(0, (depth or 0) - 1)
    tests = ctx.get("tests", "")
    grounded = bool(tests) and depth is not None and depth >= 2
    ex = _base(ex_id, concept, snippet or [], ctx.get("commit", ""))
    depth_txt = depth if depth is not None else "?"
    ex.update(
        front=f"Complexity golf: rewrite `{concept.name}` so its max nesting "
        f"depth drops from {depth_txt} to {target} or less — same behavior.\n"
        f"```python\n{code[:800]}\n```",
        back=code,
        hints=_hints(concept.name, depth if depth is not None else 0, target),
        payload={"original": code, "depth": depth, "target": target,
                 "tests": tests, "reference": code, "func": concept.name,
                 "grounded": grounded})
    return ex


def _fail(feedback: str) -> dict:
    return {"pass": False, "score": 0.0, "feedback": feedback}


def grade(exercise: dict, submission: str, runner=None) -> dict:
    """Pass = parses, still defines the function, nests less, tests green."""
    p = exercise.get("payload", {})
    func = p.get("func") or exercise.get("concept", "")
    submission = str(submission)
    old = p.get("depth")
    if old is None:
        old = max_nesting(p.get("original", ""))
    new = max_nesting(submission)
    if new is None:
        return _fail("Submission does not parse — submit runnable Python.")
    if func and func not in _defined(submission):
        return _fail(f"Your rewrite must still define `{func}` "
                     f"(a bare `pass` nests at 0 but solves nothing).")
    if old is not None:
        target = p.get("target", max(0, old - 1))
        if new > target:
            return _fail(f"Nesting is {new}; it must be {target} or less "
                         f"(original {old}). Flatten one level and retry.")
    tests = p.get("tests", "")
    if tests:
        if runner is None:
            return _fail("No sandbox available for grading.")
        res = runner.run(submission + "\n" + tests)
        if res.ok and "FAIL" not in res.stdout:
            return {"pass": True, "score": 1.0,
                    "feedback": f"Shallower ({old} → {new}) and green."}
        return _fail(f"Nesting is down ({new}) but the tests fail: "
                     f"{res.stdout[:200]} {res.stderr[:200]}")
    return {"pass": True, "score": 1.0,
            "feedback": f"Nesting {old} → {new}, `{func}` intact."}


def render(exercise: dict) -> str:
    """Golf card: metric line, original code, rewrite textarea, hints."""
    p = exercise.get("payload", {})
    front = html.escape(exercise.get("front", ""))
    original = html.escape(p.get("original", ""))
    metric = (f"<p><small>Max nesting {p.get('depth')} → "
              f"target {p.get('target')} or less (AST-measured).</small></p>")
    body = (f"<p>{front}</p>{metric}<pre>{original}</pre>"
            "<form method='post'><textarea name='answer' rows='12' "
            "cols='70' placeholder='Paste your flatter rewrite here'>"
            "</textarea><br><button>Run tests</button></form>")
    hints = "".join(f"<details><summary>Hint {i + 1}</summary>"
                    f"{html.escape(h)}</details>"
                    for i, h in enumerate(exercise.get("hints", [])))
    return (f"<article><h3>{html.escape(exercise.get('concept', ''))} "
            f"· {html.escape(exercise.get('type_name', TYPE_NAME))}</h3>"
            f"{body}{hints}"
            f"<p><small>{html.escape(exercise.get('file', ''))}:"
            f"{exercise.get('line', 0)}</small></p></article>")


def section_html() -> str:
    """Status-page home for this item (anchor status-b6-golf)."""
    return ("<h3 id='status-b6-golf'>Complexity golf "
            "<small>(feature)</small></h3>"
            "<p>Rewrite a nested function so it nests less deeply — "
            "AST-measured, tests stay green. "
            "<code>groundwork/golf.py</code>.</p>")
