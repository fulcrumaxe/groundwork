"""Perf fix: rewrite a loop-heavy function to lower complexity (F-12).

New exercise plugin (type 35, bloom modify). The learner gets a
loop-heavy function plus its AST-measured complexity score and must
submit a rewrite with a strictly lower score while keeping the hidden
tests green. Pure functions, stdlib only (ast/html); no DB, no I/O.

Metric (loop-nesting/complexity proxy, mirrors golf type 26):
complexity = max_nesting + loop_count, where max_nesting is the
deepest branch-nesting depth (if/for/while/with/try/except/match
around any statement; def/class add nothing; comprehensions,
boolean operators and ternaries add nothing) and loop_count is the
number of for/while nodes. A flat function scores 0.

Grading is AST gate + tests-green, NOT wall-clock timing: a timeit
benchmark gate would flake in CI, while AST measurement plus the
existing assert-only harness is fully deterministic.

Plugin API: generate(ex_id, concept, snippet, ctx),
render(exercise) -> html, grade(exercise, submission, runner).
Import-safe standalone: imports nothing from groundwork, so
exercises.py can import this module without a cycle.
"""
from __future__ import annotations

import ast
import html

TYPE_NUM = 35
TYPE_NAME = "perf-fix"
BLOOM = "modify"
DISCLOSURE = (
    "Your rewrite must score strictly lower (AST-measured) "
    "and keep the hidden tests green — no timing involved."
)

_NEST_NAMES = ("If", "For", "AsyncFor", "While", "With", "AsyncWith",
               "Try", "ExceptHandler", "Match", "match_case")
_NEST_NODES = tuple(getattr(ast, n) for n in _NEST_NAMES if hasattr(ast, n))
_LOOP_NODES = tuple(getattr(ast, n) for n in ("For", "AsyncFor", "While")
                    if hasattr(ast, n))


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


def loop_count(code: str) -> int | None:
    """Number of for/while loop nodes; None when code does not parse."""
    tree = _parse(code)
    if tree is None:
        return None
    return sum(1 for n in ast.walk(tree) if isinstance(n, _LOOP_NODES))


def complexity(code: str) -> int | None:
    """AST complexity proxy: max_nesting + loop_count; None if unparseable."""
    depth = max_nesting(code)
    loops = loop_count(code)
    if depth is None or loops is None:
        return None
    return depth + loops


def emits(ctx: dict | None) -> bool:
    """Emission guard: needs the measured assert-only harness in ctx."""
    return "tests" in (ctx or {})


def _concept_field(concept, name: str, default: str = "") -> str:
    return str(getattr(concept, name, default) or default)


def _defined(code: str) -> set[str]:
    """Names of every defined function (nested counts; trivial pass fails)."""
    tree = _parse(code)
    if tree is None:
        return set()
    return {n.name for n in ast.walk(tree)
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}


def _hints(name: str, score: int, target: int) -> list[str]:
    return [
        f"Replace one loop in `{name}` first — a comprehension, sum(), or "
        f"set/dict lookup beats a nested scan.",
        f"Current complexity is {score}; your rewrite must reach "
        f"{target} or less without changing behavior.",
        f"Worked step: hoist the inner loop into a comprehension, then "
        f"re-measure with complexity() before submitting.",
    ]


def generate(ex_id, concept, snippet, ctx) -> dict:
    """Deal one perf-fix card: loop-heavy code, measured score, lower target."""
    ctx = ctx or {}
    snippet = list(snippet or [])
    code = str(ctx.get("runnable") or "\n".join(snippet) or "pass")
    score = complexity(code)
    loops = loop_count(code)
    target = max(0, (score or 0) - 1)
    tests = ctx.get("tests", "")
    grounded = (bool(tests) and score is not None
                and score >= 2 and (loops or 0) >= 1)
    name = _concept_field(concept, "name", "func")
    score_txt = score if score is not None else "?"
    return {
        "id": ex_id, "type": TYPE_NUM, "type_name": TYPE_NAME, "bloom": BLOOM,
        "concept_id": _concept_field(concept, "node_id", name),
        "concept": name,
        "file": _concept_field(concept, "file"),
        "line": getattr(concept, "line", 0) or 0,
        "commit": str(ctx.get("commit", "") or ""),
        "hints": _hints(name, score or 0, target),
        "front": (
            f"Perf fix: rewrite `{name}` so its complexity drops from "
            f"{score_txt} to {target} or less — same behavior, no timing "
            f"involved (AST-measured, tests stay green).\n"
            f"```python\n{code[:800]}\n```"
        ),
        "back": code,
        "payload": {"original": code, "score": score, "target": target,
                    "loops": loops, "tests": tests, "reference": code,
                    "func": name, "grounded": grounded},
    }


def _fail(feedback: str) -> dict:
    return {"pass": False, "score": 0.0, "feedback": feedback}


def grade(exercise: dict, submission: str, runner=None) -> dict:
    """Pass = parses, still defines the function, scores lower, tests green.

    Never raises: every malformed input maps to a failing grade dict.
    """
    try:
        p = (exercise or {}).get("payload", {})
        func = p.get("func") or (exercise or {}).get("concept", "")
        text = str(submission or "")
        if not text.strip():
            return _fail("Submit your rewritten function as Python code.")
        old = p.get("score")
        if old is None:
            old = complexity(p.get("original", ""))
        new = complexity(text)
        if new is None:
            return _fail("Submission does not parse — submit runnable Python.")
        if func and func not in _defined(text):
            return _fail(f"Your rewrite must still define `{func}` "
                         f"(a bare `pass` scores 0 but solves nothing).")
        if old is not None:
            target = p.get("target", max(0, old - 1))
            if new > target:
                return _fail(f"Complexity is {new}; it must be {target} or less "
                             f"(original {old}). Remove or flatten a loop and retry.")
        else:
            target = new
        tests = p.get("tests", "")
        if tests:
            if runner is None:
                return _fail("No sandbox available for grading.")
            res = runner.run(text + "\n" + tests)
            if res.ok and "FAIL" not in res.stdout:
                return {"pass": True, "score": 1.0,
                        "feedback": f"Simpler ({old} → {new}) and green."}
            return _fail(f"Complexity is down ({new}) but the tests fail: "
                         f"{res.stdout[:200]} {res.stderr[:200]}")
        return {"pass": True, "score": 1.0,
                "feedback": f"Complexity {old} → {new}, `{func}` intact."}
    except Exception as exc:  # noqa: BLE001 — grading never raises
        return _fail(f"Could not grade the submission: {exc}")


def render(exercise: dict) -> str:
    """Perf-fix card: metric line, original code, rewrite textarea, hints."""
    p = (exercise or {}).get("payload", {})
    front = html.escape(str(exercise.get("front", "")))
    original = html.escape(str(p.get("original", "")))
    concept = html.escape(str(exercise.get("concept", "")))
    type_name = html.escape(str(exercise.get("type_name", TYPE_NAME)))
    file_line = f"{exercise.get('file', '')}:{exercise.get('line', 0)}"
    metric = (f"<p><small>Complexity {p.get('score')} → "
              f"target {p.get('target')} or less (AST-measured: nesting + "
              f"loops; no timing).</small></p>")
    hints = "".join(
        f"<details><summary>Hint {i + 1}</summary>{html.escape(h)}</details>"
        for i, h in enumerate(exercise.get("hints", []))
    )
    return (
        f"<article><h3>{concept} · {type_name}</h3>"
        f"<p>{front}</p>{metric}<pre>{original}</pre>"
        f"<form method='post'><textarea name='answer' rows='12' "
        f"cols='70' placeholder='Paste your faster rewrite here'>"
        f"</textarea><br><button>Run tests</button></form>{hints}"
        f"<p><small>{html.escape(file_line)}</small></p></article>"
    )


def section_html() -> str:
    """Status-page home for this item (anchor status-b7-perffix)."""
    return ("<h3 id='status-b7-perffix'>Perf fix "
            "<small>(feature)</small></h3>"
            "<p>Rewrite a loop-heavy function so it scores lower — "
            "AST-measured (nesting + loops), tests stay green, no timing. "
            "<code>groundwork/perffix.py</code>.</p>")
