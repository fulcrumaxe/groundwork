"""Dead-code elimination exercises (type 38, F-15, modify).

The learner removes one flagged dead node — an unused import, a
never-called function, or a constant-false branch — so the remaining
hidden tests stay green (coverage-kept-green). Grading AST-checks the
dead node is gone AND runs the harness via the sandbox runner.

Detection is heuristic and honest: when the snippet holds no real dead
node, generate seeds a never-called helper (payload ``seeded`` says
so) — the removal is still real and harness-verified. ``grounded``
follows the sibling rewrite types: true only when a harness exists.

Plugin API: ``generate(ex_id, concept, snippet, ctx)``,
``render(exercise) -> html``, ``grade(exercise, submission, runner)``.
Import-safe standalone: stdlib only (``ast``/``html``), no groundwork
imports. Registration lives in ``groundwork/exercises.py``
(TYPES, GENERATORS, BLOOM_TYPES); see ===WIRES===.
"""
from __future__ import annotations

import ast
import html

TYPE_NUM = 38
TYPE_NAME = "dead-code"
BLOOM = "modify"

GUARD = "tests"

_SEED_NAME = "_unused_helper"


def _concept_field(concept, name: str, default: str = "") -> str:
    return str(getattr(concept, name, default) or default)


def emits(ctx) -> bool:
    """Emission guard predicate: needs the assert-only harness (like 26/27)."""
    return GUARD in (ctx or {})


def _imports(tree: ast.AST) -> set[str]:
    """Top names bound by any import statement."""
    out = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                out.add((a.asname or a.name).split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            for a in node.names:
                if a.name != "*":
                    out.add(a.asname or a.name)
    return out


def _unused_imports(tree: ast.AST) -> list[str]:
    used = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
    return sorted(n for n in _imports(tree) if n not in used)


def _method_names(tree: ast.AST) -> set[str]:
    """Defs inside a class body — called via attribute, never bare names."""
    out = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            for n in ast.walk(node):
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    out.add(n.name)
    return out


def _uncalled_defs(tree: ast.AST, keep: str) -> list[str]:
    """Defined-but-never-called functions, minus the concept entry point."""
    methods = _method_names(tree)
    called = {n.func.id for n in ast.walk(tree)
              if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
    found = set()
    for n in ast.walk(tree):
        if not isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if n.name == keep or n.name in methods or n.name in called:
            continue
        if n.name.startswith("__"):
            continue
        found.add(n.name)
    return sorted(found)


def _dead_branches(tree: ast.AST) -> list[str]:
    """Labels for branches that can never run (constant tests only)."""
    out = []
    for node in ast.walk(tree):
        if isinstance(node, ast.If) and isinstance(node.test, ast.Constant):
            if node.test.value is False and "if False" not in out:
                out.append("if False")
            elif (node.test.value is True and node.orelse
                    and "else after if True" not in out):
                out.append("else after if True")
        elif isinstance(node, ast.While) and isinstance(node.test, ast.Constant):
            if node.test.value is False and "while False" not in out:
                out.append("while False")
    return out


def _find_dead(body: str, keep: str) -> tuple[str, str]:
    """(kind, target): 'import' | 'function' | 'branch' plus flagged name."""
    try:
        tree = ast.parse(body)
    except (SyntaxError, ValueError):
        return ("function", _SEED_NAME)
    for name in _unused_imports(tree):
        if name != keep:
            return ("import", name)
    funcs = _uncalled_defs(tree, keep)
    if funcs:
        return ("function", funcs[0])
    branches = _dead_branches(tree)
    if branches:
        return ("branch", branches[0])
    return ("function", _SEED_NAME)


def _seed_dead(body: str) -> str:
    """Append a genuinely never-called helper; unchanged if it won't parse."""
    candidate = body.rstrip() + f"\n\n\ndef {_SEED_NAME}():\n    return None\n"
    try:
        ast.parse(candidate)
    except (SyntaxError, ValueError):
        return body
    return candidate


def _remove_dead(body: str, kind: str, target: str) -> str:
    """Best-effort model answer: drop the flagged def/import (branch: as-is)."""
    try:
        tree = ast.parse(body)
    except (SyntaxError, ValueError):
        return body
    lines = body.splitlines()
    if kind == "function":
        for node in ast.walk(tree):
            if (isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                    and node.name == target):
                del lines[node.lineno - 1:node.end_lineno]
                rest = "\n".join(lines).strip()
                return rest + "\n" if rest else ""
    if kind == "import":
        for node in ast.walk(tree):
            names: list[str] = []
            if isinstance(node, ast.Import) and len(node.names) == 1:
                a = node.names[0]
                names = [(a.asname or a.name).split(".")[0]]
            elif isinstance(node, ast.ImportFrom) and len(node.names) == 1:
                a = node.names[0]
                names = [a.asname or a.name]
            if names == [target]:
                del lines[node.lineno - 1:node.end_lineno]
                rest = "\n".join(lines).strip()
                return rest + "\n" if rest else ""
    return body


def _task_text(kind: str, target: str, func: str) -> str:
    if kind == "import":
        return (f"Remove the unused import `{target}` from `{func}`'s module. "
                "Everything else must stay — the hidden tests must keep passing.")
    if kind == "branch":
        return (f"Cut the dead branch `{target}` in `{func}` — it can never run. "
                "Everything else must stay — the hidden tests must keep passing.")
    return (f"Delete the never-called helper `{target}` — nothing uses it. "
            f"`{func}` and everything else must stay, "
            "and the hidden tests must keep passing.")


def generate(ex_id, concept, snippet, ctx) -> dict:
    """Build the type-38 exercise dict (engine shape, standalone)."""
    ctx = ctx or {}
    snippet = list(snippet or [])
    keep = _concept_field(concept, "name", "func") or "func"
    body = str(ctx.get("runnable") or "\n".join(snippet)
               or f"def {keep}():\n    return None")
    kind, target = _find_dead(body, keep)
    seeded = False
    if target == _SEED_NAME and ("def " + _SEED_NAME) not in body:
        new_body = _seed_dead(body)
        if ("def " + _SEED_NAME) in new_body:
            body, seeded = new_body, True
    tests = str(ctx.get("tests", "") or "")
    reference = _remove_dead(body, kind, target)
    name = keep
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
        "hints": [
            f"`{target}` never runs — search the snippet for its uses.",
            "Delete only the dead node; do not reword or move live code.",
            f"Worked step: remove `{target}`, then the hidden tests still pass.",
        ],
        "front": f"{_task_text(kind, target, keep)}\n```python\n{body[:600]}\n```",
        "back": reference,
        "payload": {"kind": kind, "target": target, "func": keep,
                    "original": body, "reference": reference,
                    "tests": tests, "seeded": seeded,
                    "grounded": bool(tests)},
    }


def _fail(msg: str) -> dict:
    return {"pass": False, "score": 0.0, "feedback": msg}


def _dead_present(tree: ast.AST, kind: str, target: str) -> bool:
    if kind == "import":
        return target in _imports(tree)
    if kind == "branch":
        return target in _dead_branches(tree)
    return any(isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
               and n.name == target for n in ast.walk(tree))


def grade(exercise: dict, submission: str, runner=None) -> dict:
    """AST-check the dead node is gone, then keep the harness green."""
    try:
        return _grade(exercise, submission, runner)
    except Exception as exc:  # noqa: BLE001 — grading never raises
        return _fail(f"Grader hiccup ({exc}) — resubmit.")


def _grade(exercise: dict, submission: str, runner=None) -> dict:
    p = (exercise or {}).get("payload", {})
    kind = str(p.get("kind", "function") or "function")
    target = str(p.get("target", "") or "")
    func = str(p.get("func", "") or "")
    text = str(submission or "")
    if not text.strip():
        return _fail("Submit the pruned module — dead node removed, rest intact.")
    try:
        tree = ast.parse(text)
    except (SyntaxError, ValueError):
        return _fail("Submission does not parse — resubmit valid Python.")
    if func and func not in {
            n.name for n in ast.walk(tree)
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}:
        return _fail(f"`{func}` must stay — only remove the dead `{target or 'node'}`.")
    if not target:
        return _fail("No dead node recorded on this card.")
    if _dead_present(tree, kind, target):
        if kind == "import":
            return _fail(f"Still imports `{target}` — delete the unused import.")
        if kind == "branch":
            return _fail(f"Dead branch `{target}` is still there — cut it.")
        return _fail(f"`{target}` is still defined — delete it; nothing calls it.")
    tests = str(p.get("tests", "") or "")
    if not tests:
        return {"pass": True, "score": 1.0,
                "feedback": f"Pruned `{target}` (no harness on this card)."}
    if runner is None:
        return _fail("No sandbox available for grading.")
    res = runner.run(text + "\n" + tests)
    if bool(res.ok) and "FAIL" not in str(res.stdout):
        return {"pass": True, "score": 1.0,
                "feedback": f"Dead `{target}` gone and remaining tests stay green."}
    return {"pass": False, "score": 0.0,
            "feedback": f"Pruned, but remaining tests broke: "
                        f"{str(res.stdout)[:300]} {str(res.stderr)[:300]}".strip()}


def render(exercise: dict) -> str:
    """Exercise card HTML (mirrors exercises.render article wrapper)."""
    p = (exercise or {}).get("payload", {})
    front = html.escape(str(exercise.get("front", "")))
    concept = html.escape(str(exercise.get("concept", "")))
    type_name = html.escape(str(exercise.get("type_name", TYPE_NAME)))
    seed = html.escape(str(p.get("original", "")))
    hints = "".join(
        f"<details><summary>Hint {i + 1}</summary>{html.escape(h)}</details>"
        for i, h in enumerate(exercise.get("hints", []))
    )
    return (
        f"<article><h3>{concept} · {type_name}</h3>"
        f"<p>{front}</p>"
        f"<details><summary>How grading works</summary>"
        f"<p><small>The flagged dead code must be gone and the "
        f"hidden tests must stay green.</small></p></details>"
        f"<form method='post'><textarea name='answer' rows='12' cols='70'>{seed}</textarea>"
        f"<br><button>Run tests</button></form>{hints}"
        f"<p><small>{html.escape(str(exercise.get('file', '')))}:"
        f"{exercise.get('line', 0)}</small></p></article>"
    )


def section_html() -> str:
    """Status-page home for this item (anchor status-b7-deadcode)."""
    return ("<h3 id='status-b7-deadcode'>Dead-code elimination "
            "<small>(feature)</small></h3>"
            "<p>Remove the flagged unused function, branch, or import — "
            "AST-checked, and the remaining tests must stay green. "
            "<code>groundwork/deadcode.py</code>.</p>")


def tour_entry() -> dict:
    """Feature-tour registry entry (appended to tour.ENTRIES by parent)."""
    return {"id": "deadcode-type", "kind": "feature",
            "title": "Dead-code elimination",
            "blurb": "Cut the flagged dead function, branch, or import — "
                     "remaining tests stay green.",
            "path": "/status", "anchor": "status-b7-deadcode"}
