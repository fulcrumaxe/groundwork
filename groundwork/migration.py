"""Schema-migration authoring exercise (type 47, F-24, bloom: modify).

Learner migrates old-shape rows to a new shape: a field rename with a
default for missing values, grounded on the concept name. Fixtures
(old rows + expected new rows) are generated deterministically from
ex_id + concept name, so the card is self-contained (grounded=True
always, no pipeline guard). Grading is deterministic fixture
comparison: the submission is the migrated rows as JSON; no code is
executed, no sandbox runner needed (runner accepted, ignored).

Plugin API: generate(ex_id, concept, snippet, ctx),
render(exercise) -> html, grade(exercise, submission, runner).
Registration (parent): TYPES/GENERATORS/BLOOM_TYPES + delegate
branches in exercises.render/grade, pipeline BLOOM_DEFAULT_TYPES,
one status.py include, one tour entry.
"""
from __future__ import annotations

import hashlib
import html
import json
import re

TYPE_NUM = 47
TYPE_NAME = "migration-authoring"
BLOOM = "modify"

OLD_FIELD = "name"
NEW_FIELD = "title"
DEFAULT = "untitled"
FUNC = "migrate"

_MAX_ROWS = 3
_MAX_CELL = 40


def _concept_field(concept, name: str, default: str = "") -> str:
    return str(getattr(concept, name, default) or default)


def _seed(ex_id, concept_name: str) -> int:
    h = hashlib.sha256(f"{ex_id}|{concept_name}".encode()).hexdigest()
    return int(h[:8], 16)


def _clean_word(text: str) -> str:
    w = re.sub(r"[^A-Za-z0-9 ]+", "", text).strip().split()
    return (" ".join(w)[:_MAX_CELL].strip() or "item")


def _old_rows(seed: int, label: str) -> list[dict]:
    base = _clean_word(label) or "item"
    rows = [{"id": 1, OLD_FIELD: f"{base}-alpha", "count": 2},
            {"id": 2, OLD_FIELD: f"{base}-beta", "count": 5}]
    if seed % 3 == 0:  # every third card: one row missing the field
        rows.append({"id": 3, "count": 7})
    return rows[:_MAX_ROWS]


def _migrate(rows: list[dict]) -> list[dict]:
    out = []
    for r in rows:
        if not isinstance(r, dict):
            continue
        out.append({"id": r.get("id"),
                    NEW_FIELD: r.get(OLD_FIELD, DEFAULT),
                    "count": r.get("count", 0)})
    return out


def _reference(rows: list[dict]) -> str:
    return (
        f"def {FUNC}(rows):\n"
        f"    return [dict(r, {NEW_FIELD}=r.get({OLD_FIELD!r}, {DEFAULT!r})) "
        f"if {OLD_FIELD!r} in r else dict(r, {NEW_FIELD}={DEFAULT!r}) "
        "for r in rows]")


def generate(ex_id, concept, snippet, ctx) -> dict:
    """Build a migration card; never raises on the generic suite ctx."""
    try:
        ctx = ctx or {}
        cname = _concept_field(concept, "name", "record") or "record"
        file = _concept_field(concept, "file")
        try:
            line = int(getattr(concept, "line", 0) or 0)
        except (TypeError, ValueError):
            line = 0
        commit = str(ctx.get("commit", "") or "")
        old = _old_rows(_seed(str(ex_id), cname), cname)
        expected = _migrate(old)
        front = (
            f"Migrate {len(old)} `{cname}` rows: rename field `{OLD_FIELD}` "
            f"-> `{NEW_FIELD}`; rows missing `{OLD_FIELD}` get "
            f"`{DEFAULT!r}`. Keep `id` and `count` unchanged.\n"
            f"Old rows:\n```json\n{json.dumps(old, indent=2)[:800]}\n```\n"
            f"Reply with the migrated rows as a JSON list.")
        back = json.dumps(expected, indent=2)
        hints = [
            f"Rename `{OLD_FIELD}` to `{NEW_FIELD}` on every row.",
            f"Missing `{OLD_FIELD}` means `{NEW_FIELD}={DEFAULT!r}` — do not drop the row.",
            "Drop the old field: a rename moves it, never copies it.",
        ]
        return {
            "id": ex_id, "type": TYPE_NUM, "type_name": TYPE_NAME,
            "bloom": BLOOM,
            "concept_id": _concept_field(concept, "node_id", cname),
            "concept": cname, "file": file, "line": line,
            "commit": commit, "hints": hints, "front": front, "back": back,
            "payload": {"func": FUNC, "old_field": OLD_FIELD,
                        "new_field": NEW_FIELD, "default": DEFAULT,
                        "old_rows": old, "expected": expected,
                        "reference": _reference(old), "grounded": True},
        }
    except Exception:  # never raise on suite ctx; minimal fallback card
        old = [{"id": 1, OLD_FIELD: "item"}]
        return {
            "id": ex_id, "type": TYPE_NUM, "type_name": TYPE_NAME,
            "bloom": BLOOM, "concept_id": "fallback", "concept": "record",
            "file": "", "line": 0, "commit": "",
            "hints": ["Rename the field.", "Keep the row.", "Reply with JSON."],
            "front": "Migrate the row: rename `name` -> `title`.",
            "back": json.dumps(_migrate(old)),
            "payload": {"func": FUNC, "old_field": OLD_FIELD,
                        "new_field": NEW_FIELD, "default": DEFAULT,
                        "old_rows": old, "expected": _migrate(old),
                        "reference": "", "grounded": True},
        }


def _fail(msg: str) -> dict:
    return {"pass": False, "score": 0.0, "feedback": msg}


def _canon(rows) -> list[tuple] | None:
    if not isinstance(rows, list):
        return None
    out = []
    for r in rows:
        if not isinstance(r, dict):
            return None
        try:
            out.append((r.get("id"), str(r.get(NEW_FIELD, "")),
                        r.get("count", 0)))
        except Exception:
            return None
    return out


def grade(exercise: dict, submission: str, runner=None) -> dict:
    """Fixture comparison; runner ignored. Never raises."""
    _ = runner
    try:
        payload = (exercise or {}).get("payload", {}) or {}
        old_field = str(payload.get("old_field", OLD_FIELD) or OLD_FIELD)
        expected = _canon(payload.get("expected", []))
        # Empty fixtures mean a broken card: fail closed, never pass.
        if not expected:
            return _fail("Card has no fixtures — nothing to grade.")
        text = str(submission if submission is not None else "").strip()
        if not text:
            return _fail("Submit the migrated rows as a JSON list.")
        if len(text) > 20000:
            return _fail("Submission too large — submit just the rows.")
        try:
            raw = json.loads(text)
        except (ValueError, TypeError):
            return _fail("Submission is not a JSON list of rows — "
                         "submit the migrated rows as JSON.")
        if isinstance(raw, list) and any(
                isinstance(r, dict) and old_field in r for r in raw):
            return _fail(f"A rename moves `{old_field}` — drop the old field, do not copy it.")
        given = _canon(raw)
        if given is None:
            return _fail("Each row must be an object with id/title/count.")
        if given == expected:
            return {"pass": True, "score": 1.0,
                    "feedback": f"Migration correct ({len(expected)} rows)."}
        hits = sum(1 for g, w in zip(given, expected) if g == w)
        total = max(len(expected), len(given), 1)
        score = hits / total
        if len(given) != len(expected):
            return {"pass": False, "score": score,
                    "feedback": f"Row count {len(given)} != {len(expected)} "
                                f"({hits}/{len(expected)} rows right)."}
        bad = [str(i + 1) for i, (g, w) in
               enumerate(zip(given, expected)) if g != w]
        return {"pass": False, "score": score,
                "feedback": f"Row(s) {', '.join(bad)} wrong "
                            f"({hits}/{len(expected)} right) — check the "
                            f"`{OLD_FIELD}` -> `{NEW_FIELD}` rename and default."}
    except Exception:  # noqa: BLE001 — grading never raises
        return _fail("Grader could not read the submission — submit JSON rows.")


def render(exercise: dict) -> str:
    """Card widget: fixtures plus a JSON answer box."""
    payload = (exercise or {}).get("payload", {}) or {}
    front = html.escape(str(exercise.get("front", "")))
    concept = html.escape(str(exercise.get("concept", "")))
    type_name = html.escape(str(exercise.get("type_name", TYPE_NAME)))
    seed = html.escape(json.dumps(payload.get("old_rows", []), indent=2))
    file_line = f"{exercise.get('file', '')}:{exercise.get('line', 0)}"
    hints = "".join(
        f"<details><summary>Hint {i + 1}</summary>{html.escape(h)}</details>"
        for i, h in enumerate(exercise.get("hints", [])))
    return (
        f"<article><h3>{concept} · {type_name}</h3>"
        f"<p>{front}</p>"
        f"<details><summary>How grading works</summary>"
        f"<p><small>Deterministic fixture comparison: your JSON rows must "
        f"equal the expected migrated rows exactly (renamed field plus "
        f"default, same order). No code runs, no sandbox.</small></p></details>"
        f"<form method='post'><textarea name='answer' rows='10' "
        f"cols='70'>{seed}</textarea><br><button>Check migration</button></form>"
        f"{hints}<p><small>{html.escape(file_line)}</small></p></article>")


def section_html() -> str:
    """Anchored status subsection; wired into the status page by the parent."""
    return (
        "<h3 id='status-b8-migration'>Migration authoring <small>(feature)</small></h3>"
        "<p>Write a schema migration — rename a field with a default across "
        "fixture rows. Graded by deterministic fixture comparison, no sandbox. "
        "<code>groundwork/migration.py</code>.</p>"
    )


def tour_entry() -> dict:
    """Feature-tour registry entry (appended to tour.ENTRIES by parent)."""
    return {"id": "migration-type", "kind": "feature",
            "title": "Migration authoring",
            "blurb": "Rename a record field with a default across fixture rows.",
            "path": "/status", "anchor": "status-b8-migration"}
