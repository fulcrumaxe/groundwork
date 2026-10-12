"""Feature demo: co-op card splits for two learners (F-127).

Full behavior: two ?buddy= names on /due deal the live queue
alternately into two complementary hands (disjoint, covering every
card); solo visits render exactly as before. seed_db plants 2 cards.
"""
from __future__ import annotations

import json
import sqlite3

CARD_IDS = ("demo-coop-127a", "demo-coop-127b")

SCENARIO = {
    "id": "coop",
    "kind": "feature",
    "batch": 24,
    "item": "F-127",
    "title": "Co-op card splits",
    "blurb": "Two learners split the queue -- no repeats, none out.",
    "beats": [
        {"type": "title", "duration": 4,
         "kicker": "Batch 24 - Feature F-127",
         "title": "Co-op card splits",
         "subtitle": "One queue, two hands -- study together, locally."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b24-coop",
         "caption": "Status deals the rule: alternate off live order, cover all.",
         "assert_js": "() => !!document.querySelector('#status-b24-coop')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "Duos deal alternately; solos and singletons stay solo.",
         "commands": [
             ["python3", "-c",
              "from groundwork import coop as m; "
              "due = [{'id': 'a'}, {'id': 'b'}, {'id': 'c'}]; "
              "a, b = m.deal(due, ['Ada', 'Grace']); "
              "print('hands:', len(a), len(b), '| complementary:', m.is_complementary(a, b, due)); "
              "print('solo:', m.deal(due, ['Ada']))"],
         ]},
        {"type": "chrome", "duration": 10,
         "url_path": "/due?buddy=Ada&buddy=Grace",
         "caption": "Two names split the live queue into labelled hands.",
         "assert_js": "() => !!document.querySelector('.coop-split') "
                      "&& document.body.innerText.includes('Co-op split')",
         "assert_want": "True"},
        {"type": "title", "duration": 4,
         "kicker": "Groundwork - Batch 24",
         "title": "Split the queue.",
         "subtitle": "coop.py deals complements -- solo queues never change."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Plant two cards as the due queue for the split."""
    con = sqlite3.connect(db_path)
    try:
        row = con.execute(
            "SELECT id FROM concepts ORDER BY rowid LIMIT 1").fetchone()
        if not row:
            return {"seeded": False, "reason": "no concepts"}
        con.execute("UPDATE cards SET due='2030-01-01T00:00:00Z'")
        for i, cid in enumerate(CARD_IDS):
            con.execute("DELETE FROM reviews WHERE card_id=?", (cid,))
            con.execute(
                "INSERT OR REPLACE INTO cards(id, concept_id, exercise_type,"
                " front, back, payload, due)"
                " VALUES(?, ?, '5', ?, ?, ?, '2000-01-01T00:00:00Z')",
                (cid, row[0],
                 f"In your own words: co-op card {i + 1} of 2.",
                 f"Answer {i + 1}: split the work, share the win.",
                 json.dumps({"rubric": ["split", "share"]})))
        con.commit()
        return {"seeded": True, "cards": len(CARD_IDS)}
    finally:
        con.close()
