"""Improvement demo: one <time> stamp everywhere (I-93).

Full behavior: every human-visible date routes through timetag.stamp
— instants get relative bodies, calendar days keep short bodies, all
as machine-readable <time datetime> with hoverable exact values. The
History practice-days table is the live caller filmed here.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone

MODULE_ID = "demo-timetag-93"
NODE = "demo/stamp.py:unify"
CID = f"{MODULE_ID}:{NODE}"
CARD_ID = "demo-timetag-card"
DAY_A = "2026-10-09T09:00:00Z"
DAY_B = "2026-10-10T15:30:00Z"

SCENARIO = {
    "id": "timetag",
    "kind": "improvement",
    "batch": 22,
    "item": "I-93",
    "title": "One stamp everywhere",
    "blurb": "Every date on every page is a real <time> element — hover for exact.",
    "beats": [
        {"type": "title", "duration": 4,
         "kicker": "Batch 22 - Improvement I-93",
         "title": "One stamp everywhere",
         "subtitle": "One router for every date -- instants and days alike."},
        {"type": "chrome", "duration": 9,
         "url_path": "/reviews",
         "js": ["() => { const h = [...document.querySelectorAll('h2')].find(e => e.textContent.includes('Last 14')); if (h) h.id = 'seed-days'; return h ? 'marked' : 'missing'; }"],
         "focus": "#seed-days",
         "caption": "Practice days render through the one stamp router.",
         "assert_js": "() => !!document.querySelector('#seed-days') && !!document.querySelector('main time[datetime]')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 8,
         "caption": "The router: instants go relative, days stay short, blanks say unknown.",
         "commands": [
             ["python3", "-c",
              "from groundwork import timetag as m; "
              "print('instant:', m.stamp('2026-10-10T15:30:00Z')); "
              "print('day:    ', m.stamp('2026-01-05')); "
              "print('blank:  ', m.stamp('')); "
              "print('junk:   ', m.stamp('zzz'))"],
         ]},
        {"type": "chrome", "duration": 7,
         "url_path": "/status",
         "focus": "#status-b22-timetag",
         "caption": "Status documents the one-stamp rule with a live sample.",
         "assert_js": "() => !!document.querySelector('#status-b22-timetag') && !!document.querySelector('main time[datetime]')",
         "assert_want": "True"},
        {"type": "title", "duration": 4,
         "kicker": "Groundwork - Batch 22",
         "title": "No hand-rolled dates.",
         "subtitle": "timetag.py routes every stamp -- machine-readable, hoverable."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Plant reviews on two practice days for the days table."""
    con = sqlite3.connect(db_path)
    try:
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        con.execute("DELETE FROM reviews WHERE card_id=?", (CARD_ID,))
        con.execute("DELETE FROM cards WHERE id=?", (CARD_ID,))
        con.execute("DELETE FROM concepts WHERE module_id=?", (MODULE_ID,))
        con.execute("DELETE FROM modules WHERE id=?", (MODULE_ID,))
        lessons = [
            {"concept_id": NODE, "name": "Unify Stamps",
             "kind": "function", "file": "demo/stamp.py", "line": 1,
             "summary": "One stamp router."},
        ]
        con.execute(
            "INSERT INTO modules(id, repo, task_summary, created_at, lessons)"
            " VALUES(?, ?, ?, ?, ?)",
            (MODULE_ID, "demo/timetag", "One-stamp module", now,
             json.dumps(lessons)))
        con.execute(
            "INSERT INTO concepts(id, module_id, name, kind, file,"
            " line, mastery) VALUES(?, ?, ?, ?, ?, ?, ?)",
            (CID, MODULE_ID, "Unify Stamps", "function",
             "demo/stamp.py", 1, 0.0))
        con.execute(
            "INSERT INTO cards(id, concept_id, exercise_type, front, back, due)"
            " VALUES(?, ?, '1', ?, ?, ?)",
            (CARD_ID, CID, "One stamp?", "Yes.",
             "2001-01-01T12:00:00Z"))
        for when in (DAY_A, DAY_B):
            con.execute(
                "INSERT INTO reviews(card_id, grade, confidence, reviewed_at,"
                " submission) VALUES(?, 5, 4, ?, 'timetag seed')",
                (CARD_ID, when))
        con.commit()
        return {"seeded": True, "card_id": CARD_ID,
                "days": [DAY_A[:10], DAY_B[:10]]}
    finally:
        con.close()
