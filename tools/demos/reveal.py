"""Improvement demo: give-up reveal logs grade 0 (I-158).

Full behavior: a blank answer at confidence 1 is the surrender post:
it logs grade 0 and the answer appears only after the attempt is
recorded. seed_db plants one card so /due shows the Give up control.
"""
from __future__ import annotations

import json
import sqlite3

CARD_ID = "demo-reveal-158"

SCENARIO = {
    "id": "reveal",
    "kind": "improvement",
    "batch": 24,
    "item": "I-158",
    "title": "Give-up reveal",
    "blurb": "Surrender logs 0 -- the answer shows after, not before.",
    "beats": [
        {"type": "title", "duration": 4,
         "kicker": "Batch 24 - Improvement I-158",
         "title": "Give-up reveal",
         "subtitle": "Stuck? The answer waits until the attempt lands."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b24-reveal",
         "caption": "Status pins the contract: blank plus 1 means surrender.",
         "assert_js": "() => !!document.querySelector('#status-b24-reveal')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 8,
         "caption": "Only the surrender post reveals; real attempts grade on.",
         "commands": [
             ["python3", "-c",
              "from groundwork import reveal as m; "
              "print('surrender:', m.is_reveal_request('', 1), '| attempt:', m.is_reveal_request('Paris', 1)); "
              "r = m.reveal_result({'back': 'Paris'}); "
              "print('grade:', r['grade'], '| revealed:', r['revealed']); "
              "print('visible:', m.back_visible(True), m.back_visible(False))"],
         ]},
        {"type": "chrome", "duration": 9,
         "url_path": "/due",
         "js": ["() => { const b = document.querySelector('button.giveup'); "
                "if (!b) return 'missing'; const f = b.closest('form'); "
                "if (!f) return 'no-form'; f.id = 'seed-giveup'; "
                "return 'tagged'; }"],
         "focus": "#seed-giveup",
         "caption": "Every card offers the honest exit: Give up, show the answer.",
         "assert_js": "() => !!document.querySelector('button.giveup') "
                      "&& document.body.innerText.includes('Give up')",
         "assert_want": "True"},
        {"type": "title", "duration": 4,
         "kicker": "Groundwork - Batch 24",
         "title": "Surrender, then study.",
         "subtitle": "reveal.py logs 0 first -- the back appears after."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Plant one card as the sole due card for the give-up control."""
    con = sqlite3.connect(db_path)
    try:
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
             "In your own words: why does surrender log grade 0?",
             "An honest fail reschedules sooner than a near-miss.",
             json.dumps({"rubric": ["honest", "sooner"]})))
        con.commit()
        return {"seeded": True, "card_id": CARD_ID}
    finally:
        con.close()
