"""API guessing drills (type 81, F-77, bloom: apply).

Predict-the-call then check-docs: the learner gets a one-sentence task
plus snippet context, predicts which stdlib call fits (single choice of
four), commits, then checks the back: the true call's synopsis plus a
pointer to the official docs section (`library/<mod>`).

The true answer is derived from the snippet itself — the module
AST-scans for `X.y(...)` / `y(...)` calls matching a small curated
stdlib map; the first mapped call in source order is the target.
Distractors are sibling mapped calls, backfilled from a static pool.
Grading is normalized exact-choice match (same contract as types
7/16/18/80), so no sandbox runner is needed.

``generate`` never returns None and never raises: thin input (no
mapped call) yields an ungrounded card the pipeline skips.

Plugin API: ``generate(ex_id, concept, snippet, ctx)``,
``render(exercise) -> html``, ``grade(exercise, submission, runner)``.
Import-safe standalone: stdlib only, no groundwork imports.
Registration lives in ``groundwork/exercises.py``
(TYPES, GENERATORS, BLOOM_TYPES, grade/render branches),
``groundwork/grading.py`` (disclosure 81),
``groundwork/pipeline.py`` (BLOOM_DEFAULT_TYPES) and
``groundwork/__main__.py`` (cmd_e2e fixture); status section and
tour entry live below.
"""
from __future__ import annotations

import ast
import hashlib
import html

TYPE_NUM = 81
TYPE_NAME = "api-guess"
BLOOM = "apply"
STATUS_ANCHOR = "status-b19-apiguess"

# Curated stdlib map v1: dotted call -> (module, synopsis, docs anchor).
# Third-party calls are out of scope (no site-packages import graph).
CALLS = {
    "json.loads": ("json", "Parse a JSON string into Python objects.",
                   "library/json"),
    "os.path.join": ("os.path", "Join path parts with the OS separator.",
                     "library/os.path"),
    "re.search": ("re", "Scan a string for the first regex match.",
                  "library/re"),
    "collections.Counter": ("collections", "Count hashable items in order.",
                            "library/collections"),
    "itertools.groupby": ("itertools", "Group consecutive equal items.",
                          "library/itertools"),
    "pathlib.Path": ("pathlib", "An object-oriented filesystem path.",
                     "library/pathlib"),
    "datetime.fromisoformat": ("datetime", "Parse an ISO-8601 date string.",
                               "library/datetime"),
    "urllib.parse.urlparse": ("urllib.parse", "Split a URL into components.",
                              "library/urllib.parse"),
}

_POOL = (
    "Open a file and read its lines into a list.",
    "Sort values in place and return nothing.",
    "Sleep the current thread for some seconds.",
    "Shuffle a list into random order.",
)


def _concept_field(concept, name: str, default: str = "") -> str:
    return str(getattr(concept, name, default) or default)


def _mapped_calls(code: str) -> list[str]:
    """Mapped dotted calls in source order; never raises."""
    out: list[str] = []
    try:
        tree = ast.parse(code)
    except (SyntaxError, ValueError):
        return out
    try:
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            if isinstance(func, ast.Attribute):
                parts = []
                cur = func
                while isinstance(cur, ast.Attribute):
                    parts.append(cur.attr)
                    cur = cur.value
                if isinstance(cur, ast.Name):
                    parts.append(cur.id)
                    dotted = ".".join(reversed(parts))
                    if dotted in CALLS and dotted not in out:
                        out.append(dotted)
            elif isinstance(func, ast.Name):
                if func.id in CALLS and func.id not in out:
                    out.append(func.id)
    except Exception:  # noqa: BLE001 -- scanning never raises
        return out
    return out


def _rot(ex_id) -> int:
    try:
        return int(hashlib.sha256(str(ex_id).encode()).hexdigest(), 16)
    except Exception:  # noqa: BLE001 -- seeding must never raise
        return 0


def _choices(truth: str, others: list[str], ex_id) -> tuple[list[str], str]:
    """Four calls, true one rotated by ex_id; (choices, answer)."""
    seen: list[str] = []
    for cand in list(others) + list(_POOL):
        if cand != truth and cand not in seen:
            seen.append(cand)
        if len(seen) == 3:
            break
    while len(seen) < 3:  # pool is fixed; this only guards tiny edits
        seen.append(f"Helper #{len(seen) + 1} for internal bookkeeping.")
    opts = seen + [truth]
    k = _rot(ex_id) % 4
    opts = opts[k:] + opts[:k]
    return opts, truth


def _hints() -> list[str]:
    return [
        "Name the data transformation first, then match a call to it.",
        "The back names the true call plus its docs section — verify there.",
        "Commit before you peek: prediction is the drill.",
    ]


def _task_for(target: str) -> str:
    mod, synopsis, _docs = CALLS[target]
    return f"{synopsis} Which stdlib call fits?"


def generate(ex_id, concept, snippet, ctx):
    """Build an API-guess card; never None, never raises."""
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
        targets = _mapped_calls("\n".join(str(l) for l in snippet))
        if not targets:
            return _ungrounded(ex_id, name, file, line, commit)
        target = targets[_rot(ex_id) % len(targets)]
        mod, synopsis, docs = CALLS[target]
        others = [t for t in targets if t != target]
        choices, answer = _choices(target, others, ex_id)
        return {
            "id": ex_id, "type": TYPE_NUM, "type_name": TYPE_NAME,
            "bloom": BLOOM,
            "concept_id": _concept_field(concept, "node_id", "apiguess"),
            "concept": name or target, "file": file, "line": line,
            "commit": commit,
            "hints": _hints(),
            "front": (f"Task: {_task_for(target)} Commit to one call, "
                      "then verify against the synopsis and docs pointer."),
            "back": f"{target}: {synopsis} ({docs})",
            "payload": {"target": target, "module": mod,
                        "choices": choices, "answer": answer,
                        "synopsis": synopsis, "docs": docs,
                        "grounded": True},
        }
    except Exception:
        return _ungrounded(ex_id, "", "app.py", 0, "")


def _ungrounded(ex_id, name, file, line, commit) -> dict:
    return {
        "id": ex_id, "type": TYPE_NUM, "type_name": TYPE_NAME,
        "bloom": BLOOM, "concept_id": "apiguess",
        "concept": name or "apiguess", "file": file, "line": line,
        "commit": commit, "hints": _hints(),
        "front": "Which stdlib call fits this task? (No mapped call found.)",
        "back": "No mapped stdlib call in scope — skipped by the pipeline.",
        "payload": {"target": "", "module": "", "choices": [],
                    "answer": "", "synopsis": "", "docs": "",
                    "grounded": False},
    }


def _fail(msg: str) -> dict:
    return {"pass": False, "score": 0.0, "feedback": msg}


def grade(exercise: dict, submission: str, runner=None) -> dict:
    """Normalized exact-choice match; the synopsis + docs are the verify."""
    _ = runner
    try:
        return _grade(exercise, submission)
    except Exception as exc:  # noqa: BLE001 -- grading never raises
        return _fail(f"Grader hiccup ({exc}) — resubmit.")


def _norm(text: str) -> str:
    return " ".join(str(text or "").strip().split()).rstrip(".").lower()


def _grade(exercise: dict, submission: str) -> dict:
    p = (exercise or {}).get("payload", {}) or {}
    want = _norm(p.get("answer", ""))
    text = str(submission if submission is not None else "")
    if not text.strip():
        return _fail("Commit to a call first — then check the synopsis.")
    if not want:
        return _fail("No call recorded on this card.")
    if _norm(text) == want:
        return {"pass": True, "score": 1.0,
                "feedback": "Right call — docs confirm it."}
    return {"pass": False, "score": 0.0,
            "feedback": f"That call misleads — the fit is: {p.get('answer', '')} ({p.get('docs', '')})"}


def render(exercise: dict) -> str:
    """Exercise widget: task, four call choices, commit button."""
    p = (exercise or {}).get("payload", {}) or {}
    front = html.escape(str(exercise.get("front", "")))
    type_name = html.escape(str(exercise.get("type_name", TYPE_NAME)))
    file_line = f"{exercise.get('file', '')}:{exercise.get('line', 0)}"
    opts = "".join(
        f"<label><input type='radio' name='answer' value='{html.escape(c)}'> "
        f"<code>{html.escape(c)}</code></label><br>"
        for c in p.get("choices", []))
    hints = "".join(
        f"<details><summary>Hint {i + 1}</summary>{html.escape(h)}</details>"
        for i, h in enumerate(exercise.get("hints", [])))
    return (
        f"<article><h3>{type_name}</h3>"
        f"<p>{front}</p>"
        f"<details><summary>How grading works</summary>"
        f"<p><small>Predict the call — exact choice wins; the synopsis "
        f"and docs pointer on the back are the verify step.</small></p>"
        f"</details>"
        f"<form method='post'>{opts}<button>Commit prediction</button></form>"
        f"{hints}<p><small>{html.escape(file_line)}</small></p></article>")


def section_html() -> str:
    """Anchored status subsection; wired into the status page by the parent."""
    return (
        f"<h3 id='{STATUS_ANCHOR}'>API guessing <small>(feature)</small></h3>"
        "<p>Predict the stdlib call for a task from four choices, then verify "
        "against the recorded synopsis and docs pointer — exact-choice "
        "grading, no sandbox. <code>groundwork/apiguess.py</code>.</p>"
    )


def tour_entry() -> dict:
    """Feature-tour registry entry (appended to tour.ENTRIES by parent)."""
    return {"id": "api-guess", "kind": "feature",
            "title": "API guessing",
            "blurb": "Predict which stdlib call fits the task, then check the docs synopsis — commit before you verify.",
            "path": "/due", "anchor": "up-next"}
