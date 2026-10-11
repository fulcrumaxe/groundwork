"""Improvement demo: scrollable tables (I-92).

Full behavior: wide History log tables (calibration, coverage, last-14-days)
render inside a sideways-scroll container with the first column stuck, while
narrow tables and empty markup pass through unwrapped. seed_db plants reviews
across two days so all three wrapped tables have real rows to film.
"""
from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone

SCENARIO = {
    "id": "tablescroll",
    "kind": "improvement",
    "batch": 21,
    "item": "I-92",
    "title": "Scrollable tables",
    "blurb": "Wide tables pan sideways on phones with the first column stuck.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 21 - Improvement I-92",
         "title": "Scrollable tables",
         "subtitle": "Wide grids pan sideways -- row labels stay stuck at the left."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b21-tablescroll",
         "caption": "Status documents the fix: wrap plus sticky first column.",
         "assert_js": "() => !!document.querySelector('#status-b21-tablescroll')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 8,
         "caption": "The rule in one line: 3+ columns wrap, narrow and empty pass through.",
         "commands": [
             ["python3", "-c",
              "from groundwork import tablescroll as m; "
              "wide = '<table><tr><th>A</th><th>B</th><th>C</th><th>D</th></tr></table>'; "
              "narrow = '<table><tr><th>A</th><th>B</th></tr></table>'; "
              "print('cols:', m.column_count(wide), '| wrap:', m.wrap_table(wide)[:24]); "
              "print('narrow passthrough:', m.wrap_table(narrow) == narrow); "
              "print('empty passthrough:', repr(m.wrap_table(''))); "
              "print('css:', m.scroll_css()[:60])"],
         ]},
        {"type": "chrome", "duration": 11,
         "url_path": "/reviews",
         "focus": ".tscroll",
         "caption": "History log tables ride in scroll containers -- calibration, coverage, days.",
         "assert_js": "() => !!document.querySelector('.tscroll table.log')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 6,
         "caption": "Three wrapped tables on the live History path, fed by seeded reviews.",
         "commands": [
             ["python3", "-c",
              "import os; os.environ['GW_DB'] = os.environ.get('DEMO_DB', 'groundwork.db'); "
              "from groundwork import history; "
              "html = history.history_html(os.environ['GW_DB']); "
              "print('wrapped log tables:', html.count(chr(34) + 'tscroll' + chr(34))); "
              "import sqlite3; con = sqlite3.connect(os.environ['GW_DB']); "
              "print('review days:', con.execute('SELECT COUNT(DISTINCT substr(reviewed_at, 1, 10)) FROM reviews').fetchone()[0])"],
         ]},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 21",
         "title": "Pan, don't overflow.",
         "subtitle": "tablescroll.py wraps wide tables -- narrow ones stay untouched."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Plant reviews across two days so every History log table renders."""
    con = sqlite3.connect(db_path)
    try:
        cards = con.execute(
            "SELECT id FROM cards ORDER BY due LIMIT 6").fetchall()
        if len(cards) < 4:
            return {"seeded": False, "reason": "too few cards"}
        now = datetime.now(timezone.utc)
        stamps = [(now - timedelta(days=d)).strftime("%Y-%m-%dT%H:%M:%SZ")
                  for d in (0, 0, 0, 1, 1, 1)]
        for (cid,), stamp, grade in zip(cards, stamps, (5, 4, 2, 5, 3, 4)):
            con.execute(
                "INSERT INTO reviews(card_id, grade, confidence,"
                " reviewed_at, submission)"
                " VALUES(?, ?, 3, ?, 'tablescroll seed')",
                (cid, grade, stamp))
        con.commit()
        return {"seeded": True, "planted": len(cards)}
    finally:
        con.close()
