"""Feature demo: friendly coffee wagers on delayed recalls (F-128).

Full behavior: ?wager=probe:<card>:<window> bets settle against the
latest recorded grade (4+ wins); accuracy bets settle against the
north-star delayed snapshot; missing data stays open. seed_db banks
one grade-5 review so the probe bet wins.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone

CARD_ID = "demo-wagers-128"

SCENARIO = {
    "id": "wagers",
    "kind": "feature",
    "batch": 24,
    "item": "F-128",
    "title": "Friendly wagers",
    "blurb": "Bet a coffee on your next delayed retest.",
    "beats": [
        {"type": "title", "duration": 4,
         "kicker": "Batch 24 - Feature F-128",
         "title": "Friendly wagers",
         "subtitle": "Probe passes win coffee -- the ledger keeps score."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b24-wagers",
         "caption": "Status names the stakes: coffee only, measured outcomes.",
         "assert_js": "() => !!document.querySelector('#status-b24-wagers')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "Probes settle on grades, accuracy on delayed snapshots.",
         "commands": [
             ["python3", "-c",
              "from groundwork import wagers as m; "
              "w = m.wagers_from_query({'wager': ['probe:c1:7']}); "
              "print('placed:', w[0]['kind'], w[0]['card_id']); "
              "print('settle5:', m.settle(w[0], {'grade': 5})['status']); "
              "print('ledger:', m.ledger_summary(m.settle_all(w, {'c1': 5}, None)))"],
         ]},
        {"type": "chrome", "duration": 10,
         "url_path": "/reviews?wager=probe:{seed_card_id}:7",
         "focus": "#status-wagers",
         "caption": "The History ledger settles the probe bet won on grade 5.",
         "assert_js": "() => !!document.querySelector('#status-wagers') "
                      "&& document.body.innerText.includes('coffees won')",
         "assert_want": "True"},
        {"type": "title", "duration": 4,
         "kicker": "Groundwork - Batch 24",
         "title": "Coffee on recall.",
         "subtitle": "wagers.py settles measured bets -- no money, no network."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Plant one card with a grade-5 review so the probe bet wins."""
    con = sqlite3.connect(db_path)
    try:
        row = con.execute(
            "SELECT id FROM concepts ORDER BY rowid LIMIT 1").fetchone()
        if not row:
            return {"seeded": False, "reason": "no concepts"}
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        con.execute("DELETE FROM reviews WHERE card_id=?", (CARD_ID,))
        con.execute(
            "INSERT OR REPLACE INTO cards(id, concept_id, exercise_type,"
            " front, back, payload, due)"
            " VALUES(?, ?, '5', ?, ?, ?, '2030-01-01T00:00:00Z')",
            (CARD_ID, row[0],
             "In your own words: why bet coffee on recall?",
             "Stakes make the delayed retest matter.",
             json.dumps({"rubric": ["stakes", "recall"]})))
        con.execute(
            "INSERT INTO reviews(card_id, grade, confidence, reviewed_at,"
            " submission) VALUES(?, 5, 4, ?, 'wagers seed: fluent recall')",
            (CARD_ID, now))
        con.commit()
        return {"seeded": True, "card_id": CARD_ID}
    finally:
        con.close()
