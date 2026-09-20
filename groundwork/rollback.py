"""Rollback-planning exercise (type 48, F-25, bloom: evaluate).

The learner orders the steps of a small deploy/change rollback scenario
(freeze rollout, flag-flip, roll back deploy, down-migrate, verify).
The scenario is templated and grounded on the concept name; the payload
carries the correct order. Grading is an exact sequence check with
adjacent-pair partial credit — deterministic, no sandbox runner.
Stdlib only (``hashlib``/``html``/``random``), import-safe standalone:
no groundwork imports.

Plugin API: ``generate(ex_id, concept, snippet, ctx)``,
``render(exercise) -> html``, ``grade(exercise, submission, runner)``.
Registration lives in ``groundwork/exercises.py``
(TYPES, GENERATORS, BLOOM_TYPES); pipeline needs no skip guard.
"""
from __future__ import annotations

import hashlib
import html
import random

TYPE_NUM = 48
TYPE_NAME = "rollback-plan"
BLOOM = "evaluate"


def _concept_field(concept, name: str, default: str = "") -> str:
    return str(getattr(concept, name, default) or default)


def _seeded_order(ex_id: str, name: str, n: int) -> list[int]:
    digest = hashlib.sha256(f"{ex_id}:{name}".encode()).hexdigest()
    rng = random.Random(int(digest, 16))
    idx = list(range(n))
    rng.shuffle(idx)
    return idx


def _steps(name: str) -> list[str]:
    name = name or "service"
    return [
        f"Freeze the rollout of `{name}` — stop the bleeding, no new deploys.",
        "Flip the feature flag / route traffic back to the previous release.",
        f"Roll back the deploy of `{name}` to the last good release.",
        "Down-migrate the migration that shipped with it (newest first).",
        "Verify health (smoke checks + error rate), then re-enable rollout.",
    ]


def generate(ex_id, concept, snippet, ctx) -> dict:
    """Build a rollback-planning card; never raises on the generic suite ctx."""
    try:
        ctx = ctx or {}
        name = _concept_field(concept, "name", "service") or "service"
        kind = _concept_field(concept, "kind", "service")
        file = _concept_field(concept, "file")
        try:
            line = int(getattr(concept, "line", 0) or 0)
        except (TypeError, ValueError):
            line = 0
        commit = str(ctx.get("commit", "") or "")
        correct = _steps(name)
        perm = _seeded_order(str(ex_id), name, len(correct))
        steps = [correct[i] for i in perm]
        order = [perm.index(i) for i in range(len(correct))]
        front = (f"A change to `{name}` ({kind}) went bad in production: "
                 "migration + deploy + flag-flip all shipped together.\n"
                 f"Put these {len(steps)} rollback steps in the safe order "
                 "(first step first). Reply with space-separated step numbers.")
        back = "\n".join(f"{i + 1}. {s}" for i, s in enumerate(correct))
        hints = [
            "First stop the bleeding: freeze the rollout before undoing anything.",
            "Undo in reverse order of the blast radius: traffic/flag before data.",
            "Migrations roll back newest-first, and verification is always last.",
        ]
        return {
            "id": ex_id, "type": TYPE_NUM, "type_name": TYPE_NAME, "bloom": BLOOM,
            "concept_id": _concept_field(concept, "node_id", name),
            "concept": name, "file": file, "line": line, "commit": commit,
            "hints": hints, "front": front, "back": back,
            "payload": {"steps": steps, "order": order, "solution": correct,
                        "scenario": "migration + deploy + flag-flip rollback",
                        "grounded": True},
        }
    except Exception:  # never raise on the generic suite ctx
        name = "service"
        correct = _steps(name)
        return {"id": ex_id, "type": TYPE_NUM, "type_name": TYPE_NAME,
                "bloom": BLOOM, "concept_id": name, "concept": name,
                "file": "", "line": 0, "commit": "",
                "hints": ["Freeze first.", "Traffic before data.", "Verify last."],
                "front": "Put the rollback steps in the safe order.",
                "back": "\n".join(correct),
                "payload": {"steps": list(correct),
                            "order": list(range(len(correct))),
                            "solution": correct,
                            "scenario": "migration + deploy + flag-flip rollback",
                            "grounded": True}}


def _fail(msg: str) -> dict:
    return {"pass": False, "score": 0.0, "feedback": msg}


def _parse_order(text: str, n: int) -> list[int] | None:
    try:
        idx = [int(x) for x in str(text).replace(",", " ").split()]
    except (ValueError, TypeError):
        return None
    if len(idx) != n:
        return None
    if sorted(idx) == list(range(1, n + 1)):  # 1-based
        return [i - 1 for i in idx]
    if sorted(idx) == list(range(n)):  # 0-based
        return idx
    return None


def grade(exercise: dict, submission: str, runner=None) -> dict:
    """Exact sequence check with adjacent-pair partial credit. Never raises."""
    _ = runner
    try:
        payload = (exercise or {}).get("payload", {})
        steps = list(payload.get("steps", []) or [])
        order = list(payload.get("order", []) or [])
        n = len(steps)
        if n < 2 or len(order) != n:
            return _fail("Exercise payload is missing the step order.")
        text = str(submission if submission is not None else "").strip()
        if not text:
            return _fail("Submit the step numbers in rollback order, e.g. `2 1 3 4 5`.")
        got = _parse_order(text, n)
        if got is None:
            return _fail(f"Submit {n} space-separated step numbers (1-{n}), each once.")
        if got == order:
            return {"pass": True, "score": 1.0,
                    "feedback": f"Correct rollback order ({n}/{n} steps)."}
        pairs = sum(1 for i in range(n - 1)
                    if order.index(got[i]) + 1 == order.index(got[i + 1]))
        # Longest correct contiguous run (in submission terms).
        pos = [order.index(i) for i in got]
        run = best = 1
        for a, b in zip(pos, pos[1:]):
            run = run + 1 if b == a + 1 else 1
            best = max(best, run)
        score = pairs / max(1, n - 1)
        first_bad = next((i + 1 for i in range(n) if got[i] != order[i]), n)
        return {"pass": False, "score": score,
                "feedback": f"Not quite ({pairs}/{n - 1} adjacent pairs right; "
                            f"longest correct run {best}/{n}). "
                            f"Step {first_bad} is the first out of place — reorder and retry."}
    except Exception:  # noqa: BLE001 — grading must never raise
        return _fail("Grader could not read the submission — submit step numbers.")


def render(exercise: dict) -> str:
    """Shuffled steps + ordering widget + click-to-order note."""
    payload = (exercise or {}).get("payload", {})
    front = html.escape(str(exercise.get("front", "")))
    concept = html.escape(str(exercise.get("concept", "")))
    type_name = html.escape(str(exercise.get("type_name", TYPE_NAME)))
    items = "".join(
        f"<li><b>{i + 1}.</b> {html.escape(str(s))}</li>"
        for i, s in enumerate(payload.get("steps", [])))
    file_line = f"{exercise.get('file', '')}:{exercise.get('line', 0)}"
    hints = "".join(
        f"<details><summary>Hint {i + 1}</summary>{html.escape(h)}</details>"
        for i, h in enumerate(exercise.get("hints", [])))
    return (
        f"<article><h3>{concept} · {type_name}</h3>"
        f"<p>{front}</p><ol>{items}</ol>"
        f"<details><summary>How grading works</summary>"
        f"<p><small>Exact step sequence required to pass; partial credit "
        f"per correct adjacent pair (longest correct run reported). "
        f"No sandbox.</small></p></details>"
        f"<form method='post'><input name='answer' size='30' "
        f"placeholder='e.g. 2 1 3 4 5'><br>"
        f"<small>Or click steps in order, then type the numbers.</small><br>"
        f"<button>Check order</button></form>{hints}"
        f"<p><small>{html.escape(file_line)}</small></p></article>")


def section_html() -> str:
    """Anchored status subsection; wired into the status page by the parent."""
    return (
        "<h3 id='status-b8-rollback'>Rollback planning <small>(feature)</small></h3>"
        "<p>Order the rollback steps for a bad deploy — freeze, flag-flip, "
        "roll back the deploy, down-migrate, verify. Graded by exact sequence "
        "with adjacent-pair partial credit, no sandbox. "
        "<code>groundwork/rollback.py</code>.</p>"
    )


def tour_entry() -> dict:
    """Feature-tour registry entry (appended to tour.ENTRIES by parent)."""
    return {"id": "rollback-type", "kind": "feature",
            "title": "Rollback planning",
            "blurb": "Order the rollback steps for a bad deploy — freeze, flag, revert, verify.",
            "path": "/status", "anchor": "status-b8-rollback"}
