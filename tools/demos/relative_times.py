"""Improvement demo: relative timestamps (Batch 2, I-25).

Full functionality: History attempt times render as relative bodies
("just now", "3h ago", "2d ago", absolute past a week) inside <time>
elements whose title carries the exact instant plus zone. seed_db
wipes reviews and plants four attempts from 20 seconds to 10 days
old; the beats film the attempt stamps, stamp the same instants
through tztime, and reveal one hover tooltip visibly.
"""
from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone

SCENARIO = {
    "id": "relative-times",
    "kind": "improvement",
    "batch": 2,
    "item": "I-25",
    "title": "Relative timestamps",
    "blurb": "History reads as \u201cjust now\u201d and \u201c3h ago\u201d \u2014 hover any time for the exact timestamp.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 2 - Improvement I-25",
         "title": "Relative timestamps",
         "subtitle": "History reads as just now and 3h ago -- hover any time for the exact timestamp."},
        {"type": "chrome", "duration": 9,
         "url_path": "/reviews",
         "focus": "#timestamps",
         "caption": "Attempt times render relative; every stamp keeps its exact instant on hover.",
         "assert_js": "() => { const ts = Array.prototype.map.call("
                      "document.querySelectorAll('main time'), "
                      "function (t) { return t.textContent; }); "
                      "return ts.length + ':' + ts.join('|'); }",
         "assert_want": "4:just now"},
        {"type": "terminal", "duration": 9,
         "caption": "Same four instants through tztime: relative bodies, exact tooltips.",
         "commands": [
             ["python3", "-c",
              "import os, sqlite3; from groundwork import tztime as t; "
              "con = sqlite3.connect(os.environ.get('DEMO_DB', 'groundwork.db')); "
              "rows = con.execute('SELECT reviewed_at FROM reviews ORDER BY reviewed_at DESC').fetchall(); "
              "print(len(rows), 'seeded attempts:'); "
              "[print(' ', t.stamp_html(r[0])) for r in rows]"],
         ]},
        {"type": "chrome", "duration": 8,
         "url_path": "/reviews",
         "focus": "#tip-reveal",
         "caption": "Hover content, revealed: the exact instant plus its zone.",
         "js": ["() => { const t = document.querySelector('main p.ok time, main p.stale time'); "
                "if (!t) return 'no-stamp'; "
                "const p = document.createElement('p'); p.id = 'tip-reveal'; "
                "p.innerHTML = '<small>hover shows: <code>' + t.title + '</code></small>'; "
                "t.closest('p').before(p); return 'revealed'; }"],
         "assert_js": "() => { const p = document.querySelector('#tip-reveal'); "
                      "return p ? p.textContent : 'missing'; }",
         "assert_want": "(UTC)"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 2",
         "title": "Relative at a glance, exact on hover.",
         "subtitle": "tztime.py stamps every attempt as <time> with a UTC tooltip."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Four attempts from 20 seconds to 10 days old, oldest inserted first.

    Wiping reviews keeps the stamp count exact (the served library DB
    holds one older review). Insertion oldest-first makes the newest
    attempt render first (rows order by reviews.id DESC).
    """
    con = sqlite3.connect(db_path)
    try:
        cards = con.execute(
            "SELECT id FROM cards ORDER BY due LIMIT 4").fetchall()
        if len(cards) < 4:
            return {"seeded": False, "reason": "need 4 cards"}
        con.execute("DELETE FROM reviews")
        now = datetime.now(timezone.utc).replace(microsecond=0)
        ages = [timedelta(days=10), timedelta(days=2),
                timedelta(hours=3), timedelta(seconds=20)]
        stamps = []
        for i, age in enumerate(ages):
            iso = (now - age).strftime("%Y-%m-%dT%H:%M:%SZ")
            stamps.append(iso)
            con.execute(
                "INSERT INTO reviews(card_id, grade, confidence,"
                " reviewed_at, submission) VALUES(?, ?, ?, ?, ?)",
                (cards[i][0], [5, 3, 4, 5][i], 3, iso,
                 f"relseed{i}"))
        con.commit()
        return {"seeded": True, "stamps": stamps}
    finally:
        con.close()
