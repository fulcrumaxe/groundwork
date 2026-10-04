"""Improvement demo: session-end summary (I-47).

Full functionality: session.summarize() turns today's review rows into
answered/accuracy/next-due, and the empty Due queue renders it as the
all-caught-up hero (web._hero_stats -> donehero.done_hero_html).
seed_db empties the queue (all dues to a fixed future stamp) and plants
four of today's reviews with grades 5/4/3/2, so the hero reads "4
answered today - 50% accuracy - next due 2026-11-01T07:00:00Z".
"""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone

NEXT_DUE = "2026-11-01T07:00:00Z"

SCENARIO = {
    "id": "session",
    "kind": "improvement",
    "batch": 5,
    "item": "I-47",
    "title": "Session-end summary",
    "blurb": "Answered, accuracy and what returns when -- the 5-minute debrief.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 5 - Improvement I-47",
         "title": "Session-end summary",
         "subtitle": "Answered, accuracy, next due -- the 5-minute debrief."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b5-session",
         "caption": "Status documents the item with its live anchor.",
         "assert_js": "() => !!document.querySelector('#status-b5-session')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "The rule in one line: grade >= 4 counts correct; earliest due wins.",
         "commands": [
             ["python3", "-c",
              "from groundwork import session as m; "
              "rows = [{'grade': 5}, {'grade': 4}, {'grade': 3}, {'grade': 2}]; "
              "print(m.summarize(rows))"],
         ]},
        {"type": "chrome", "duration": 12,
         "url_path": "/due",
         "focus": "#done-hero",
         "caption": "Queue empty, session debriefed: 4 answered, 50% accuracy, next due shown.",
         "assert_js": "() => document.querySelector('#done-hero').innerText",
         "assert_want": "4 answered today"},
        {"type": "terminal", "duration": 6,
         "caption": "Proof in the fixture DB: four of today's grades plus the pushed dues.",
         "commands": [
             ["python3", "-c",
              "import os, sqlite3; con = sqlite3.connect(os.environ.get('DEMO_DB', 'groundwork.db')); "
              "print('grades:', [r[0] for r in con.execute(\"SELECT grade FROM reviews ORDER BY id\")]); "
              "print('min due:', con.execute('SELECT MIN(due) FROM cards').fetchone()[0])"],
         ]},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 5",
         "title": "Debriefed, not just done.",
         "subtitle": "session.py summarizes -- the empty queue renders the hero."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Empty the queue and plant four of today's reviews (grades 5/4/3/2).

    All cards move to one fixed future due stamp so MIN(due) is exact
    and the Due queue renders the done hero; the four seeded reviews
    carry today's UTC date so _hero_stats counts them.
    """
    con = sqlite3.connect(db_path)
    try:
        cards = con.execute(
            "SELECT id FROM cards ORDER BY id LIMIT 4").fetchall()
        if len(cards) < 4:
            return {"seeded": False, "reason": "need 4 cards"}
        con.execute("UPDATE cards SET due=?", (NEXT_DUE,))
        con.execute("DELETE FROM reviews")
        today = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        for (cid,), grade in zip(cards, (5, 4, 3, 2)):
            con.execute(
                "INSERT INTO reviews(card_id, grade, confidence, reviewed_at,"
                " submission) VALUES(?, ?, 3, ?, 'session seed')",
                (cid, grade, today))
        con.commit()
        return {"seeded": True, "grades": [5, 4, 3, 2],
                "next_due": NEXT_DUE}
    finally:
        con.close()
