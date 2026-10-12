"""Improvement demo: honest give-up records a lapse (I-159).

Full behavior: a blank submit scores grade 0 through sched so the
card returns sooner, and increments the lapses counter the due-why
tooltip already displays. seed_db plants one due card for the control.
"""
from __future__ import annotations

import json
import sqlite3

CARD_ID = "demo-giveup-159"

SCENARIO = {
    "id": "giveup",
    "kind": "improvement",
    "batch": 24,
    "item": "I-159",
    "title": "Honest give-up",
    "blurb": "Give up and the scheduler tells the truth: lapse, sooner.",
    "beats": [
        {"type": "title", "duration": 4,
         "kicker": "Batch 24 - Improvement I-159",
         "title": "Honest give-up",
         "subtitle": "A blank submit is a lapse -- and returns sooner."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b24-giveup",
         "caption": "Status states the honest path: grade 0 plus one lapse.",
         "assert_js": "() => !!document.querySelector('#status-b24-giveup')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 8,
         "caption": "Blanks lapse, text attempts; the scheduler sets the return.",
         "commands": [
             ["python3", "-c",
              "from groundwork import giveup as m; "
              "print('blank:', m.is_giveup('   '), '| text:', m.is_giveup('x')); "
              "print('next:', m.next_lapses(2)); "
              "u = m.apply_giveup(1.0, 0.5, 2); "
              "print('grade:', u['grade'], '| lapses:', u['lapses']); "
              "print(m.lapse_line(1))"],
         ]},
        {"type": "chrome", "duration": 9,
         "url_path": "/due",
         "js": ["() => { const b = document.querySelector('button.giveup'); "
                "if (!b) return 'missing'; const f = b.closest('form'); "
                "if (!f) return 'no-form'; f.id = 'seed-giveup'; "
                "return 'tagged'; }"],
         "focus": "#seed-giveup",
         "caption": "The lead card offers the same honest exit beside Check.",
         "assert_js": "() => !!document.querySelector('button.giveup') "
                      "&& document.body.innerText.includes('Give up')",
         "assert_want": "True"},
        {"type": "title", "duration": 4,
         "kicker": "Groundwork - Batch 24",
         "title": "Lapse, then sooner.",
         "subtitle": "giveup.py banks the lapse -- the queue forgives."},
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
             "In your own words: what does a lapse cost?",
             "A sooner return until the card sticks.",
             json.dumps({"rubric": ["sooner", "sticks"]})))
        con.commit()
        return {"seeded": True, "card_id": CARD_ID}
    finally:
        con.close()
