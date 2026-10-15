"""Feature demo: classroom quests via ?quest= spec (F-130).

Full behavior: a teacher spec (title + ordered concept names) rides
the ?quest= module link; completion derives from owned/mastery
already in the DB. seed_db owns the first concept of the first
module (two passing reviews on an ownership-type card) and builds
a two-step quest spec naming two real concepts.
"""
from __future__ import annotations

import json
import sqlite3
from urllib.parse import quote

CARD_ID = "demo-classquests-130"

SCENARIO = {
    "id": "classquests",
    "kind": "feature",
    "batch": 25,
    "item": "F-130",
    "title": "Classroom quests",
    "blurb": "Teacher checklists graded by what you already own.",
    "beats": [
        {"type": "title", "duration": 4,
         "kicker": "Batch 25 - Feature F-130",
         "title": "Classroom quests",
         "subtitle": "A spec in the link -- complete, never ranked."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b25-classquests",
         "caption": "Status renders a live demo quest beside the contract.",
         "assert_js": "() => !!document.querySelector('#status-b25-classquests') "
                      "&& !!document.querySelector('#classquests')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "Blanks and dupes drop; owned steps complete in order.",
         "commands": [
             ["python3", "-c",
              "from groundwork import classquests as m; "
              "v = m.quest_view({'title': 'Week 3', 'steps': ['Read', 'Grade', 'Read', '']}, owned={'Read'}); "
              "print(v['done'], 'of', v['total'], '| next:', v['next']); "
              "print('garbage:', m.parse_spec('nope'))"],
         ]},
        {"type": "chrome", "duration": 10,
         "url_path": "/modules/{seed_module}?quest={seed_quest}",
         "focus": "#classquests",
         "caption": "The quest link: one owned step done, one still to go.",
         "assert_js": "() => !!document.querySelector('#classquests') "
                      "&& document.body.innerText.includes('1 of 2 steps complete')",
         "assert_want": "True"},
        {"type": "title", "duration": 4,
         "kicker": "Groundwork - Batch 25",
         "title": "Teach the checklist.",
         "subtitle": "classquests.py derives done from owned -- no tables."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Own concept one of module one; build a two-step quest spec."""
    con = sqlite3.connect(db_path)
    try:
        mod = con.execute(
            "SELECT id FROM modules ORDER BY rowid LIMIT 1").fetchone()
        if not mod:
            return {"seeded": False, "reason": "no modules"}
        mid = mod[0]
        rows = con.execute(
            "SELECT id, name FROM concepts WHERE module_id=?"
            " ORDER BY rowid LIMIT 2", (mid,)).fetchall()
        if len(rows) < 2:
            return {"seeded": False, "reason": "module needs 2 concepts"}
        (c1, n1), (_c2, n2) = rows[0], rows[1]
        con.execute("DELETE FROM reviews WHERE card_id=?", (CARD_ID,))
        con.execute(
            "INSERT OR REPLACE INTO cards(id, concept_id, exercise_type,"
            " front, back, payload, due)"
            " VALUES(?, ?, '24', ?, ?, ?, '2030-01-01T00:00:00Z')",
            (CARD_ID, c1, "Design a quest step.", "Done.",
             json.dumps({})))
        for i in range(2):
            when = f"2026-10-0{i + 1}T12:00:00Z"
            con.execute(
                "INSERT INTO reviews(card_id, grade, confidence,"
                " reviewed_at, submission) VALUES(?, 5, 4, ?,"
                " 'quest seed pass')",
                (CARD_ID, when))
        con.commit()
        spec = {"format": "groundwork-quest/1", "title": "Demo quest",
                "steps": [n1, n2]}
        return {"seeded": True, "module": mid,
                "quest": quote(json.dumps(spec), safe="")}
    finally:
        con.close()
