"""Improvement demo: sandbox output inline on predict cards (I-156).

Full behavior: type-8 predict-output cards carry a collapsed Show
measured output block with the stored sandbox stdout; unmeasured
cards render byte-identical. seed_db plants one measured type-8 card.
"""
from __future__ import annotations

import json
import sqlite3

CARD_ID = "demo-sandout-156"

SCENARIO = {
    "id": "sandout",
    "kind": "improvement",
    "batch": 24,
    "item": "I-156",
    "title": "Sandbox output inline",
    "blurb": "Predict first, then check the measured output on the card.",
    "beats": [
        {"type": "title", "duration": 4,
         "kicker": "Batch 24 - Improvement I-156",
         "title": "Sandbox output inline",
         "subtitle": "Guess first -- the answer never leaves the card."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b24-sandout",
         "caption": "Status documents the collapsed reveal with a live sample.",
         "assert_js": "() => !!document.querySelector('#status-b24-sandout')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "Measured payloads reveal; legacy payloads stay silent.",
         "commands": [
             ["python3", "-c",
              "from groundwork import sandout as m; "
              "print('measured:', repr(m.measured_output({'code': 'print(1)', 'expected': '1'}))); "
              "print('legacy:', repr(m.measured_output({'hints': []}))); "
              "print(m.output_html({'payload': '{\"code\": \"print(2+3)\", \"expected\": \"5\"}'})[:120])"],
         ]},
        {"type": "chrome", "duration": 10,
         "url_path": "/due",
         "focus": "details.sandout",
         "caption": "The lead predict card hides its measured output one click away.",
         "assert_js": "() => !!document.querySelector('details.sandout') "
                      "&& document.body.innerText.includes('Show measured output')",
         "assert_want": "True"},
        {"type": "title", "duration": 4,
         "kicker": "Groundwork - Batch 24",
         "title": "Verify without leaving.",
         "subtitle": "sandout.py keeps the proof on the card."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Plant one measured type-8 card as the sole due card."""
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
            " VALUES(?, ?, '8', ?, ?, ?, '2000-01-01T00:00:00Z')",
            (CARD_ID, row[0],
             "Predict the stdout/return value of:\n```python\nprint(2 + 3)\n```",
             "5",
             json.dumps({"code": "print(2 + 3)", "expected": "5",
                         "choices": [], "answer": "5"})))
        con.commit()
        return {"seeded": True, "card_id": CARD_ID}
    finally:
        con.close()
