"""Feature demo: October Owntober seasonal event (F-131).

Full behavior: each October brings Owntober -- own 5 concepts whose
owned-date falls inside the month, counted from the existing tables
via milestones, no streaks. Outside October the section omits
itself. seed_db dates two owned concepts inside this October (the
2nd passing review dates ownership).
"""
from __future__ import annotations

import json
import sqlite3

CARD_IDS = ("demo-seasonevent-131a", "demo-seasonevent-131b")

SCENARIO = {
    "id": "seasonevent",
    "kind": "feature",
    "batch": 25,
    "item": "F-131",
    "title": "Owntober seasonal event",
    "blurb": "Each October: own 5 concepts. Gentle goal, no streak.",
    "beats": [
        {"type": "title", "duration": 4,
         "kicker": "Batch 25 - Feature F-131",
         "title": "Owntober seasonal event",
         "subtitle": "Five Octobers-owned concepts -- then the month ends."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b25-seasonevent",
         "caption": "Status states the window: October, goal of 5.",
         "assert_js": "() => !!document.querySelector('#status-b25-seasonevent') "
                      "&& document.body.innerText.includes('Owntober')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "In October it resolves; in November it is None.",
         "commands": [
             ["python3", "-c",
              "import os; from groundwork import seasonevent as m; "
              "print('oct:', m.current_event('2026-10-15')['title']); "
              "print('nov:', m.current_event('2026-11-01')); "
              "p = m.progress(os.environ.get('DEMO_DB', 'groundwork.db')); "
              "print('fixture:', p['owned'], 'of', p['goal'], '| done:', p['done'])"],
         ]},
        {"type": "chrome", "duration": 10,
         "url_path": "/reviews",
         "focus": "#seasonal-event",
         "caption": "History counts this October's owned concepts to 5.",
         "assert_js": "() => !!document.querySelector('#seasonal-event') "
                      "&& (document.body.innerText.includes('owned this October') "
                      "|| document.body.innerText.includes('Goal met'))",
         "assert_want": "True"},
        {"type": "title", "duration": 4,
         "kicker": "Groundwork - Batch 25",
         "title": "Seasonal, not streaky.",
         "subtitle": "seasonevent.py counts owned-dates -- out of season, silent."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Date two owned concepts inside this October."""
    con = sqlite3.connect(db_path)
    try:
        rows = con.execute(
            "SELECT id FROM concepts ORDER BY rowid LIMIT 2").fetchall()
        if len(rows) < 2:
            return {"seeded": False, "reason": "need 2 concepts"}
        for cid, when in zip(CARD_IDS, ("2026-10-05", "2026-10-10")):
            con.execute("DELETE FROM reviews WHERE card_id=?", (cid,))
        for (concept,), cid, when in zip(rows, CARD_IDS,
                                         ("2026-10-05", "2026-10-10")):
            con.execute(
                "INSERT OR REPLACE INTO cards(id, concept_id, exercise_type,"
                " front, back, payload, due)"
                " VALUES(?, ?, '24', ?, ?, ?, '2030-01-01T00:00:00Z')",
                (cid, concept, "Design a seasonal goal.", "Done.",
                 json.dumps({})))
            for day in (f"{when}T12:00:00Z", f"{when}T13:00:00Z"):
                con.execute(
                    "INSERT INTO reviews(card_id, grade, confidence,"
                    " reviewed_at, submission) VALUES(?, 5, 4, ?, 'season seed')",
                    (cid, day))
        con.commit()
        return {"seeded": True}
    finally:
        con.close()
