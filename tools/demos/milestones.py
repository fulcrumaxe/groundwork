"""Feature demo: milestone moments (F-107).

Full behavior: History dates First Owned, the 10th practiced module,
and full repo coverage from the existing tables — achieved ones only,
oldest-first, the rest unwritten. seed_db plants the two passing
reviews that write the First Owned milestone.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone

MODULE_ID = "demo-miles-107"
NODE = "demo/miles.py:first"
CID = f"{MODULE_ID}:{NODE}"
CARD_ID = "demo-miles-card"
FIRST_PASS = "2026-03-01T09:00:00Z"
OWNED_DAY = "2026-03-04T09:00:00Z"

SCENARIO = {
    "id": "milestones",
    "kind": "feature",
    "batch": 22,
    "item": "F-107",
    "title": "Milestone moments",
    "blurb": "First Owned, tenth module, full coverage — the dates that mattered.",
    "beats": [
        {"type": "title", "duration": 4,
         "kicker": "Batch 22 - Feature F-107",
         "title": "Milestone moments",
         "subtitle": "Calm, streak-free milestones -- dated from tables you already have."},
        {"type": "chrome", "duration": 9,
         "url_path": "/reviews",
         "focus": "#milestones",
         "caption": "The second passing review writes the First Owned milestone.",
         "assert_js": "() => document.body.textContent.includes('First concept owned')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 8,
         "caption": "Moments oldest-first; unreachable ones stay unwritten, never greyed.",
         "commands": [
             ["python3", "-c",
              "import os; from groundwork import milestones as m; "
              "db = os.environ.get('DEMO_DB', 'groundwork.db'); "
              "print('owned dates:', m.owned_dates(db)); "
              "[print(x['kind'], '|', x['label'], '|', x['when'][:10]) for x in m.moments(db)]; "
              "print('tenth needs:', m.TENTH_MODULE_N, 'modules; have:', len(m.module_first_dates(db)))"],
         ]},
        {"type": "chrome", "duration": 7,
         "url_path": "/status",
         "focus": "#status-b22-milestones",
         "caption": "Status documents the three milestone kinds.",
         "assert_js": "() => !!document.querySelector('#status-b22-milestones')",
         "assert_want": "True"},
        {"type": "title", "duration": 4,
         "kicker": "Groundwork - Batch 22",
         "title": "Dates that mattered.",
         "subtitle": "milestones.py writes achieved moments -- nothing greyed, nothing streaky."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Plant the two passing reviews that date First Owned."""
    con = sqlite3.connect(db_path)
    try:
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        con.execute("DELETE FROM reviews WHERE card_id=?", (CARD_ID,))
        con.execute("DELETE FROM cards WHERE id=?", (CARD_ID,))
        con.execute("DELETE FROM concepts WHERE module_id=?", (MODULE_ID,))
        con.execute("DELETE FROM modules WHERE id=?", (MODULE_ID,))
        lessons = [
            {"concept_id": NODE, "name": "First",
             "kind": "function", "file": "demo/miles.py", "line": 1,
             "summary": "The first owned concept."},
        ]
        con.execute(
            "INSERT INTO modules(id, repo, task_summary, created_at, lessons)"
            " VALUES(?, ?, ?, ?, ?)",
            (MODULE_ID, "demo/milestones", "Milestones module", now,
             json.dumps(lessons)))
        con.execute(
            "INSERT INTO concepts(id, module_id, name, kind, file,"
            " line, mastery) VALUES(?, ?, ?, ?, ?, ?, ?)",
            (CID, MODULE_ID, "First", "function",
             "demo/miles.py", 1, 0.0))
        con.execute(
            "INSERT INTO cards(id, concept_id, exercise_type, front, back, due)"
            " VALUES(?, ?, '19', ?, ?, ?)",
            (CARD_ID, CID, "Refactor this first?", "Done.",
             "2001-01-01T12:00:00Z"))
        for when in (FIRST_PASS, OWNED_DAY):
            con.execute(
                "INSERT INTO reviews(card_id, grade, confidence, reviewed_at,"
                " submission) VALUES(?, 5, 4, ?, 'milestones seed')",
                (CARD_ID, when))
        con.commit()
        return {"seeded": True, "card_id": CARD_ID,
                "owned_day": OWNED_DAY[:10]}
    finally:
        con.close()
