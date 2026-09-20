"""Rebase-conflict resolution exercise (type 46, F-23, bloom: modify).

The learner resolves a planted git-conflict block (``<<<<<<<`` /
``=======`` / ``>>>>>>>``) inside a function derived from the snippet:
keep both sides' lines, drop the markers, reply with the full
function. Grading is a deterministic static check — markers gone,
both sides kept, same-name def present, parses — with partial credit
and no sandbox. Stdlib only (``ast``/``html``/``re``), import-safe
standalone: no groundwork imports.

Plugin API: ``generate(ex_id, concept, snippet, ctx)``,
``render(exercise) -> html``, ``grade(exercise, submission, runner)``.
Registration lives in ``groundwork/exercises.py``
(TYPES, GENERATORS, BLOOM_TYPES).
"""
from __future__ import annotations

import ast
import html
import re

TYPE_NUM = 46
TYPE_NAME = "rebase-resolve"
BLOOM = "modify"

_FALLBACK_BODY = "def {func}():\n    x = 1\n    return x"

# Deterministic token swaps, first hit wins (applied leftmost-once).
_SWAPS = (("==", "!="), ("+=", "-="), ("-=", "+="), ("+", "-"),
          ("-", "+"), ("*", "+"), ("True", "False"), ("False", "True"))
_DIGIT_RE = re.compile(r"\b0\b")
_MARKERS = ("<<<<<<<", "=======", ">>>>>>>")


def _concept_field(concept, name: str, default: str = "") -> str:
    return str(getattr(concept, name, default) or default)


def _slug(name: str) -> str:
    return re.sub(r"\W+", "_", name.strip()).strip("_") or "func"


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


def _fn_lines(code: str, fn) -> list[str]:
    """Source lines spanning the def, via lineno/end_lineno."""
    lines = code.splitlines()
    try:
        start = max(0, (fn.lineno or 1) - 1)
        end = max(start + 1, fn.end_lineno or start + 1)
    except (AttributeError, TypeError):
        return lines
    return lines[start:end]


def _variant(line: str) -> str:
    """A deterministic same-shape-but-different line; never equal input."""
    for old, new in _SWAPS:
        if old in line:
            out = line.replace(old, new, 1)
            if out != line:
                return out
    if _DIGIT_RE.search(line):
        return _DIGIT_RE.sub("1", line, count=1)
    try:
        if ast.parse(line).body and isinstance(ast.parse(line).body[0], ast.Expr):
            return line + " or 0"
    except (SyntaxError, ValueError):
        pass
    return line + "  # theirs"


def _pick_target(lines: list[str]) -> int:
    """Body-line index for the conflict: middle-out, skipping continuations.

    Never the def line (index 0); skips lines ending in a backslash
    (a comment fallback there would not parse). Deterministic.
    """
    n = len(lines)
    if n < 2:
        return -1
    order = [min(1 + (n // 2), n - 1)]
    order += [i for i in range(1, n) if i not in order]
    for i in order:
        if not lines[i].rstrip().endswith("\\"):
            return i
    return -1


def _plant(fn_lines: list[str]) -> tuple[str, str, str, str]:
    """(conflicted, ours_line, theirs_line, reference) for fn lines."""
    idx = _pick_target(fn_lines)
    head = fn_lines[:1]
    if idx < 0:
        return "", "", "", ""
    pre, ours = fn_lines[1:idx], fn_lines[idx]
    theirs = _variant(ours)
    post = fn_lines[idx + 1:]
    conflicted = "\n".join(
        head + pre + ["<<<<<<< ours", ours, "=======", theirs,
                      ">>>>>>> theirs"] + post)
    reference = "\n".join(head + pre + [ours, theirs] + post)
    return conflicted, ours, theirs, reference


def generate(ex_id, concept, snippet, ctx) -> dict:
    """Build a rebase-resolve card: planted conflict in the concept's fn."""
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
    if fn is None:
        func = _slug(name)
        fn_lines = _FALLBACK_BODY.format(func=func).splitlines()
        fn = _find_fn("\n".join(fn_lines), func)
    else:
        func = fn.name
        fn_lines = _fn_lines(code, fn)
        if len(fn_lines) < 2:
            # One-line def: nothing to split — synthesize a plantable body.
            fn_lines = _FALLBACK_BODY.format(func=_slug(func)).splitlines()
            fn = _find_fn("\n".join(fn_lines), _slug(func))
            func = fn.name if fn is not None else _slug(func)
    conflicted, ours, theirs, reference = _plant(fn_lines)
    if not conflicted:
        fn_lines = _FALLBACK_BODY.format(func=_slug(func)).splitlines()
        conflicted, ours, theirs, reference = _plant(fn_lines)
    front = (
        f"Resolve the rebase conflict in `{func}` ({kind}"
        f"{f' in {file}' if file else ''}): keep BOTH sides' lines, "
        f"drop the conflict markers, and reply with the full function.\n"
        f"```python\n{conflicted}\n```")
    back = reference + "  (model answer — markers gone, both sides kept)."
    hints = [
        "Delete the `<<<<<<<`, `=======`, and `>>>>>>>` lines entirely.",
        "Keep every code line from BOTH sides — neither side wins outright.",
        "Reply with the whole function, starting at its `def` line.",
    ]
    return {
        "id": ex_id, "type": TYPE_NUM, "type_name": TYPE_NAME, "bloom": BLOOM,
        "concept_id": _concept_field(concept, "node_id", name),
        "concept": name, "file": file, "line": line, "commit": commit,
        "hints": hints, "front": front, "back": back,
        "payload": {"func": func, "ours": [ours], "theirs": [theirs],
                    "conflicted": conflicted, "reference": reference,
                    "grounded": True},
    }


def _fail(msg: str) -> dict:
    return {"pass": False, "score": 0.0, "feedback": msg}


def _norm(line: str) -> str:
    return " ".join(str(line or "").split())


def _has_markers(text: str) -> bool:
    return any(l.lstrip().startswith(m) for m in _MARKERS
               for l in text.splitlines())


def grade(exercise: dict, submission: str, runner=None) -> dict:
    """Static merge check: markers gone, both sides kept, parses.

    Points: markers gone (1) + parses (1) + same-name def (1) + each
    side-unique line present, whitespace-normalized (1 each). Pass
    needs every point; partial credit recorded. ``runner`` is accepted
    for API symmetry and ignored. Never raises.
    """
    _ = runner
    try:
        payload = (exercise or {}).get("payload", {}) or {}
        func = str(payload.get("func", "") or "")
        ours = [_norm(l) for l in payload.get("ours", []) if _norm(l)]
        theirs = [_norm(l) for l in payload.get("theirs", []) if _norm(l)]
        text = str(submission or "").strip()
        if not text:
            return _fail("Submit the resolved function.")
        missing = []
        if _has_markers(text):
            missing.append("remove the <<<<<<<, =======, and >>>>>>> lines")
        try:
            ast.parse(text)
            parses = True
        except (SyntaxError, ValueError):
            parses = False
        if not parses:
            missing.append("the resolved code does not parse")
        if not (func and re.search(r"\bdef\s+" + re.escape(func) + r"\b", text)):
            missing.append(f"keep the `def {func or '...'}' header")
        have = {_norm(l) for l in text.splitlines() if _norm(l)}
        only_ours = [l for l in ours if l not in theirs]
        only_theirs = [l for l in theirs if l not in ours]
        dropped = [l for l in only_ours + only_theirs if l not in have]
        missing.extend(f"keep the line `{l}`" for l in dropped)
        total = 3 + len(only_ours) + len(only_theirs)
        earned = total - len(missing)
        score = earned / max(1, total)
        detail = f"{earned}/{total} rubric points."
        if not missing:
            return {"pass": True, "score": 1.0,
                    "feedback": f"Conflict resolved. {detail}"}
        return {"pass": False, "score": score,
                "feedback": f"Not yet. {detail} Fix: {'; '.join(missing)[:200]}."}
    except Exception:  # noqa: BLE001 — grading must never raise
        return _fail("Grader could not read the submission — submit the resolved function.")


def render(exercise: dict) -> str:
    """Exercise widget: conflicted block plus a seeded textarea."""
    payload = (exercise or {}).get("payload", {}) or {}
    front = html.escape(str(exercise.get("front", "")))
    concept = html.escape(str(exercise.get("concept", "")))
    type_name = html.escape(str(exercise.get("type_name", TYPE_NAME)))
    conflicted = html.escape(str(payload.get("conflicted", "")))
    file_line = f"{exercise.get('file', '')}:{exercise.get('line', 0)}"
    hints = "".join(
        f"<details><summary>Hint {i + 1}</summary>{html.escape(h)}</details>"
        for i, h in enumerate(exercise.get("hints", [])))
    return (
        f"<article><h3>{concept} · {type_name}</h3>"
        f"<p>{front}</p>"
        f"<pre>{conflicted}</pre>"
        f"<details><summary>How grading works</summary>"
        f"<p><small>No conflict markers remain, every kept line from both "
        f"sides is present, and the code parses — checked statically, no "
        f"sandbox. Partial credit per rubric point.</small></p></details>"
        f"<form method='post'><textarea name='answer' rows='8' cols='70'>{conflicted}</textarea>"
        f"<br><button>Check resolution</button></form>{hints}"
        f"<p><small>{html.escape(file_line)}</small></p></article>")


def section_html() -> str:
    """Anchored status subsection; wired into the status page by the parent."""
    return (
        "<h3 id='status-b8-rebase'>Rebase-conflict resolution <small>(feature)</small></h3>"
        "<p>Resolve a planted git-conflict block inside a function, keeping "
        "both sides' lines — graded statically (markers gone, both sides "
        "kept, parses), no sandbox. "
        "<code>groundwork/rebase.py</code>.</p>"
    )


def tour_entry() -> dict:
    """Feature-tour registry entry (appended to tour.ENTRIES by parent)."""
    return {"id": "rebase-type", "kind": "feature",
            "title": "Rebase-conflict resolution",
            "blurb": "Resolve a planted git-conflict block keeping both sides; static check stays green.",
            "path": "/status", "anchor": "status-b8-rebase"}
