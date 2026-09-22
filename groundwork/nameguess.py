"""Naming-fluency drills (type 80, F-76, bloom: understand).

Purpose-from-name prediction then verify: the learner sees one real
identifier plus its signature, predicts what it does from the name
alone (single choice of four), then verifies against the recorded
docstring on the back. The true purpose is the target function's own
docstring first line; distractors are sibling docstrings from the same
snippet, backfilled from a static generic pool. Grading is normalized
exact-choice match — the same contract as types 7/16/18 — so no
sandbox runner is needed.

``generate`` never returns None and never raises: thin input (no
documented def) yields an ungrounded card the pipeline skips.

Plugin API: ``generate(ex_id, concept, snippet, ctx)``,
``render(exercise) -> html``, ``grade(exercise, submission, runner)``.
Import-safe standalone: stdlib only, no groundwork imports.
Registration lives in ``groundwork/exercises.py``
(TYPES, GENERATORS, BLOOM_TYPES, grade/render branches),
``groundwork/grading.py`` (disclosure 80),
``groundwork/pipeline.py`` (BLOOM_DEFAULT_TYPES) and
``groundwork/__main__.py`` (cmd_e2e fixture); status section and
tour entry live below.
"""
from __future__ import annotations

import ast
import hashlib
import html

TYPE_NUM = 80
TYPE_NAME = "naming-fluency"
BLOOM = "understand"
STATUS_ANCHOR = "status-b18-nameguess"

_POOL = (
    "Parses command-line arguments into options.",
    "Opens a database connection and returns a handle.",
    "Renders an HTML page from a template and context.",
    "Sends an email notification to the configured address.",
    "Validates user input and returns cleaned values.",
    "Writes buffered records to disk and fsyncs.",
)


def _concept_field(concept, name: str, default: str = "") -> str:
    return str(getattr(concept, name, default) or default)


def _doc_targets(code: str) -> list[tuple[str, str, str]]:
    """(name, signature, purpose) for documented defs, source order."""
    out: list[tuple[str, str, str]] = []
    try:
        tree = ast.parse(code)
    except (SyntaxError, ValueError):
        return out
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if node.name.startswith("_") and node.name != "__init__":
            continue
        try:
            doc = ast.get_docstring(node) or ""
        except Exception:  # noqa: BLE001 — docstring read never raises
            doc = ""
        first = next((l.strip() for l in doc.splitlines() if l.strip()), "")
        if not first:
            continue
        args = [a.arg for a in node.args.args
                if a.arg not in ("self", "cls")]
        out.append((node.name, f"{node.name}({', '.join(args)})", first))
    # Source order, deduped by name; never raises.
    seen: set[str] = set()
    ordered = []
    for name, sig, purpose in out:
        if name not in seen:
            seen.add(name)
            ordered.append((name, sig, purpose))
    return ordered


def _rot(ex_id) -> int:
    try:
        return int(hashlib.sha256(str(ex_id).encode()).hexdigest(), 16)
    except Exception:  # noqa: BLE001 — seeding must never raise
        return 0


def _choices(truth: str, others: list[str], ex_id) -> tuple[list[str], str]:
    """Four purposes, true one rotated by ex_id; (choices, answer)."""
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
        "Say what you expect from the name before looking at the choices.",
        "Verbs carry the action, nouns carry the object — split them.",
        "Verify on the back: the docstring first line is ground truth.",
    ]


def generate(ex_id, concept, snippet, ctx):
    """Build a naming-fluency card; never None, never raises."""
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
        targets = _doc_targets("\n".join(str(l) for l in snippet))
        if not targets:
            return _ungrounded(ex_id, name, file, line, commit)
        tname, sig, purpose = targets[_rot(ex_id) % len(targets)]
        others = [p for n, _, p in targets if n != tname]
        choices, answer = _choices(purpose, others, ex_id)
        return {
            "id": ex_id, "type": TYPE_NUM, "type_name": TYPE_NAME,
            "bloom": BLOOM,
            "concept_id": _concept_field(concept, "node_id", "nameguess"),
            "concept": name or tname, "file": file, "line": line,
            "commit": commit,
            "hints": _hints(),
            "front": (f"What does `{tname}` do? Guess from the name "
                      f"alone — signature: `{sig}`. Commit to a choice, "
                      "then verify against the recorded docstring."),
            "back": f"{tname}: {purpose} ({file}:{line or '?'})",
            "payload": {"name": tname, "signature": sig,
                        "choices": choices, "answer": answer,
                        "docstring": purpose, "grounded": True},
        }
    except Exception:
        return _ungrounded(ex_id, "", "app.py", 0, "")


def _ungrounded(ex_id, name, file, line, commit) -> dict:
    return {
        "id": ex_id, "type": TYPE_NUM, "type_name": TYPE_NAME,
        "bloom": BLOOM, "concept_id": "nameguess",
        "concept": name or "nameguess", "file": file, "line": line,
        "commit": commit, "hints": _hints(),
        "front": "What does this name do? (No documented name found.)",
        "back": "No documented function in scope — skipped by the pipeline.",
        "payload": {"name": "", "signature": "", "choices": [],
                    "answer": "", "docstring": "", "grounded": False},
    }


def _fail(msg: str) -> dict:
    return {"pass": False, "score": 0.0, "feedback": msg}


def grade(exercise: dict, submission: str, runner=None) -> dict:
    """Normalized exact-choice match; the back docstring is the verify."""
    _ = runner
    try:
        return _grade(exercise, submission)
    except Exception as exc:  # noqa: BLE001 — grading never raises
        return _fail(f"Grader hiccup ({exc}) — resubmit.")


def _norm(text: str) -> str:
    return " ".join(str(text or "").strip().split()).rstrip(".").lower()


def _grade(exercise: dict, submission: str) -> dict:
    p = (exercise or {}).get("payload", {}) or {}
    want = _norm(p.get("answer", ""))
    text = str(submission if submission is not None else "")
    if not text.strip():
        return _fail("Pick the purpose the name predicts — then verify "
                     "against the docstring on the back.")
    if not want:
        return _fail("No purpose recorded on this card.")
    if _norm(text) == want:
        return {"pass": True, "score": 1.0,
                "feedback": "Name read right — docstring confirms it."}
    return {"pass": False, "score": 0.0,
            "feedback": "That reading misleads — the docstring says: "
                        f"{p.get('answer', '')}"}


def render(exercise: dict) -> str:
    """Exercise widget: name + signature, four purpose choices."""
    name = html.escape(str((exercise.get("payload", {}) or {}).get(
        "name", exercise.get("concept", ""))))
    sig = html.escape(str((exercise.get("payload", {}) or {}).get(
        "signature", "")))
    front = html.escape(str(exercise.get("front", "")))
    type_name = html.escape(str(exercise.get("type_name", TYPE_NAME)))
    file_line = f"{exercise.get('file', '')}:{exercise.get('line', 0)}"
    opts = "".join(
        f"<label><input type='radio' name='answer' value='{html.escape(c)}'> "
        f"{html.escape(c)}</label><br>"
        for c in (exercise.get("payload", {}) or {}).get("choices", []))
    hints = "".join(
        f"<details><summary>Hint {i + 1}</summary>{html.escape(h)}</details>"
        for i, h in enumerate(exercise.get("hints", [])))
    return (
        f"<article><h3>{name} · {type_name}</h3>"
        f"<p>{front}</p>"
        f"<p><code>{sig}</code></p>"
        f"<details><summary>How grading works</summary>"
        f"<p><small>Predict the purpose from the name — exact choice "
        f"wins; the docstring on the back is the verify step.</small></p>"
        f"</details>"
        f"<form method='post'>{opts}<button>Commit prediction</button></form>"
        f"{hints}<p><small>{html.escape(file_line)}</small></p></article>")


def section_html() -> str:
    """Anchored status subsection; wired into the status page by the parent."""
    return (
        f"<h3 id='{STATUS_ANCHOR}'>Naming fluency <small>(feature)</small></h3>"
        "<p>Guess a function's purpose from its name alone, then verify "
        "against the recorded docstring — exact-choice grading, no "
        "sandbox. <code>groundwork/nameguess.py</code>.</p>"
    )


def tour_entry() -> dict:
    """Feature-tour registry entry (appended to tour.ENTRIES by parent)."""
    return {"id": "naming-fluency", "kind": "feature",
            "title": "Naming fluency",
            "blurb": "Guess what a name does before reading its docstring — prediction then verify.",
            "path": "/status", "anchor": "status-b18-nameguess"}
