"""Feature demo: review-log CSV export (Batch 2, I-231).

Full functionality: /export/reviews.csv dumps every attempt with
grades, confidence, a derived pass column, and answers -- quoted
properly when submissions hold commas or quotes. seed_db wipes
reviews and plants three attempts (Paris / "Lyon, old town" /
'say "hi"'), so the beats assert the header, the quoting, and the
pass derivation on real rows.
"""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone

SCENARIO = {
    "id": "reviews-csv",
    "kind": "feature",
    "batch": 2,
    "item": "I-231",
    "title": "Review-log CSV export",
    "blurb": "Every attempt as CSV for personal analysis \u2014 grades, confidence, answers.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 2 - Feature I-231",
         "title": "Review-log CSV export",
         "subtitle": "Every attempt as CSV for personal analysis -- grades, confidence, answers."},
        {"type": "chrome", "duration": 7,
         "url_path": "/status",
         "focus": "#status-exports",
         "caption": "Status links the review-log CSV beside the Anki and RSS exports.",
         "assert_js": "() => !!document.querySelector("
                      "\"#status-csv a[href='/export/reviews.csv']\")",
         "assert_want": "True"},
        {"type": "terminal", "duration": 12,
         "caption": "The generator, called directly: header plus one row per attempt.",
         "commands": [
             ["python3", "-c",
              "import os; from groundwork import exports as e; "
              "print(e.reviews_csv(os.environ.get('DEMO_DB', 'groundwork.db')).strip())"],
             ["python3", "-c",
              "import csv, io, os; from groundwork import exports as e; "
              "rows = list(csv.reader(io.StringIO(e.reviews_csv(os.environ.get('DEMO_DB', 'groundwork.db'))))); "
              "print('rows:', len(rows) - 1); "
              "[print(' grade', r[3], '-> pass', r[5], '|', r[6][:24]) for r in rows[1:]]"],
         ]},
        {"type": "chrome", "duration": 9,
         "url_path": "/reviews",
         "focus": "#attempts",
         "caption": "The attempts behind the rows: the same three reviews on History.",
         "assert_js": "() => String(document.querySelectorAll("
                      "'main p.ok, main p.stale').length)",
         "assert_want": "3"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 2",
         "title": "Your log, portable.",
         "subtitle": "exports.py dumps every attempt as CSV for personal analysis."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Three attempts with CSV-tricky submissions (comma, quotes).

    Wiping reviews pins the row count at three (the served library DB
    holds one older review). Grades 5/2/4 exercise both pass values.
    """
    con = sqlite3.connect(db_path)
    try:
        cards = con.execute(
            "SELECT id FROM cards ORDER BY due LIMIT 3").fetchall()
        if len(cards) < 3:
            return {"seeded": False, "reason": "need 3 cards"}
        con.execute("DELETE FROM reviews")
        now = datetime.now(timezone.utc).replace(microsecond=0)
        iso = now.strftime("%Y-%m-%dT%H:%M:%SZ")
        subs = ["Paris", "Lyon, old town", 'say "hi"']
        for i, (card, sub, grade) in enumerate(
                zip([c[0] for c in cards], subs, [5, 2, 4])):
            con.execute(
                "INSERT INTO reviews(card_id, grade, confidence,"
                " reviewed_at, submission) VALUES(?, ?, ?, ?, ?)",
                (card, grade, 3, iso, sub))
        con.commit()
        return {"seeded": True, "rows": 3}
    finally:
        con.close()
