"""Improvement demo: visible Run button with Ctrl+Enter hint (I-155).

Full behavior: every code exercise shows a labeled Run control with
its shortcut plus a form-scoped handler; non-code cards render
byte-identical. seed_db plants one type-12 card as the sole due card.
"""
from __future__ import annotations

import json
import sqlite3

CARD_ID = "demo-runkey-155"

SCENARIO = {
    "id": "runkey",
    "kind": "improvement",
    "batch": 24,
    "item": "I-155",
    "title": "Run button with shortcut",
    "blurb": "Every code exercise names its Ctrl+Enter runner.",
    "beats": [
        {"type": "title", "duration": 4,
         "kicker": "Batch 24 - Improvement I-155",
         "title": "Run button with shortcut",
         "subtitle": "See the button, run from the keyboard."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b24-runkey",
         "caption": "Status shows the labeled control with a live sample.",
         "assert_js": "() => !!document.querySelector('#status-b24-runkey')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "Code types get the affordance; choice and text cards get ''.",
         "commands": [
             ["python3", "-c",
              "from groundwork import runkey as m; "
              "print('code12:', m.is_code_exercise('12'), '| text5:', m.is_code_exercise('5')); "
              "print(m.run_button_html()[:110]); "
              "print('non-code:', repr(m.runkey_for('5')[:20]))"],
         ]},
        {"type": "chrome", "duration": 10,
         "url_path": "/due",
         "focus": "form[action='/cards/{seed_card_id}/review']",
         "caption": "The lead code card carries Run tests with its Ctrl+Enter hint.",
         "assert_js": "() => !!document.querySelector('[data-runkey]') "
                      "&& document.body.innerText.includes('Ctrl+Enter')",
         "assert_want": "True"},
        {"type": "title", "duration": 4,
         "kicker": "Groundwork - Batch 24",
         "title": "Run it, hands home.",
         "subtitle": "runkey.py labels the shortcut where it is used."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Plant one type-12 card as the sole due card."""
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
            " VALUES(?, ?, '12', ?, ?, ?, '2000-01-01T00:00:00Z')",
            (CARD_ID, row[0],
             "Implement mul(a, b) so the hidden tests pass.",
             "def mul(a, b):\n    return a * b",
             json.dumps({"stub": "def mul(a, b):\n    pass",
                         "tests": "assert mul(2, 3) == 6"})))
        con.commit()
        return {"seeded": True, "card_id": CARD_ID}
    finally:
        con.close()
