"""Feature demo: skill endorsements from delayed tests (F-110).

Full behavior: a Bloom skill earns its endorsement the day a delayed
test proves it — a passing review at 21+ days stability — with proof
counts and latest dates, no peers consulted. seed_db plants two
delayed apply passes.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone

MODULE_ID = "demo-endorse-110"
NODE = "demo/endorse.py:predict"
CID = f"{MODULE_ID}:{NODE}"
CARD_ID = "demo-endorse-card"

SCENARIO = {
    "id": "endorse",
    "kind": "feature",
    "batch": 22,
    "item": "F-110",
    "title": "Skill endorsements",
    "blurb": "Endorsed by your own delayed tests — references from your future self.",
    "beats": [
        {"type": "title", "duration": 4,
         "kicker": "Batch 22 - Feature F-110",
         "title": "Skill endorsements",
         "subtitle": "No votes, no peers -- a delayed pass writes the reference."},
        {"type": "chrome", "duration": 10,
         "url_path": "/reviews",
         "focus": "#endorsements",
         "caption": "Apply endorses on two delayed proofs, latest date named.",
         "assert_js": "() => document.body.textContent.includes('Endorsed: apply') && document.body.textContent.includes('2 delayed proofs')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 8,
         "caption": "One row per delayed-proven skill: proofs counted, latest dated.",
         "commands": [
             ["python3", "-c",
              "import os; from groundwork import endorse as m; "
              "print('mature bar:', m.MATURE_DAYS, 'days'); "
              "[print(r['skill'], '| proofs:', r['proofs'], '| latest:', r['latest']) for r in m.endorsements(os.environ.get('DEMO_DB', 'groundwork.db'))]"],
         ]},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b22-endorse",
         "caption": "Status documents the delayed-test rule: no peers consulted.",
         "assert_js": "() => !!document.querySelector('#status-b22-endorse')",
         "assert_want": "True"},
        {"type": "title", "duration": 4,
         "kicker": "Groundwork - Batch 22",
         "title": "Future you vouches.",
         "subtitle": "endorse.py counts delayed passes -- one lucky recall reads as one."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Plant two delayed passing apply reviews (one endorsement)."""
    con = sqlite3.connect(db_path)
    try:
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        con.execute("DELETE FROM reviews WHERE card_id=?", (CARD_ID,))
        con.execute("DELETE FROM cards WHERE id=?", (CARD_ID,))
        con.execute("DELETE FROM concepts WHERE module_id=?", (MODULE_ID,))
        con.execute("DELETE FROM modules WHERE id=?", (MODULE_ID,))
        lessons = [
            {"concept_id": NODE, "name": "Predict",
             "kind": "function", "file": "demo/endorse.py", "line": 1,
             "summary": "Predictions that held up over delay."},
        ]
        con.execute(
            "INSERT INTO modules(id, repo, task_summary, created_at, lessons)"
            " VALUES(?, ?, ?, ?, ?)",
            (MODULE_ID, "demo/endorse", "Endorsements module", now,
             json.dumps(lessons)))
        con.execute(
            "INSERT INTO concepts(id, module_id, name, kind, file,"
            " line, mastery) VALUES(?, ?, ?, ?, ?, ?, ?)",
            (CID, MODULE_ID, "Predict", "function",
             "demo/endorse.py", 1, 0.0))
        con.execute(
            "INSERT INTO cards(id, concept_id, exercise_type, front, back, due)"
            " VALUES(?, ?, '8', ?, ?, ?)",
            (CARD_ID, CID, "Predict the output?", "42.",
             "2001-01-01T12:00:00Z"))
        for when, stab in (("2026-09-01T09:00:00Z", 30),
                           ("2026-09-20T09:00:00Z", 25)):
            con.execute(
                "INSERT INTO reviews(card_id, grade, confidence, reviewed_at,"
                " prev_stability, submission) VALUES(?, 5, 4, ?, ?, ?)",
                (CARD_ID, when, stab, "endorse seed"))
        con.commit()
        return {"seeded": True, "card_id": CARD_ID}
    finally:
        con.close()
