"""Feature demo: flow detection (F-95).

Full behavior: a window of fast accurate attempts (accuracy >=80%, median
pace <=45s) extends the Due session by up to 3 bonus cards. seed_db plants
six 20s-apart passing reviews; the caller beat reads them back through the
same Row-shaped query the Due page uses.
"""
from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone

SCENARIO = {
    "id": "flowdetect",
    "kind": "feature",
    "batch": 21,
    "item": "F-95",
    "title": "Flow detection",
    "blurb": "Nailing cards quickly? The session stretches a little -- bonus cards.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 21 - Feature F-95",
         "title": "Flow detection",
         "subtitle": "Fast plus accurate earns a longer session -- up to 3 bonus cards."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b21-flowdetect",
         "caption": "Status documents the gate: accuracy plus pace, both required.",
         "assert_js": "() => !!document.querySelector('#status-b21-flowdetect')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 9,
         "caption": "The rule in one line: fast and accurate extends; slow or sloppy stands.",
         "commands": [
             ["python3", "-c",
              "from groundwork import flowdetect as m; "
              "hot = [{'grade': 5, 'secs': 20.0}] * 4 + [{'grade': 4, 'secs': 25.0}]; "
              "slow = [{'grade': 5, 'secs': 120.0}] * 5; "
              "print('hot:', m.describe(hot), '| bonus:', m.bonus_count(hot)); "
              "print('slow:', m.describe(slow), '| bonus:', m.bonus_count(slow))"],
         ]},
        {"type": "terminal", "duration": 11,
         "caption": "The live fixture reads in-flow, and the session plan grows by three.",
         "commands": [
             ["python3", "-c",
              "import os; "
              "from groundwork import db as dbmod, flowdetect as m, minisession as ms; "
              "db = os.environ.get('DEMO_DB', 'groundwork.db'); "
              "con = dbmod.connect(db); "
              "rows = con.execute('SELECT grade, reviewed_at FROM reviews"
              " ORDER BY id DESC LIMIT 6').fetchall(); "
              "due = [dict(r) for r in con.execute('SELECT id, due FROM cards')]; "
              "con.close(); "
              "atts = m.attempts_with_pace(rows); "
              "print('gate:', m.describe(atts)); "
              "picks = ms.pick_cards(due, minutes=2, estimate_fn=lambda c: 60); "
              "grown = m.extend_session(picks, due, atts); "
              "print('planned:', len(picks), '-> in flow:', len(grown))"],
         ]},
        {"type": "chrome", "duration": 6,
         "url_path": "/due",
         "focus": "#minisession",
         "caption": "The Due session box carries the extended plan.",
         "assert_js": "() => { const b = document.querySelector('#minisession'); "
                      "return !!b && b.innerText.includes('About'); }",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 21",
         "title": "Ride the hot streak.",
         "subtitle": "flowdetect.py extends sessions -- calm plans stand untouched."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Plant six 20s-apart passing reviews: a hot streak with pace."""
    con = sqlite3.connect(db_path)
    try:
        cards = con.execute(
            "SELECT id FROM cards WHERE id NOT IN"
            " (SELECT card_id FROM reviews) LIMIT 6").fetchall()
        if len(cards) < 6:
            return {"seeded": False, "reason": "too few new cards"}
        base = datetime.now(timezone.utc) - timedelta(seconds=100)
        for i, (cid,) in enumerate(cards):
            stamp = (base + timedelta(seconds=20 * i)).strftime(
                "%Y-%m-%dT%H:%M:%SZ")
            con.execute(
                "INSERT INTO reviews(card_id, grade, confidence,"
                " reviewed_at, submission)"
                " VALUES(?, ?, 4, ?, 'flowdetect seed')",
                (cid, 4 if i == 2 else 5, stamp))
        con.commit()
        return {"seeded": True, "streak": len(cards)}
    finally:
        con.close()
