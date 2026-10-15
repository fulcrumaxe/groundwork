"""Improvement demo: live rubric checklist (I-167).

Full behavior: explain textareas show their rubric keywords beside
the box, ticking [x] as the learner types them -- advisory only,
grading untouched. seed_db plants one etype-5 card with a two-word
rubric as the sole due card.
"""
from __future__ import annotations

import json
import sqlite3

CARD_ID = "demo-rubriclive-167"

PAYLOAD = {"rubric": ["honest", "sooner"]}

SCENARIO = {
    "id": "rubriclive",
    "kind": "improvement",
    "batch": 25,
    "item": "I-167",
    "title": "Live rubric checklist",
    "blurb": "Explain answers tick their keywords live -- advisory only.",
    "beats": [
        {"type": "title", "duration": 4,
         "kicker": "Batch 25 - Improvement I-167",
         "title": "Live rubric checklist",
         "subtitle": "Type the key points -- watch them tick, ungraded."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b25-rubriclive",
         "caption": "Status states the deal: advisory ticks, grading untouched.",
         "assert_js": "() => !!document.querySelector('#status-b25-rubriclive') "
                      "&& document.body.innerText.includes('advisory only')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "Word-boundary hits, mirrored server-side for tests.",
         "commands": [
             ["python3", "-c",
              "from groundwork import rubriclive as m; "
              "print(m.matched('An honest fail reschedules sooner', ['honest', 'sooner'])); "
              "print(m.matched('a vague answer', ['honest', 'sooner']))"],
         ]},
        {"type": "chrome", "duration": 10,
         "url_path": "/due",
         "js": ["() => { const f = document.querySelector(\"form[action='/cards/{seed_card_id}/review']\"); "
                "if (!f) return 'seed-form-missing'; "
                "const ta = f.querySelector('textarea[name=answer]'); "
                "if (!ta) return 'no-textarea'; ta.value = 'an honest effort here'; "
                "ta.textContent = ta.value; "
                "ta.dispatchEvent(new Event('input', {bubbles: true})); "
                "return 'typed'; }"],
         "focus": "form[action='/cards/{seed_card_id}/review']",
         "caption": "Type 'honest' -- one box ticks, one stays open.",
         "poll_js": "() => document.querySelector(\"form[action='/cards/{seed_card_id}/review'] .rubriclive\").innerText",
         "poll_want": "[x]",
         "poll_required": True,
         "assert_js": "() => document.querySelector(\"form[action='/cards/{seed_card_id}/review'] .rubriclive\")"
                      ".innerText.includes('[x]')",
         "assert_want": "True"},
        {"type": "title", "duration": 4,
         "kicker": "Groundwork - Batch 25",
         "title": "Write to the rubric.",
         "subtitle": "rubriclive.py ticks client-side -- never graded."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Plant one rubric-graded explain card as the sole due card."""
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
             json.dumps(PAYLOAD)))
        con.commit()
        return {"seeded": True, "card_id": CARD_ID}
    finally:
        con.close()
