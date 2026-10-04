"""Demo: queue position (Batch 1 improvement).

Full functionality: every Due card numbers itself Card i of n
against the live due list while the lead card wears the Up-next
tag. seed_db backdates two cards due so the position line always
has a real denominator; the beats film the tag, the grouped queue,
and the one template line behind the numbers.
"""
from __future__ import annotations

import datetime
import sqlite3

SCENARIO = {
    "id": "queue-position",
    "kind": "improvement",
    "batch": 1,
    "item": "I-43",
    "title": "Queue position",
    "blurb": "Card i of n plus an Up-next tag on the first card.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 1 - Improvement queue-position",
         "title": "Queue position",
         "subtitle": "Card i of n plus an Up-next tag on the first card."},
        {"type": "chrome", "duration": 10,
         "url_path": "/due",
         "focus": "#up-next",
         "caption": "The lead card wears the Up-next tag with its queue number.",
         "assert_js": "() => document.body.innerText.includes('Up next') && document.body.innerText.includes('Card 1 of')",
         "assert_want": "True"},
        {"type": "chrome", "duration": 9,
         "url_path": "/due",
         "focus": "#queue-groups",
         "caption": "Cards group by module but number against the whole queue.",
         "assert_js": "() => !!document.querySelector('#queue-groups') && document.body.innerText.includes('Card 1 of')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 9,
         "caption": "The fixture holds {seed_due_total} due cards -- position is live, not stored.",
         "commands": [
             ["python3", "-c",
              "import os, sqlite3, datetime; con = sqlite3.connect(os.environ.get('DEMO_DB', 'groundwork.db')); "
              "now = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'); "
              "n = con.execute('SELECT COUNT(*) FROM cards WHERE due <= ? AND stale = 0', (now,)).fetchone()[0]; "
              "print('due in fixture:', n); print('lead card reads: Card 1 of', min(n, 20))"],
             ["bash", "-lc", "grep -n 'Card {i + 1} of {len(due)}' groundwork/web.py"],
         ]},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 1",
         "title": "Always know where you stand.",
         "subtitle": "One template line numbers every card over the live due list."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Backdate two cards due so the position line has a denominator.

    Picks the two earliest-due live cards; returns their ids plus the
    fixture-wide due total for caption tokens.
    """
    con = sqlite3.connect(db_path)
    try:
        rows = con.execute(
            "SELECT id FROM cards WHERE stale = 0 ORDER BY due LIMIT 2"
        ).fetchall()
        if not rows:
            return {"seeded": False, "reason": "no cards"}
        for (cid,) in rows:
            con.execute(
                "UPDATE cards SET due = '2000-01-01T00:00:00Z', stale = 0 WHERE id = ?",
                (cid,))
        con.commit()
        now = datetime.datetime.now(datetime.timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ")
        total = con.execute(
            "SELECT COUNT(*) FROM cards WHERE due <= ? AND stale = 0",
            (now,)).fetchone()[0]
        ids = [r[0] for r in rows]
        return {"seeded": True, "card_a": ids[0],
                "card_b": ids[1] if len(ids) > 1 else ids[0],
                "due_total": total}
    finally:
        con.close()
