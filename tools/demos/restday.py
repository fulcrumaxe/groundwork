"""Feature demo: rest-day affirmations (F-122).

Full behavior: an empty Due queue after >= 1 idle day shows one
quiet consolidation sentence; busy queues and fresh learners see
nothing new. seed_db empties the queue and backdates reviews 1 day.
"""
from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone

SCENARIO = {
    "id": "restday",
    "kind": "feature",
    "batch": 24,
    "item": "F-122",
    "title": "Rest-day affirmations",
    "blurb": "Empty queue after time away: rest is consolidation.",
    "beats": [
        {"type": "title", "duration": 4,
         "kicker": "Batch 24 - Feature F-122",
         "title": "Rest-day affirmations",
         "subtitle": "A break reads as consolidation -- not failure."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b24-restday",
         "caption": "Status frames the break: one quiet sentence, no streaks.",
         "assert_js": "() => !!document.querySelector('#status-b24-restday')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "Empty plus idle affirms; busy or fresh stays silent.",
         "commands": [
             ["python3", "-c",
              "from groundwork import restday as m; "
              "print('rest:', m.is_rest_day(0, 2), '| busy:', m.is_rest_day(3, 2)); "
              "print(m.affirmation_for(0, 1)); "
              "print('silent:', repr(m.restday_html(3, 2)))"],
         ]},
        {"type": "chrome", "duration": 10,
         "url_path": "/due",
         "focus": "#rest-day",
         "caption": "The empty queue greets one idle day with one calm line.",
         "assert_js": "() => !!document.querySelector('#rest-day') "
                      "&& document.body.innerText.includes('Rest day')",
         "assert_want": "True"},
        {"type": "title", "duration": 4,
         "kicker": "Groundwork - Batch 24",
         "title": "Rest is part of it.",
         "subtitle": "restday.py affirms the pause -- then you return."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Empty the queue; backdate every review 1 day so idle=1."""
    con = sqlite3.connect(db_path)
    try:
        con.execute("UPDATE cards SET due='2030-01-01T00:00:00Z'")
        stamp = (datetime.now(timezone.utc) - timedelta(days=1)).strftime(
            "%Y-%m-%dT%H:%M:%SZ")
        cur = con.execute("UPDATE reviews SET reviewed_at=?", (stamp,))
        if cur.rowcount == 0:
            row = con.execute(
                "SELECT id FROM cards ORDER BY rowid LIMIT 1").fetchone()
            if row:
                con.execute(
                    "INSERT INTO reviews(card_id, grade, confidence,"
                    " reviewed_at, submission) VALUES(?, 4, 3, ?, 'restday seed')",
                    (row[0], stamp))
        con.commit()
        return {"seeded": True, "idle_days": 1}
    finally:
        con.close()
