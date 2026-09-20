"""Bisect drill (type 45, F-22, bloom: analyse).

The learner finds the breaking commit in a small SYNTHETIC history.
Deterministic from the concept id hash: N fake commits each with a
pass/fail test outcome and exactly one breaking commit (first FAIL;
all before it PASS, all from it on FAIL). The history is self-contained
in the payload, so no repo access is needed at grade time.

Plugin API: ``generate(ex_id, concept, snippet, ctx)``,
``render(exercise) -> html``, ``grade(exercise, submission, runner)``.
Registration lives in ``groundwork/exercises.py``
(TYPES, GENERATORS, BLOOM_TYPES); see ===WIRES=== (parent wires).
"""
from __future__ import annotations

import hashlib
import html

TYPE_NUM = 45
TYPE_NAME = "bisect-drill"
BLOOM = "analyse"

N_COMMITS = 6
_MSGS = ("add helper", "tweak logging", "refactor loop",
         "bump timeout", "rename var", "fix typo", "speed up query")


def _concept_field(concept, name: str, default: str = "") -> str:
    return str(getattr(concept, name, default) or default)


def _seed(concept) -> str:
    cid = _concept_field(concept, "node_id", "") or _concept_field(concept, "name", "x")
    return hashlib.sha256(cid.encode("utf-8")).hexdigest()


def _history(seed: str) -> tuple[list[dict], int]:
    n = N_COMMITS
    breaking = 1 + int(seed[:8], 16) % (n - 1)  # 1..n-1, never 0: a culprit needs a green parent
    commits = []
    for i in range(n):
        h = hashlib.sha256(f"{seed}:{i}".encode()).hexdigest()[:7]
        commits.append({"index": i, "hash": h,
                        "message": _MSGS[int(seed[2 * i:2 * i + 2], 16) % len(_MSGS)],
                        "result": "FAIL" if i >= breaking else "PASS"})
    return commits, breaking


def generate(ex_id, concept, snippet, ctx) -> dict:
    """Build a bisect card; never raises on the generic suite ctx."""
    try:
        ctx = ctx or {}
        name = _concept_field(concept, "name", "func")
        file = _concept_field(concept, "file")
        try:
            line = int(getattr(concept, "line", 0) or 0)
        except (TypeError, ValueError):
            line = 0
        commit = str(ctx.get("commit", "") or "")
        seed = _seed(concept)
        commits, breaking = _history(seed)
        culprit = commits[breaking]
        rows = "\n".join(f"{c['index']} {c['hash']} {c['message']} [{c['result']}]"
                         for c in commits)
        front = (f"Bisect the regression in `{name}`: the test passed, now it fails.\n"
                 f"Name the breaking commit (hash or index).\n```\n{rows}\n```")
        back = f"Breaking commit: {culprit['index']} ({culprit['hash']}) — first FAIL."
        hints = [f"PASS commits are innocent; the culprit is the first FAIL ({commits[0]['hash']} passed).",
                 "Bisect it: check the middle commit, then halve the failing half.",
                 f"Answer with `{culprit['hash']}` or `{culprit['index']}`."]
        return {"id": ex_id, "type": TYPE_NUM, "type_name": TYPE_NAME, "bloom": BLOOM,
                "concept_id": _concept_field(concept, "node_id", name),
                "concept": name, "file": file, "line": line, "commit": commit,
                "hints": hints, "front": front, "back": back,
                "payload": {"commits": commits, "breaking_index": breaking,
                            "breaking_hash": culprit["hash"], "grounded": True}}
    except Exception:  # noqa: BLE001 — generate must never raise
        return {"id": ex_id, "type": TYPE_NUM, "type_name": TYPE_NAME, "bloom": BLOOM,
                "concept_id": "x", "concept": "x", "file": "", "line": 0, "commit": "",
                "hints": ["Name the first FAIL commit."], "front": "Name the breaking commit.",
                "back": "", "payload": {"commits": [], "breaking_index": -1,
                                        "breaking_hash": "", "grounded": True}}


def _fail(msg: str) -> dict:
    return {"pass": False, "score": 0.0, "feedback": msg}


def _candidates(payload: dict) -> set[str]:
    # No history (fallback card) means no answer: fail closed.
    if not (payload or {}).get("commits"):
        return set()
    out = set()
    bh = str(payload.get("breaking_hash", "") or "").lower()
    if bh:
        out.add(bh)
    try:
        out.add(str(int(payload.get("breaking_index", -1))))
    except (TypeError, ValueError):
        pass
    return out


def grade(exercise: dict, submission: str, runner=None) -> dict:
    """Exact hash-or-index match; no sandbox. Never raises."""
    _ = runner
    try:
        payload = (exercise or {}).get("payload", {})
        want = _candidates(payload)
        if not want:
            return _fail("Card has no breaking commit — regenerate it.")
        text = str(submission or "").strip().lower()
        if not text:
            return _fail("Name the breaking commit hash or index.")
        tok = text.replace("commit", " ").replace("#", " ").replace(":", " ").split()
        got = tok[-1] if tok else ""
        if got in want:
            return {"pass": True, "score": 1.0,
                    "feedback": f"Correct — {payload.get('breaking_hash')} (index {payload.get('breaking_index')}) is the first FAIL."}
        return _fail(f"Not the culprit — want hash `{payload.get('breaking_hash')}` or index `{payload.get('breaking_index')}`.")
    except Exception:  # noqa: BLE001 — grading must never raise
        return _fail("Grader could not read the submission — send a commit hash or index.")


def render(exercise: dict) -> str:
    """History table + answer box + How-grading-works disclosure."""
    payload = (exercise or {}).get("payload", {})
    front = html.escape(str(exercise.get("front", "")))
    concept = html.escape(str(exercise.get("concept", "")))
    type_name = html.escape(str(exercise.get("type_name", TYPE_NAME)))
    rows = "".join(
        f"<tr><td>{html.escape(str(c.get('index', '')))}</td>"
        f"<td><code>{html.escape(str(c.get('hash', '')))}</code></td>"
        f"<td>{html.escape(str(c.get('message', '')))}</td>"
        f"<td>{html.escape(str(c.get('result', '')))}</td></tr>"
        for c in payload.get("commits", []))
    file_line = f"{exercise.get('file', '')}:{exercise.get('line', 0)}"
    return (
        f"<article><h3>{concept} · {type_name}</h3>"
        f"<p>{front}</p>"
        f"<table><tr><th>#</th><th>commit</th><th>message</th><th>test</th></tr>{rows}</table>"
        f"<details><summary>How grading works</summary>"
        f"<p><small>Exact match on the breaking commit hash or index; "
        f"off-by-one (parent or next commit) fails. Deterministic, no sandbox.</small></p></details>"
        f"<form method='post'><input name='answer' placeholder='hash or index'>"
        f"<button>Check culprit</button></form>"
        f"<p><small>{html.escape(file_line)}</small></p></article>")


def section_html() -> str:
    """Anchored status subsection; wired into the status page by the parent."""
    return (
        "<h3 id='status-b8-bisect'>Bisect drill <small>(feature)</small></h3>"
        "<p>Name the breaking commit in a synthetic history — graded by exact "
        "hash-or-index match, no sandbox. "
        "<code>groundwork/bisect.py</code>.</p>"
    )


def tour_entry() -> dict:
    """Feature-tour registry entry (appended to tour.ENTRIES by parent)."""
    return {"id": "bisect-type", "kind": "feature",
            "title": "Bisect drill",
            "blurb": "Find the breaking commit in a synthetic history — hash or index.",
            "path": "/status", "anchor": "status-b8-bisect"}
