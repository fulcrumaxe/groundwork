"""Feature demo: backfill-script exercise (F-44, type 67).

Full behavior: the learner writes def backfill(rows) migrating
old-shape fixture rows (rename label to title, coerce score, default
status, drop retired fields, keep order). Unlike static migration
cards, the submitted FUNCTION executes in the sandbox over fixtures.
seed_db plants the generated card as the sole due card.
"""
from __future__ import annotations

import json
import sqlite3

CARD_ID = 'demo-backfill-67'
FRONT = 'Write `def backfill(rows):` migrating each old row to {"id", "title", "score", "status"}: rename `label`\u2192`title` (missing \u2192 "untitled"), coerce `score` to int (missing/invalid \u2192 0), default `status` to "active" when missing, drop retired fields (`legacy`, `label`), keep every row in order.\nOld rows:\n```json\n[{"id": 1, "label": "record", "score": 40}, {"id": 2, "score": 5, "legacy": "v1"}, {"id": 3, "label": "record+", "score": "7", "status": "archived"}]\n```'
BACK = 'def backfill(rows):\n    out = []\n    for r in rows:\n        try:\n            score = int(r.get("score", 0))\n        except (ValueError, TypeError):\n            score = 0\n        out.append({"id": r.get("id"), "title": r.get("label", "untitled"), "score": score, "status": r.get("status", "active")})\n    return out\n[{"id": 1, "title": "record", "score": 40, "status": "active"}, {"id": 2, "title": "untitled", "score": 5, "status": "active"}, {"id": 3, "title": "record+", "score": 7, "status": "archived"}]'
PAYLOAD = {'func': 'backfill', 'old_field': 'label', 'new_field': 'title', 'defaults': {'title': 'untitled', 'status': 'active'}, 'retired': ['legacy', 'label'], 'old_rows': [{'id': 1, 'label': 'record', 'score': 40}, {'id': 2, 'score': 5, 'legacy': 'v1'}, {'id': 3, 'label': 'record+', 'score': '7', 'status': 'archived'}], 'expected': [{'id': 1, 'title': 'record', 'score': 40, 'status': 'active'}, {'id': 2, 'title': 'untitled', 'score': 5, 'status': 'active'}, {'id': 3, 'title': 'record+', 'score': 7, 'status': 'archived'}], 'reference': 'def backfill(rows):\n    out = []\n    for r in rows:\n        try:\n            score = int(r.get("score", 0))\n        except (ValueError, TypeError):\n            score = 0\n        out.append({"id": r.get("id"), "title": r.get("label", "untitled"), "score": score, "status": r.get("status", "active")})\n    return out\n', 'grounded': True}
ANSWER = 'def backfill(rows):\n    out = []\n    for r in rows:\n        try:\n            score = int(r.get("score", 0))\n        except (ValueError, TypeError):\n            score = 0\n        out.append({"id": r.get("id"), "title": r.get("label", "untitled"), "score": score, "status": r.get("status", "active")})\n    return out\n'

SCENARIO = {
    "id": "backfill",
    "kind": "feature",
    "batch": 11,
    "item": "F-44",
    "title": "Backfill script",
    "blurb": "Migrate old rows with code -- the function runs, not the data.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 11 - Feature F-44",
         "title": "Backfill script",
         "subtitle": "Old rows in, new shape out -- your function does it."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b11-backfill",
         "caption": "Status homes the type: executed migration, rename, coerce, drop.",
         "assert_js": "() => !!document.querySelector('#status-b11-backfill')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 8,
         "caption": "The rule in one line: the reference migrates all rows, passthrough fails.",
         "commands": [
             ["python3", "-c",
              "import sys; sys.path.insert(0, 'tools'); "
              "from demos.backfill import PAYLOAD, ANSWER; "
              "from groundwork import backfill as m; "
              "from groundwork.sandbox import SandboxRunner; "
              "ex = {'payload': PAYLOAD}; r = SandboxRunner(); "
              "ok = m.grade(ex, ANSWER, r); "
              "bad = m.grade(ex, 'def backfill(rows):\\n    return rows\\n', r); "
              "print('good:', ok['pass'], '-', ok['feedback']); "
              "print('bad:', bad['pass'], '-', bad['feedback'])"],
         ]},
        {"type": "chrome", "duration": 8,
         "url_path": "/due",
         "focus": "#card-{seed_card_id}",
         "caption": "The backfill card: old rows on top, function below.",
         "assert_js": "() => { const f = document.querySelector("
                      "\"form[action='/cards/{seed_card_id}/review']\"); "
                      "return !!f && !!f.querySelector(\"[name='answer']\") && "
                      "document.body.innerText.includes('backfill(rows)'); }",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 11",
         "title": "Migrate with muscle.",
         "subtitle": "backfill.py executes the function -- data alone earns nothing."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Plant one type-67 card (generated shape) as the sole due card."""
    con = sqlite3.connect(db_path)
    try:
        row = con.execute(
            "SELECT id FROM concepts ORDER BY rowid LIMIT 1").fetchone()
        if not row:
            return {"seeded": False, "reason": "no concepts"}
        con.execute("UPDATE cards SET due='2030-01-01T00:00:00Z'")
        con.execute("DELETE FROM reviews WHERE card_id=?", (CARD_ID,))
        con.execute(
            "INSERT OR REPLACE INTO cards(id, concept_id, exercise_type,"
            " front, back, payload, due)"
            " VALUES(?, ?, '67', ?, ?, ?, '2000-01-01T00:00:00Z')",
            (CARD_ID, row[0], FRONT, BACK, json.dumps(PAYLOAD)))
        con.commit()
        return {"seeded": True, "card_id": CARD_ID}
    finally:
        con.close()
