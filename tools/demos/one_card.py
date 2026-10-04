"""Feature demo: just-one-card mode (Batch 4, F-121).

Full functionality: /due?mode=one shows a single card with a no-guilt
note for low-energy days. seed_db stages three due cards, so the mode
must show exactly one while the full queue shows all three.
"""
from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone

SCENARIO = {
    "id": "one-card",
    "kind": "feature",
    "batch": 4,
    "item": "F-121",
    "title": "Just-one-card mode",
    "blurb": "Low energy? Answer a single card -- no guilt design.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 4 - Feature F-121",
         "title": "Just-one-card mode",
         "subtitle": "Low energy? Answer a single card -- no guilt design."},
        {"type": "chrome", "duration": 7,
         "url_path": "/due",
         "caption": "The full queue offers just one card for low-energy days.",
         "assert_js": "() => { const a = document.querySelector('#one-card'); "
                      "return a ? a.getAttribute('href') : 'missing'; }",
         "assert_want": "/due?mode=one"},
        {"type": "chrome", "duration": 10,
         "url_path": "/due?mode=one",
         "focus": "#one-card-note",
         "caption": "One card is enough today -- no guilt, full queue one click away.",
         "assert_js": "() => !!document.querySelector('#one-card-note') + '|' + "
                      "document.querySelectorAll('main article').length",
         "assert_want": "true|1"},
        {"type": "terminal", "duration": 6,
         "caption": "Three due in the fixture; the mode shows exactly one.",
         "commands": [
             ["python3", "-c",
              "import os, sqlite3; "
              "con = sqlite3.connect(os.environ.get('DEMO_DB', 'groundwork.db')); "
              "n = con.execute(\"SELECT COUNT(*) FROM cards WHERE due < '2999-01-01T00:00:00Z' AND stale = 0\").fetchone()[0]; "
              "print('due in fixture:', n); print('mode=one shows: 1')"],
         ]},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 4",
         "title": "One card is enough.",
         "subtitle": "due_html slices the queue to one card with a no-guilt note."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Three attempted cards due now; the rest parked.

    Attempted seeds are sleep-hook-proof, so all three must render on
    the full queue while mode=one slices to exactly one.
    """
    con = sqlite3.connect(db_path)
    try:
        cards = con.execute(
            "SELECT id FROM cards WHERE stale = 0 ORDER BY due LIMIT 3"
            ).fetchall()
        if len(cards) < 3:
            return {"seeded": False, "reason": "need 3 live cards"}
        now = datetime.now(timezone.utc)
        stamp = (now - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
        con.execute("DELETE FROM reviews")
        con.execute("UPDATE cards SET due='2999-01-01T00:00:00Z'")
        for i, (cid,) in enumerate(cards):
            due = (now - timedelta(days=3 - i)).strftime(
                "%Y-%m-%dT%H:%M:%SZ")
            con.execute("UPDATE cards SET due=?, stability=1.0,"
                        " retrievability=0.9, lapses=0 WHERE id=?",
                        (due, cid))
            con.execute("INSERT INTO reviews(card_id, grade, confidence,"
                        " reviewed_at, submission) VALUES(?, 4, 3, ?, 'one seed')",
                        (cid, stamp))
        con.commit()
        return {"seeded": True, "cards": [c[0] for c in cards]}
    finally:
        con.close()
