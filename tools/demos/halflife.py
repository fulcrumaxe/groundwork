"""Pilot feature demo: knowledge half-life (F-182).

Full functionality: per-concept half-life (9x mean stability) plus the
slipped-since-last-quarter list on History, with live counts on Status.
seed_db backdates one low-stability review 120 days so the report has
a real decayed row to show.
"""
from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone

SCENARIO = {
    "id": "halflife",
    "kind": "feature",
    "batch": 29,
    "item": "F-182",
    "title": "Knowledge half-life",
    "blurb": "What decayed since last quarter -- review time goes where it matters.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 29 - Feature F-182",
         "title": "Knowledge half-life",
         "subtitle": "What decayed since last quarter -- per-concept half-life plus the slipped list."},
        {"type": "terminal", "duration": 7,
         "caption": "Pure logic first: half-life is 9x stability; old low-recall cards flag decayed.",
         "commands": [
             ["python3", "-c",
              "from groundwork import halflife as m; "
              "print('half-life S=1.0:', m.half_life_days(1.0)); "
              "rows = [('closures', 1.0, '2025-05-01T00:00:00Z')]; "
              "print(m.summarize(rows, now='2025-09-29T00:00:00Z'))"],
         ]},
        {"type": "chrome", "duration": 7,
         "url_path": "/status#status-b29-halflife",
         "focus": "#status-b29-halflife",
         "caption": "Status carries the live counts: decayed of tracked, from your own reviews.",
         "assert_js": "() => !!document.querySelector('#status-b29-halflife')",
         "assert_want": "True"},
        {"type": "chrome", "duration": 10,
         "url_path": "/reviews#half-life",
         "focus": "#half-life",
         "caption": "History shows the slipped list -- concept, half-life, recall now, last seen.",
         "assert_js": "() => !!document.querySelector('#half-life')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 6,
         "caption": "The manipulated fixture: one review backdated past the quarter line.",
         "commands": [
             ["python3", "-c",
              "import os, sqlite3; con = sqlite3.connect(os.environ.get('DEMO_DB', 'groundwork.db')); "
              "row = con.execute('SELECT reviewed_at FROM reviews ORDER BY reviewed_at LIMIT 1').fetchone(); "
              "print('oldest review:', row[0] if row else None)"],
         ]},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 29",
         "title": "Review time goes here first.",
         "subtitle": "halflife.py renders on History -- silent until some review is a quarter old."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Backdate one low-stability review 120 days to force a decayed row."""
    con = sqlite3.connect(db_path)
    try:
        card = con.execute(
            "SELECT id FROM cards ORDER BY due LIMIT 1").fetchone()
        if not card:
            return {"seeded": False, "reason": "no cards"}
        cid = card[0]
        con.execute("UPDATE cards SET stability=1.0 WHERE id=?", (cid,))
        old = (datetime.now(timezone.utc) - timedelta(days=120)).strftime(
            "%Y-%m-%dT%H:%M:%SZ")
        con.execute("DELETE FROM reviews WHERE card_id=?", (cid,))
        con.execute(
            "INSERT INTO reviews(card_id, grade, confidence, reviewed_at, submission)"
            " VALUES(?, 2, 3, ?, 'half-life seed')", (cid, old))
        con.commit()
        return {"seeded": True, "card_id": cid, "reviewed_at": old}
    finally:
        con.close()
