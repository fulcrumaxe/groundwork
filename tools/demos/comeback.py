"""Feature demo: comeback after 30 idle days (F-123).

Full behavior: at 30+ idle days the Due page shows one welcome-back
recap (days away, recent concepts, one-card next step); active
libraries see nothing. seed_db backdates reviews 40 days + 1 due card.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta, timezone

CARD_ID = "demo-comeback-123"

SCENARIO = {
    "id": "comeback",
    "kind": "feature",
    "batch": 24,
    "item": "F-123",
    "title": "Comeback after time away",
    "blurb": "Away 30 days? A gentle recap -- one card restarts.",
    "beats": [
        {"type": "title", "duration": 4,
         "kicker": "Batch 24 - Feature F-123",
         "title": "Comeback after time away",
         "subtitle": "No shame, no backlog -- one card restarts the loop."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b24-comeback",
         "caption": "Status names the gate: 30 idle days, kindly worded.",
         "assert_js": "() => !!document.querySelector('#status-b24-comeback')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "The gate counts idle days; the recap lists recent names.",
         "commands": [
             ["python3", "-c",
              "from groundwork import comeback as m; "
              "print('away40:', m.is_comeback('2000-01-01T00:00:00Z')); "
              "rows = [{'name': 'loops', 'reviewed_at': '2000-01-02T00:00:00Z'}]; "
              "print('recap:', m.recap_items(rows)); "
              "print(m.comeback_box_html(rows=rows)[:130])"],
         ]},
        {"type": "chrome", "duration": 10,
         "url_path": "/due",
         "focus": "#comeback",
         "caption": "Forty days away greets one welcome-back banner on Due.",
         "assert_js": "() => !!document.querySelector('#comeback') "
                      "&& document.body.innerText.includes('Welcome back')",
         "assert_want": "True"},
        {"type": "title", "duration": 4,
         "kicker": "Groundwork - Batch 24",
         "title": "Welcome back, gently.",
         "subtitle": "comeback.py recaps -- active queues see nothing."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Backdate every review 40 days; keep one card due for the queue."""
    con = sqlite3.connect(db_path)
    try:
        stamp = (datetime.now(timezone.utc) - timedelta(days=40)).strftime(
            "%Y-%m-%dT%H:%M:%SZ")
        con.execute("UPDATE reviews SET reviewed_at=?", (stamp,))
        row = con.execute(
            "SELECT id FROM concepts ORDER BY rowid LIMIT 1").fetchone()
        if not row:
            return {"seeded": False, "reason": "no concepts"}
        con.execute("UPDATE cards SET due='2030-01-01T00:00:00Z'")
        con.execute("DELETE FROM reviews WHERE card_id=?", (CARD_ID,))
        con.execute(
            "INSERT OR REPLACE INTO cards(id, concept_id, exercise_type,"
            " front, back, payload, due)"
            " VALUES(?, ?, '5', ?, ?, ?, '2000-01-01T00:00:00Z')",
            (CARD_ID, row[0],
             "In your own words: why is one card enough today?",
             "One card restarts the loop without shame.",
             json.dumps({"rubric": ["one", "loop"]})))
        con.execute(
            "INSERT INTO reviews(card_id, grade, confidence, reviewed_at,"
            " submission) VALUES(?, 4, 3, ?, 'comeback seed')",
            (CARD_ID, stamp))
        con.commit()
        return {"seeded": True, "idle_days": 40}
    finally:
        con.close()
