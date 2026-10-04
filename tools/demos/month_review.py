"""Improvement demo: month in review (Batch 4, I-244).

Full functionality: History's This-month section counts last-30-day
attempts, active days, pass rate, and owned concepts, plus the
accuracy trend of the two halves. seed_db plants eight attempts --
25% in the first half, 75% in the second -- so both the totals and
the trend must read exactly.
"""
from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone

SCENARIO = {
    "id": "month-review",
    "kind": "improvement",
    "batch": 4,
    "item": "I-244",
    "title": "Month in review",
    "blurb": "Concepts owned, accuracy trend and effort across the last 30 days.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 4 - Improvement I-244",
         "title": "Month in review",
         "subtitle": "Concepts owned, accuracy trend and effort across the last 30 days."},
        {"type": "chrome", "duration": 11,
         "url_path": "/reviews",
         "focus": "#month",
         "caption": "This month: eight attempts across eight days, half passed.",
         "assert_js": "() => { const h = document.querySelector('#month'); "
                      "const p = h ? h.nextElementSibling : null; "
                      "return p ? p.textContent : 'missing'; }",
         "assert_want": "8 attempts across 8 active days \u00b7 4 passed (50%)"},
        {"type": "chrome", "duration": 7,
         "url_path": "/reviews",
         "focus": "#month",
         "caption": "The trend tells the story: 25% then, 75% now.",
         "assert_js": "() => { const h = document.querySelector('#month'); "
                      "const p = h ? h.nextElementSibling : null; "
                      "return p ? p.textContent : 'missing'; }",
         "assert_want": "Accuracy trend: 25% \u2192 75%"},
        {"type": "terminal", "duration": 7,
         "caption": "Two halves in the log: the buckets behind the trend.",
         "commands": [
             ["python3", "-c",
              "import os, sqlite3; from datetime import datetime, timedelta, timezone; "
              "con = sqlite3.connect(os.environ.get('DEMO_DB', 'groundwork.db')); "
              "now = datetime.now(timezone.utc); "
              "cuts = [(now - timedelta(days=d)).strftime('%Y-%m-%dT%H:%M:%SZ') for d in (30, 15, 0)]; "
              "halves = con.execute('SELECT SUM(CASE WHEN reviewed_at >= ? AND reviewed_at < ? THEN 1 ELSE 0 END), SUM(CASE WHEN reviewed_at >= ? AND reviewed_at < ? THEN grade >= 4 ELSE 0 END), SUM(CASE WHEN reviewed_at >= ? THEN 1 ELSE 0 END), SUM(CASE WHEN reviewed_at >= ? THEN grade >= 4 ELSE 0 END) FROM reviews', (cuts[0], cuts[1], cuts[0], cuts[1], cuts[1], cuts[1])).fetchone(); "
              "print('days -30..-15:', halves[0], 'attempts,', halves[1], 'passed'); "
              "print('days -15..today:', halves[2], 'attempts,', halves[3], 'passed')"],
         ]},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 4",
         "title": "A monthly ritual.",
         "subtitle": "monthreview.py buckets the last 30 days: effort, owned, trend."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Eight attempts: 1/4 passing early, 3/4 passing late.

    Offsets 25/24/20/16 land in days -30..-15, offsets 14/10/5/1 in
    -15..today, with noon pinning keeping every row clear of the
    half boundary (both window ends are inclusive).
    """
    con = sqlite3.connect(db_path)
    try:
        cards = con.execute(
            "SELECT id FROM cards ORDER BY due LIMIT 8").fetchall()
        if len(cards) < 8:
            return {"seeded": False, "reason": "need 8 cards"}
        con.execute("DELETE FROM reviews")
        now = datetime.now(timezone.utc).replace(microsecond=0)
        plan = [(25, 5), (24, 2), (20, 2), (16, 3),
                (14, 5), (10, 4), (5, 2), (1, 5)]
        days = []
        for i, (offset, grade) in enumerate(plan):
            day = (now - timedelta(days=offset)).replace(
                hour=12, minute=0) - timedelta(minutes=i)
            iso = day.strftime("%Y-%m-%dT%H:%M:%SZ")
            days.append(iso[:10])
            con.execute(
                "INSERT INTO reviews(card_id, grade, confidence,"
                " reviewed_at, submission) VALUES(?, ?, ?, ?, ?)",
                (cards[i][0], grade, 3, iso, f"monthseed{i}"))
        con.commit()
        return {"seeded": True, "days": sorted(set(days))}
    finally:
        con.close()
