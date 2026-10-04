"""Feature demo: week in review (Batch 2, I-243).

Full functionality: History's This-week section counts last-7-day
attempts, active days, and pass rate. seed_db wipes reviews and
plants six attempts across three days (grades 5,2 / 4,4 / 5,3), so
the section must read "6 attempts across 3 active days, 4 passed
(67%)" with six attempt rows behind it.
"""
from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone

SCENARIO = {
    "id": "week-review",
    "kind": "feature",
    "batch": 2,
    "item": "I-243",
    "title": "Week in review",
    "blurb": "Attempts, active days and pass rate for the last 7 days \u2014 a weekly ritual.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 2 - Feature I-243",
         "title": "Week in review",
         "subtitle": "Attempts, active days and pass rate for the last 7 days -- a weekly ritual."},
        {"type": "chrome", "duration": 12,
         "url_path": "/reviews",
         "focus": "#week",
         "caption": "This week: six attempts across three active days, four passed.",
         "assert_js": "() => { const h = document.querySelector('#week'); "
                      "const p = h ? h.nextElementSibling : null; "
                      "return p ? p.textContent : 'missing'; }",
         "assert_want": "6 attempts across 3 active days \u00b7 4 passed (67%)"},
        {"type": "chrome", "duration": 8,
         "url_path": "/reviews",
         "focus": "#attempts",
         "caption": "The attempts behind the numbers: six rows across three days.",
         "assert_js": "() => String(document.querySelectorAll("
                      "'main p.ok, main p.stale').length)",
         "assert_want": "6"},
        {"type": "terminal", "duration": 7,
         "caption": "Three active days in the log: the buckets behind the ritual.",
         "commands": [
             ["python3", "-c",
              "import os, sqlite3; "
              "con = sqlite3.connect(os.environ.get('DEMO_DB', 'groundwork.db')); "
              "rows = con.execute(\"SELECT substr(reviewed_at, 1, 10), COUNT(*), SUM(CASE WHEN grade >= 4 THEN 1 ELSE 0 END) FROM reviews GROUP BY 1 ORDER BY 1\").fetchall(); "
              "print('days:', len(rows)); "
              "[print(' ', r[0], 'attempts:', r[1], 'passed:', r[2]) for r in rows]"],
         ]},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 2",
         "title": "A weekly ritual.",
         "subtitle": "history.py buckets the last 7 days: attempts, days, pass rate."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Six attempts on three days: grades (5,2) / (4,4) / (5,3).

    Wiping reviews pins the counts exactly (the served library DB
    holds one older review). Day offsets 6/3/1 keep every row inside
    the 7-day window with one day of slack on each side.
    """
    con = sqlite3.connect(db_path)
    try:
        cards = con.execute(
            "SELECT id FROM cards ORDER BY due LIMIT 6").fetchall()
        if len(cards) < 6:
            return {"seeded": False, "reason": "need 6 cards"}
        con.execute("DELETE FROM reviews")
        now = datetime.now(timezone.utc).replace(microsecond=0)
        plan = [(6, 5), (6, 2), (3, 4), (3, 4), (1, 5), (1, 3)]
        days = []
        for i, (offset, grade) in enumerate(plan):
            # Noon UTC pins the calendar date: near-midnight runs
            # can't straddle into a fourth active day.
            day = (now - timedelta(days=offset)).replace(
                hour=12, minute=0) - timedelta(minutes=i)
            iso = day.strftime("%Y-%m-%dT%H:%M:%SZ")
            days.append(iso[:10])
            con.execute(
                "INSERT INTO reviews(card_id, grade, confidence,"
                " reviewed_at, submission) VALUES(?, ?, ?, ?, ?)",
                (cards[i][0], grade, 3, iso, f"weekseed{i}"))
        con.commit()
        return {"seeded": True, "days": sorted(set(days))}
    finally:
        con.close()
