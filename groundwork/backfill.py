"""Backfill-script exercise (type 67, F-44, bloom: modify).

The learner writes a ``backfill(rows)`` function migrating old-shape
fixture rows to the target shape (rename ``label``→``title`` with a
default, coerce ``score`` to int, default ``status``, drop the retired
``legacy``/``label`` fields, keep every row in order). Unlike type 47
(migration-authoring, static JSON graded with no execution), type 67
EXECUTES the learner's function in the sandbox over fixtures — it
tests code, not data.

``generate`` never returns None and never raises: fixtures seed from
``ex_id`` alone, so a card is always groundable; thin input yields a
fallback card on a fixed ``record`` concept.

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
import copy
import hashlib
import html
import json
import re

TYPE_NUM = 67
TYPE_NAME = "backfill-script"
BLOOM = "modify"
STATUS_ANCHOR = "status-b11-backfill"

FUNC = "backfill"
OLD_FIELD = "label"
NEW_FIELD = "title"
DEFAULT_TITLE = "untitled"
DEFAULT_STATUS = "active"
RETIRED = ("legacy", "label")
_MAX_ROWS = 3
_MAX_CHARS = 20000

_REFERENCE_SRC = (
    "def backfill(rows):\n"
    "    out = []\n"
    "    for r in rows:\n"
    "        try:\n"
    "            score = int(r.get(\"score\", 0))\n"
    "        except (ValueError, TypeError):\n"
    "            score = 0\n"
    "        out.append({\"id\": r.get(\"id\"), "
    "\"title\": r.get(\"label\", \"untitled\"), "
    "\"score\": score, \"status\": r.get(\"status\", \"active\")})\n"
    "    return out\n"
)

_HARNESS_TAIL = (
    "\nimport json as _json, copy as _copy\n"
    "def _canon(rows):\n"
    "    vals, keys = [], []\n"
    "    for r in rows:\n"
    "        if isinstance(r, dict):\n"
    "            vals.append([r.get('id'), r.get('title'), "
    "r.get('score'), r.get('status')])\n"
    "            keys.append(sorted(str(k) for k in r.keys()))\n"
    "        else:\n"
    "            vals.append(r)\n"
    "            keys.append([])\n"
    "    return {'rows': vals, 'keys': keys}\n"
    "_out = backfill(_copy.deepcopy(_ROWS_))\n"
    "print(_json.dumps(_canon(_out)))\n"
)


def _concept_field(concept, name: str, default: str = "") -> str:
    return str(getattr(concept, name, default) or default)


def _clean_word(name: str) -> str:
    words = re.findall(r"[a-z0-9]+", str(name or "").lower())
    return " ".join(words) or "record"


def _seed(ex_id, cname: str) -> int:
    try:
        digest = hashlib.sha256(
            f"{ex_id}|{cname}".encode()).hexdigest()[:8]
        return int(digest, 16)
    except (TypeError, ValueError):
        return 0


def _backfill(rows) -> list:
    """Reference migration: rename, coerce, default, drop retired."""
    out = []
    for r in rows:
        try:
            score = int(r.get("score", 0))
        except (ValueError, TypeError):
            score = 0
        out.append({"id": r.get("id"),
                    "title": r.get(OLD_FIELD, DEFAULT_TITLE),
                    "score": score,
                    "status": r.get("status", DEFAULT_STATUS)})
    return out


def _canon(rows) -> list:
    return [[r.get("id"), r.get("title"), r.get("score"), r.get("status")]
            for r in rows]


def _fixture_rows(seed: int, base: str) -> list:
    first = {"id": 1, OLD_FIELD: base, "score": 10 + seed % 40}
    second = {"id": 2, "score": 5, RETIRED[0]: "v1"}
    third = {"id": 3, OLD_FIELD: base + "+", "score": str(7 + seed % 10),
             "status": "archived"}
    return [first, second, third][:max(1, _MAX_ROWS)]


def _front_text(old_rows) -> str:
    rules = (
        f"Write `def {FUNC}(rows):` migrating each old row to "
        f"{{\"id\", \"{NEW_FIELD}\", \"score\", \"status\"}}: rename "
        f"`{OLD_FIELD}`→`{NEW_FIELD}` (missing → \"{DEFAULT_TITLE}\"), "
        "coerce `score` to int (missing/invalid → 0), default `status` to "
        f"\"{DEFAULT_STATUS}\" when missing, drop retired fields "
        f"(`{'`, `'.join(RETIRED)}`), keep every row in order."
    )
    return f"{rules}\nOld rows:\n```json\n{json.dumps(old_rows)}\n```"


def _hints() -> list[str]:
    return [
        f"Rename plus default: `r.get(\"{OLD_FIELD}\", \"{DEFAULT_TITLE}\")`.",
        "Coerce the score inside try/except — strings and junk arrive.",
        "Rebuild each row with only the four target keys; retired fields go.",
    ]


def generate(ex_id, concept, snippet, ctx):
    """Build a backfill card; never None, never raises."""
    try:
        ctx = ctx if isinstance(ctx, dict) else {}
        snippet = list(snippet or [])
        name = _concept_field(concept, "name", "")
        file = _concept_field(concept, "file", "") or "records.py"
        try:
            line = int(getattr(concept, "line", 0) or 0)
        except (TypeError, ValueError):
            line = 0
        commit = str(ctx.get("commit", "") or "")
        base = _clean_word(name or "record")
        if not name and not any(str(l).strip() for l in snippet):
            old_rows = [{"id": 1, OLD_FIELD: "record", "score": "3"}]
            grounded = False
            concept_label = "record"
        else:
            old_rows = _fixture_rows(_seed(ex_id, base), base)
            grounded = True
            concept_label = name or "record"
        expected = _backfill(copy.deepcopy(old_rows))
        return {
            "id": ex_id, "type": TYPE_NUM, "type_name": TYPE_NAME,
            "bloom": BLOOM,
            "concept_id": _concept_field(concept, "node_id", concept_label),
            "concept": concept_label, "file": file, "line": line,
            "commit": commit,
            "hints": _hints(),
            "front": _front_text(old_rows),
            "back": _REFERENCE_SRC + json.dumps(expected),
            "payload": {"func": FUNC, "old_field": OLD_FIELD,
                        "new_field": NEW_FIELD,
                        "defaults": {"title": DEFAULT_TITLE,
                                     "status": DEFAULT_STATUS},
                        "retired": list(RETIRED),
                        "old_rows": old_rows, "expected": expected,
                        "reference": _REFERENCE_SRC, "grounded": grounded},
        }
    except Exception:
        return {  # generate never raises and never returns None
            "id": ex_id, "type": TYPE_NUM, "type_name": TYPE_NAME,
            "bloom": BLOOM, "concept_id": "record", "concept": "record",
            "file": "records.py", "line": 0, "commit": "",
            "hints": _hints(),
            "front": _front_text(
                [{"id": 1, OLD_FIELD: "record", "score": "3"}]),
            "back": _REFERENCE_SRC,
            "payload": {"func": FUNC, "old_field": OLD_FIELD,
                        "new_field": NEW_FIELD,
                        "defaults": {"title": DEFAULT_TITLE,
                                     "status": DEFAULT_STATUS},
                        "retired": list(RETIRED),
                        "old_rows": [{"id": 1, OLD_FIELD: "record",
                                      "score": "3"}],
                        "expected": _backfill(
                            [{"id": 1, OLD_FIELD: "record", "score": "3"}]),
                        "reference": _REFERENCE_SRC, "grounded": False},
        }


def _fail(msg: str) -> dict:
    return {"pass": False, "score": 0.0, "feedback": msg}


def grade(exercise: dict, submission: str, runner=None) -> dict:
    """Sandbox-executed migration gate over fixture rows."""
    try:
        return _grade(exercise, submission, runner)
    except Exception as exc:  # noqa: BLE001 — grading never raises
        return _fail(f"Grader hiccup ({exc}) — resubmit.")


def _defines_backfill(text: str) -> bool:
    try:
        tree = ast.parse(text)
    except (SyntaxError, ValueError):
        return False
    return any(isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
               and n.name == FUNC and n.args.args
               for n in ast.walk(tree))


def _grade(exercise: dict, submission: str, runner=None) -> dict:
    p = (exercise or {}).get("payload", {}) or {}
    old_rows = p.get("old_rows")
    expected = p.get("expected")
    if not isinstance(old_rows, list) or not old_rows \
            or not isinstance(expected, list):
        return _fail("Card has no fixtures.")
    text = str(submission if submission is not None else "")
    if not text.strip():
        return _fail(f"Submit a `def {FUNC}(rows):` function.")
    if len(text) > _MAX_CHARS:
        return _fail("Submission too long — submit just the function.")
    if not _defines_backfill(text):
        return _fail(f"Define `def {FUNC}(rows):` taking the rows.")
    if runner is None:
        return _fail("No sandbox available for grading.")
    harness = text + _HARNESS_TAIL.replace(
        "_ROWS_", json.dumps(old_rows))
    res = runner.run(harness)
    if not bool(res.ok):
        last = str(res.stderr).strip().splitlines()
        return _fail(f"Your function raised: {(last[-1] if last else 'error')[:200]}")
    try:
        got = json.loads(str(res.stdout).strip().splitlines()[-1])
    except (ValueError, IndexError):
        return _fail("Harness printed no JSON — return the migrated list.")
    if not isinstance(got, dict) or not isinstance(got.get("rows"), list):
        return _fail("Return the migrated list of rows.")
    rows, keys = got["rows"], got.get("keys", [])
    want = _canon(expected)
    if len(rows) != len(want):
        return _fail(f"Row count {len(rows)} != {len(want)} "
                      "(no rows lost or added).")
    for keyset in keys:
        hit = next((f for f in RETIRED if f in keyset), None)
        if hit is not None:
            return _fail(f"Retired field `{hit}` must be dropped.")
    if rows == want:
        return {"pass": True, "score": 1.0,
                "feedback": f"Backfill correct ({len(want)} rows)."}
    hits = sum(1 for g, w in zip(rows, want) if g == w)
    bad = [str(i) for i, (g, w) in enumerate(zip(rows, want)) if g != w]
    return {"pass": False, "score": 0.0,
            "feedback": f"Row(s) {','.join(bad)} wrong ({hits}/{len(want)} "
                        "right) — check rename/default/coercion."}


def render(exercise: dict) -> str:
    """Exercise widget: migration spec plus stub textarea."""
    front = html.escape(str(exercise.get("front", "")))
    concept = html.escape(str(exercise.get("concept", "")))
    type_name = html.escape(str(exercise.get("type_name", TYPE_NAME)))
    file_line = f"{exercise.get('file', '')}:{exercise.get('line', 0)}"
    hints = "".join(
        f"<details><summary>Hint {i + 1}</summary>{html.escape(h)}</details>"
        for i, h in enumerate(exercise.get("hints", [])))
    stub = html.escape(f"def {FUNC}(rows):\n    out = []\n    return out\n")
    return (
        f"<article><h3>{concept} · {type_name}</h3>"
        f"<p>{front}</p>"
        f"<details><summary>How grading works</summary>"
        f"<p><small>Your function runs in the sandbox over fixture rows: "
        f"every row migrated with defaults applied and no rows lost "
        f"passes.</small></p></details>"
        f"<form method='post'><textarea name='answer' rows='12' cols='70'>"
        f"{stub}</textarea><br><button>Migrate rows</button></form>{hints}"
        f"<p><small>{html.escape(file_line)}</small></p></article>")


def section_html() -> str:
    """Anchored status subsection; wired into the status page by the parent."""
    return (
        f"<h3 id='{STATUS_ANCHOR}'>Backfill script <small>(feature)</small></h3>"
        "<p>Write a <code>backfill(rows)</code> function that migrates "
        "old-shape rows (rename, coerce, defaults, drop retired fields) — "
        "graded by sandbox execution over fixtures, no rows lost. "
        "<code>groundwork/backfill.py</code>.</p>"
    )


def tour_entry() -> dict:
    """Feature-tour registry entry (appended to tour.ENTRIES by parent)."""
    return {"id": "backfill-script", "kind": "feature",
            "title": "Backfill script",
            "blurb": "Write a backfill function that migrates old rows to the new shape — sandbox-executed over fixtures.",
            "path": "/status", "anchor": "status-b11-backfill"}
