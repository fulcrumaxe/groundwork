"""Batch 1 improvement demo: due-why tooltips.

Full functionality: the Due queue's lead card carries a "why due?"
hover naming memory strength, days overdue, and lapse count -- one
shared builder (cards._due_why) over the card row. seed_db plants
known values (strength 4.5 days, 45 days overdue, 2 lapses) on the
due-first card; the interaction beat copies the real title attribute
into visible text (title tooltips do not photograph) and the assert
checks all three facts against the seed tokens.
"""
from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone

SCENARIO = {
    "id": "due-why",
    "kind": "improvement",
    "batch": 1,
    "item": "I-239",
    "title": "Due-why tooltips",
    "blurb": "Hover why-due: memory strength, days overdue, lapse count.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 1 - Improvement due-why",
         "title": "Due-why tooltips",
         "subtitle": "Hover why-due: memory strength, days overdue, lapse count."},
        {"type": "chrome", "duration": 8,
         "url_path": "/due",
         "focus": "article.next",
         "caption": "The lead card explains itself: why-due names strength, overdue, lapses.",
         "assert_js": "() => { const s = document.querySelector('#due-why'); "
                      "return (s && s.title) || 'missing'; }",
         "assert_want": "memory strength"},
        {"type": "chrome", "duration": 10,
         "url_path": "/due",
         "focus": "article.next",
         "caption": "The hover text, revealed: 45 days overdue, strength 4.5, 2 lapses.",
         "js": ["() => { const s = document.querySelector('#due-why'); "
                "if (!s) return 'why-missing'; "
                "s.textContent = 'why due? (' + s.title + ')'; return s.title; }"],
         "assert_js": "() => { const t = ((document.querySelector('#due-why') || {}).title || ''); "
                      "return (t.includes('{seed_overdue}d overdue') && t.includes('memory strength {seed_stability} days') && t.includes('lapses {seed_lapses}')) ? 'why-ok' : t; }",
         "assert_want": "why-ok"},
        {"type": "terminal", "duration": 6,
         "caption": "The builder: one shared tooltip from due date, stability, lapses.",
         "commands": [
             ["python3", "-c",
              "from datetime import datetime, timedelta, timezone; "
              "from groundwork.cards import _due_why; "
              "d = (datetime.now(timezone.utc) - timedelta(days=45)).strftime('%Y-%m-%dT%H:%M:%SZ'); "
              "print(_due_why({'due': d, 'stability': 4.5, 'lapses': 2}))"],
         ]},
        {"type": "terminal", "duration": 6,
         "caption": "The seeded row behind the tooltip: strength 4.5, 2 lapses.",
         "commands": [
             ["python3", "-c",
              "import os, sqlite3; con = sqlite3.connect(os.environ.get('DEMO_DB', 'groundwork.db')); "
              "print(con.execute(\"SELECT stability, lapses, due FROM cards WHERE id='{seed_card_id}'\").fetchone())"],
         ]},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 1",
         "title": "Overdue, explained.",
         "subtitle": "cards._due_why renders the scheduler's reasons on every lead card."},
    ],
}


def seed_db(db_path: str) -> dict:
    """One card due-first with known strength/overdue/lapses.

    Backdating 45 days keeps the tooltip story-readable ("45d
    overdue" -- a 2000-era date would print a 9000+ day count).
    """
    con = sqlite3.connect(db_path)
    try:
        card = con.execute(
            "SELECT id FROM cards ORDER BY due LIMIT 1").fetchone()
        if not card:
            return {"seeded": False, "reason": "no cards"}
        cid = card[0]
        # Minus 45d12h, not 45d: the Due queue's sleep-aware hook
        # (sleepsched.defer_night_new) pushes NEW cards due in quiet
        # hours (22-07 UTC) forward to 07:00 -- up to +9h. The 12h
        # cushion keeps elapsed in [45d3h, 45d12h], so .days is 45
        # whether or not the hook fires.
        due = (datetime.now(timezone.utc) - timedelta(days=45, hours=12)
               ).strftime("%Y-%m-%dT%H:%M:%SZ")
        con.execute("UPDATE cards SET due=?, stability=4.5, lapses=2"
                    " WHERE id=?", (due, cid))
        # 45 days is NOT older than the library's real dues, so push
        # every other card out of the queue: the seeded card must be
        # the undisputed lead card that wears #due-why.
        con.execute("UPDATE cards SET due='2030-01-01T00:00:00Z'"
                    " WHERE id != ?", (cid,))
        con.commit()
        return {"seeded": True, "card_id": cid, "overdue": 45,
                "stability": "4.5", "lapses": 2}
    finally:
        con.close()
