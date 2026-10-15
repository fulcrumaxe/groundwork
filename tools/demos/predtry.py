"""Improvement demo: predict pre-submit retries (I-166).

Full behavior: type-8 cards offer 3 client-side pre-submit checks --
each miss narrows the hint (shape, position, region quote) with no
POST and no grade touched. seed_db plants one etype-8 card as the
sole due card; the beat tries twice and lands on the position hint.
"""
from __future__ import annotations

import json
import sqlite3

CARD_ID = "demo-predtry-166"

PAYLOAD = {"code": "print(2 + 2)", "expected": "4"}

SCENARIO = {
    "id": "predtry",
    "kind": "improvement",
    "batch": 25,
    "item": "I-166",
    "title": "Predict retries: 3 strikes",
    "blurb": "Try a prediction 3 times pre-submit; each miss narrows it.",
    "beats": [
        {"type": "title", "duration": 4,
         "kicker": "Batch 25 - Improvement I-166",
         "title": "Predict retries: 3 strikes",
         "subtitle": "Shape, then position, then a quote -- before you submit."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b25-predtry",
         "caption": "Status shows the tier ladder with a sample tier-1.",
         "assert_js": "() => !!document.querySelector('#status-b25-predtry') "
                      "&& document.body.innerText.includes('tier-1')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "Strikes narrow: shape, first-difference, region quote.",
         "commands": [
             ["python3", "-c",
              "from groundwork import predtry as m; "
              "print(m.hint_for('4', '5', 1)); "
              "print(m.hint_for('4', '5', 2)); "
              "print('match:', repr(m.hint_for('4', '4', 1)))"],
         ]},
        {"type": "chrome", "duration": 10,
         "url_path": "/due",
         "js": ["() => { const f = document.querySelector(\"form[action='/cards/{seed_card_id}/review']\"); "
                "if (!f) return 'seed-form-missing'; "
                "const g = f.querySelector('input[name=answer]'); "
                "const b = f.querySelector('.predtry-try'); "
                "if (!g || !b) return 'no-widget'; "
                "g.value = '5'; g.setAttribute('value', g.value); "
                "b.click(); b.click(); "
                "return f.querySelector('.predtry-hint').textContent; }"],
         "focus": "form[action='/cards/{seed_card_id}/review']",
         "caption": "Two wrong tries -- the hint narrows to line 1, char 1.",
         "poll_js": "() => document.querySelector(\"form[action='/cards/{seed_card_id}/review'] .predtry-hint\").textContent",
         "poll_want": "First differs at line",
         "poll_required": True,
         "assert_js": "() => document.querySelector(\"form[action='/cards/{seed_card_id}/review'] .predtry-hint\")"
                      ".textContent.includes('First differs at line 1, char 1')",
         "assert_want": "True"},
        {"type": "title", "duration": 4,
         "kicker": "Groundwork - Batch 25",
         "title": "Struggle first, then submit.",
         "subtitle": "predtry.py checks client-side -- grade path untouched."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Plant one predict-output card as the sole due card."""
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
             "What does this print? print(2 + 2).",
             "4",
             json.dumps(PAYLOAD)))
        con.commit()
        return {"seeded": True, "card_id": CARD_ID}
    finally:
        con.close()
