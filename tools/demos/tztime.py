"""Improvement demo: timezone-explicit stamps (I-26).

Full behavior: History attempt rows and coverage dates render as
<time> elements with explicit-UTC title tooltips — relative bodies
("3h ago") for the fresh week, absolute "YYYY-MM-DD UTC" bodies past
it. seed_db plants one fresh and one old review so both shapes show.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta, timezone

MODULE_ID = "demo-tztime-26"
NODE = "demo/clock.py:stamp"
CID = f"{MODULE_ID}:{NODE}"
CARD_ID = "demo-tztime-card"
OLD_REVIEWED = "2025-06-01T12:00:00Z"

SCENARIO = {
    "id": "tztime",
    "kind": "improvement",
    "batch": 22,
    "item": "I-26",
    "title": "Timezone-explicit stamps",
    "blurb": "Every History stamp names its zone — hover for the exact UTC instant.",
    "beats": [
        {"type": "title", "duration": 4,
         "kicker": "Batch 22 - Improvement I-26",
         "title": "Timezone-explicit stamps",
         "subtitle": "Relative bodies, exact UTC tooltips -- no more guessing zones."},
        {"type": "chrome", "duration": 8,
         "url_path": "/reviews",
         "focus": "#attempts",
         "caption": "Attempt rows stamp relative times with exact-UTC hover titles.",
         "assert_js": "() => !!document.querySelector('time[title*=\"UTC\"]')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 9,
         "caption": "The rule: fresh stamps stay relative, old ones go absolute UTC.",
         "commands": [
             ["python3", "-c",
              "from groundwork import tztime as m; "
              "from datetime import datetime, timedelta, timezone; "
              "fresh = (datetime.now(timezone.utc) - timedelta(hours=3)).strftime('%Y-%m-%dT%H:%M:%SZ'); "
              "print('fresh:', m.stamp_html(fresh)); "
              "print('old:  ', m.stamp_html('2025-06-01T12:00:00Z')); "
              "print('day:  ', m.day_html('2026-01-05')); "
              "print('junk: ', m.stamp_html('not-a-date'))"],
         ]},
        {"type": "chrome", "duration": 8,
         "url_path": "/reviews",
         "focus": "#coverage",
         "caption": "Coverage dates carry midnight-UTC tooltips on the same page.",
         "assert_js": "() => document.querySelectorAll('time[datetime]').length > 5 ? 'stamped' : 'bare'",
         "assert_want": "stamped"},
        {"type": "title", "duration": 4,
         "kicker": "Groundwork - Batch 22",
         "title": "Hover any time.",
         "subtitle": "tztime.py stamps History -- relative, absolute, always zoned."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Plant one fresh and one old review for the two stamp shapes."""
    con = sqlite3.connect(db_path)
    try:
        fresh = (datetime.now(timezone.utc) - timedelta(hours=3)).strftime(
            "%Y-%m-%dT%H:%M:%SZ")
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        con.execute("DELETE FROM reviews WHERE card_id=?", (CARD_ID,))
        con.execute("DELETE FROM cards WHERE id=?", (CARD_ID,))
        con.execute("DELETE FROM concepts WHERE module_id=?", (MODULE_ID,))
        con.execute("DELETE FROM modules WHERE id=?", (MODULE_ID,))
        lessons = [
            {"concept_id": NODE, "name": "Clock Stamp",
             "kind": "function", "file": "demo/clock.py", "line": 1,
             "summary": "Stamp attempts with zones."},
        ]
        con.execute(
            "INSERT INTO modules(id, repo, task_summary, created_at, lessons)"
            " VALUES(?, ?, ?, ?, ?)",
            (MODULE_ID, "demo/tztime", "Timezone stamps module", now,
             json.dumps(lessons)))
        con.execute(
            "INSERT INTO concepts(id, module_id, name, kind, file,"
            " line, mastery) VALUES(?, ?, ?, ?, ?, ?, ?)",
            (CID, MODULE_ID, "Clock Stamp", "function",
             "demo/clock.py", 1, 0.0))
        con.execute(
            "INSERT INTO cards(id, concept_id, exercise_type, front, back, due)"
            " VALUES(?, ?, '1', ?, ?, ?)",
            (CARD_ID, CID, "What zone?", "UTC.",
             "2001-01-01T12:00:00Z"))
        con.execute(
            "INSERT INTO reviews(card_id, grade, confidence, reviewed_at,"
            " submission) VALUES(?, 5, 4, ?, 'tztime seed fresh')",
            (CARD_ID, fresh))
        con.execute(
            "INSERT INTO reviews(card_id, grade, confidence, reviewed_at,"
            " submission) VALUES(?, 4, 3, ?, 'tztime seed old')",
            (CARD_ID, OLD_REVIEWED))
        con.commit()
        return {"seeded": True, "card_id": CARD_ID, "fresh": fresh,
                "old": OLD_REVIEWED}
    finally:
        con.close()
