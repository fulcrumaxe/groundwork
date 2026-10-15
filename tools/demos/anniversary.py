"""Feature demo: year-in-review anniversary recaps (F-132).

Full behavior: history spanning a year+ earns one gentle recap on
History -- trailing-365-day attempts, active days/months, owned,
half-vs-half accuracy, top 3 modules. Private, no streaks; young
histories render exactly as before. seed_db backdates one review
past the 365-day gate and adds fresh attempts for the window.
"""
from __future__ import annotations

import sqlite3
from datetime import date, timedelta

SCENARIO = {
    "id": "anniversary",
    "kind": "feature",
    "batch": 25,
    "item": "F-132",
    "title": "Anniversary recaps",
    "blurb": "A year in? History shows your quiet year in review.",
    "beats": [
        {"type": "title", "duration": 4,
         "kicker": "Batch 25 - Feature F-132",
         "title": "Anniversary recaps",
         "subtitle": "Attempts, trend, most-revisited -- only you see it."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b25-anniversary",
         "caption": "Status names the gate: 365 days, then one recap.",
         "assert_js": "() => !!document.querySelector('#status-b25-anniversary') "
                      "&& document.body.innerText.includes('eligible()')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "Eligibility spans full history; stats window the year.",
         "commands": [
             ["python3", "-c",
              "from groundwork import anniversary as m; "
              "print('year old:', m.eligible('2025-01-01', '2026-10-15')); "
              "print('young:', m.eligible('2026-09-01', '2026-10-15')); "
              "r = m.summarize([{'reviewed_at': '2026-10-01', 'grade': 5, 'module': 'a'}], 2, '2026-10-15'); "
              "print('attempts:', r['attempts'], '| owned:', r['owned'])"],
         ]},
        {"type": "chrome", "duration": 10,
         "url_path": "/reviews",
         "focus": "#anniversary",
         "caption": "History earns its quiet anniversary: a year in review.",
         "assert_js": "() => !!document.querySelector('#anniversary') "
                      "&& document.body.innerText.includes('Your year in code comprehension')",
         "assert_want": "True"},
        {"type": "title", "duration": 4,
         "kicker": "Groundwork - Batch 25",
         "title": "A quiet anniversary.",
         "subtitle": "anniversary.py windows trailing-365 -- unearned, silent."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Backdate one review past the gate; add fresh window attempts."""
    con = sqlite3.connect(db_path)
    try:
        card = con.execute(
            "SELECT id FROM cards ORDER BY rowid LIMIT 1").fetchone()
        if not card:
            return {"seeded": False, "reason": "no cards"}
        today = date.today()
        old = (today - timedelta(days=400)).strftime("%Y-%m-%dT12:00:00Z")
        now = today.strftime("%Y-%m-%dT12:00:00Z")
        con.execute(
            "INSERT INTO reviews(card_id, grade, confidence, reviewed_at,"
            " submission) VALUES(?, 4, 3, ?, 'anniversary seed: old')",
            (card[0], old))
        for i in range(2):
            con.execute(
                "INSERT INTO reviews(card_id, grade, confidence, reviewed_at,"
                " submission) VALUES(?, 5, 4, ?, 'anniversary seed: fresh')",
                (card[0], now))
        con.commit()
        return {"seeded": True}
    finally:
        con.close()
