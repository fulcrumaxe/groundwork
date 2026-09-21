"""Feature-flag removal exercise (type 66, F-43, bloom: modify).

The learner cleans up a stale feature-flag branch: the flag name must
vanish everywhere (grep gate over the raw text — flags hide in
comments and string literals where tests stay green) AND the hidden
tests must stay green on the pruned code (reference-run via the
sandbox runner, deadcode pattern). The scenario is always built
deterministically: a snippet `if <FLAG>:` branch supplies the flag
name when present (found mode), otherwise a `FLAG_<hex>` name seeds
from ex_id (planted mode) — so the reference answer and harness are
exact in both modes.

``generate`` never returns None and never raises: thin input yields
an ungrounded fallback card the pipeline skips.

Plugin API: ``generate(ex_id, concept, snippet, ctx)``,
``render(exercise) -> html``, ``grade(exercise, submission, runner)``.
Import-safe standalone: stdlib only, no groundwork imports.
Registration lives in ``groundwork/exercises.py``
(TYPES, GENERATORS, BLOOM_TYPES, grade/render branches) and
``groundwork/pipeline.py`` (BLOOM_DEFAULT_TYPES); status section and
tour entry live below.
"""

from __future__ import annotations

import ast
import hashlib
import html
import re

TYPE_NUM = 66
TYPE_NAME = "flag-cut"
BLOOM = "modify"
STATUS_ANCHOR = "status-b11-flagcut"

_FLAG_RE = re.compile(r"if\s+([A-Z][A-Z0-9_]{2,})\s*:")


def _concept_field(concept, name: str, default: str = "") -> str:
    return str(getattr(concept, name, default) or default)


def _func_name(name: str) -> str:
    cleaned = re.sub(r"\W", "_", str(name or "")).strip("_") or "handle"
    if cleaned[0].isdigit():
        cleaned = "handle_" + cleaned
    return cleaned or "handle"


def _seed_flag(ex_id) -> str:
    try:
        digest = hashlib.sha256(str(ex_id).encode()).hexdigest()[:4]
        return "FLAG_" + digest.upper()
    except Exception:  # noqa: BLE001 — seeding must never raise
        return "FLAG_0000"


def _polarity(ex_id) -> bool:
    """Deterministic live-branch polarity: True means `if FLAG:` runs."""
    try:
        digest = hashlib.sha256(("pol|" + str(ex_id)).encode()).hexdigest()
        return int(digest[:2], 16) % 2 == 0
    except Exception:  # noqa: BLE001 — seeding must never raise
        return True


def _scenario(func: str, flag: str, live: bool) -> str:
    return (
        f"{flag} = {live}\n"
        f"\n"
        f"def {func}(x):\n"
        f"    if {flag}:\n"
        f"        out = x * 2\n"
        f"    else:\n"
        f"        out = x + 100\n"
        f"    return out\n"
    )


def _resolve(body: str, flag: str, live: bool) -> str:
    """Reference answer: drop the flag assignment, inline the live branch."""
    try:
        tree = ast.parse(body)
    except (SyntaxError, ValueError):
        return body
    lines = body.splitlines()
    drop: set = set()
    splice = None
    for node in ast.walk(tree):
        if (isinstance(node, ast.Assign) and len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name)
                and node.targets[0].id == flag):
            drop.update(range(node.lineno - 1, node.end_lineno))
        if (isinstance(node, ast.If)
                and isinstance(node.test, ast.Name)
                and node.test.id == flag and splice is None):
            taken = node.body if live else node.orelse
            if not taken:
                return body
            start = taken[0].lineno - 1
            end = taken[-1].end_lineno
            indent = len(lines[node.lineno - 1]) - len(
                lines[node.lineno - 1].lstrip())
            kept = [l[indent:] if l.strip() else l
                    for l in lines[start:end]]
            splice = (node.lineno - 1, node.end_lineno, kept)
    if splice is None:
        return body
    lo, hi, kept = splice
    out = []
    for i, l in enumerate(lines):
        if i == lo:
            out.extend(kept)
        if i in drop or (lo <= i < hi):
            continue
        out.append(l)
    rest = "\n".join(out).strip()
    return rest + "\n" if rest else ""


def _tests(func: str, live: bool) -> str:
    a, b = (6, 206) if live else (106, 306)
    return (f"assert {func}(3) == {a}\n"
            f"assert {func}(103) == {b}\n"
            "print('OK')")


def _hints(flag: str) -> list[str]:
    return [
        f"`{flag}` is stale — search the whole file, not just the `if` line.",
        "Keep the live branch's math exactly; delete only the flag and the dead side.",
        "Worked step: no `if`, no flag name anywhere, hidden asserts green.",
    ]


def generate(ex_id, concept, snippet, ctx):
    """Build a flag-cut card; never None, never raises."""
    try:
        ctx = ctx if isinstance(ctx, dict) else {}
        snippet = list(snippet or [])
        name = _concept_field(concept, "name", "")
        file = _concept_field(concept, "file", "") or "app.py"
        try:
            line = int(getattr(concept, "line", 0) or 0)
        except (TypeError, ValueError):
            line = 0
        commit = str(ctx.get("commit", "") or "")
        text = "\n".join(str(l) for l in snippet)
        found = _FLAG_RE.search(text)
        flag = found.group(1) if found else _seed_flag(ex_id)
        func = _func_name(name or "handle")
        live = _polarity(ex_id)
        original = _scenario(func, flag, live)
        reference = _resolve(original, flag, live)
        tests = _tests(func, live)
        grounded = bool(name or text.strip())
        front = (
            f"Cut the stale flag `{flag}` in `{func}`: remove every "
            "reference to the flag name and resolve both branches so "
            "only live behavior remains. The hidden tests must stay green.\n"
            f"```python\n{original}```"
        )
        return {
            "id": ex_id, "type": TYPE_NUM, "type_name": TYPE_NAME,
            "bloom": BLOOM,
            "concept_id": _concept_field(concept, "node_id", func),
            "concept": name or func, "file": file, "line": line,
            "commit": commit,
            "hints": _hints(flag),
            "front": front, "back": reference,
            "payload": {"flag": flag, "func": func, "original": original,
                        "reference": reference, "tests": tests,
                        "seeded": found is None, "grounded": grounded},
        }
    except Exception:
        return {  # generate never raises and never returns None
            "id": ex_id, "type": TYPE_NUM, "type_name": TYPE_NAME,
            "bloom": BLOOM, "concept_id": "handle", "concept": "handle",
            "file": "app.py", "line": 0, "commit": "",
            "hints": _hints("FLAG_0000"),
            "front": "Cut the stale flag `FLAG_0000`: remove every "
                     "reference and resolve both branches.",
            "back": "def handle(x):\n    out = x * 2\n    return out\n",
            "payload": {"flag": "FLAG_0000", "func": "handle",
                        "original": "", "reference": "",
                        "tests": "", "seeded": True, "grounded": False},
        }


def _fail(msg: str) -> dict:
    return {"pass": False, "score": 0.0, "feedback": msg}


def grade(exercise: dict, submission: str, runner=None) -> dict:
    """Grep gate plus reference-run: flag gone, behavior kept."""
    try:
        return _grade(exercise, submission, runner)
    except Exception as exc:  # noqa: BLE001 — grading never raises
        return _fail(f"Grader hiccup ({exc}) — resubmit.")


def _grade(exercise: dict, submission: str, runner=None) -> dict:
    p = (exercise or {}).get("payload", {}) or {}
    flag = str(p.get("flag", "") or "")
    func = str(p.get("func", "") or "")
    text = str(submission if submission is not None else "")
    if not text.strip():
        return _fail("Submit the cleaned module — flag removed, branches resolved.")
    try:
        tree = ast.parse(text)
    except (SyntaxError, ValueError):
        return _fail("Submission does not parse — resubmit valid Python.")
    if func and func not in {
            n.name for n in ast.walk(tree)
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}:
        return _fail(f"`{func}` must stay — only cut the flag.")
    if not flag:
        return _fail("No flag recorded on this card.")
    if re.search(r"\b" + re.escape(flag) + r"\b", text):
        return _fail(f"`{flag}` still appears — the flag must vanish "
                      "everywhere, comments and strings included.")
    tests = str(p.get("tests", "") or "")
    if not tests:
        return _fail("No harness recorded on this card.")
    if runner is None:
        return _fail("No sandbox available for grading.")
    res = runner.run(text + "\n" + tests)
    if bool(res.ok) and "FAIL" not in str(res.stdout):
        return {"pass": True, "score": 1.0,
                "feedback": f"Flag `{flag}` gone and remaining tests stay green."}
    return {"pass": False, "score": 0.0,
            "feedback": f"Flag gone, but behavior drifted: "
                        f"{str(res.stdout)[:300]} {str(res.stderr)[:300]}".strip()}


def render(exercise: dict) -> str:
    """Exercise widget: flag-cut spec plus disclosed gates and textarea."""
    front = html.escape(str(exercise.get("front", "")))
    concept = html.escape(str(exercise.get("concept", "")))
    type_name = html.escape(str(exercise.get("type_name", TYPE_NAME)))
    file_line = f"{exercise.get('file', '')}:{exercise.get('line', 0)}"
    hints = "".join(
        f"<details><summary>Hint {i + 1}</summary>{html.escape(h)}</details>"
        for i, h in enumerate(exercise.get("hints", [])))
    return (
        f"<article><h3>{concept} · {type_name}</h3>"
        f"<p>{front}</p>"
        f"<details><summary>How grading works</summary>"
        f"<p><small>Two gates, no partial credit. The flag name must not "
        f"appear anywhere (comments and strings included); the hidden "
        f"tests must stay green.</small></p></details>"
        f"<form method='post'><textarea name='answer' rows='12' cols='70' "
        f"placeholder='def handle(x):'>"
        f"</textarea><br><button>Cut the flag</button></form>{hints}"
        f"<p><small>{html.escape(file_line)}</small></p></article>")


def section_html() -> str:
    """Anchored status subsection; wired into the status page by the parent."""
    return (
        f"<h3 id='{STATUS_ANCHOR}'>Cut the stale flag <small>(feature)</small></h3>"
        "<p>Remove a dead feature-flag branch so no reference to the flag "
        "name remains and the hidden tests stay green — static grep gate "
        "plus sandbox run, no partial credit. "
        "<code>groundwork/flagcut.py</code>.</p>"
    )


def tour_entry() -> dict:
    """Feature-tour registry entry (appended to tour.ENTRIES by parent)."""
    return {"id": "flag-cut", "kind": "feature",
            "title": "Cut the stale flag",
            "blurb": "Remove a dead feature-flag branch — grep gate plus green hidden tests.",
            "path": "/status", "anchor": "status-b11-flagcut"}
