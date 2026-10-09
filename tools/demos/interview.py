"""Feature demo: mastery interview (F-69, type 73).

Full behavior: read the prompt aloud as if defending the concept in
an oral exam, then write the spoken explanation -- graded against a
spoken-style rubric where half the key points passes. seed_db plants
the generated interview card as the sole due card; the /due beat
submits a covering explanation and polls the cleared-bar verdict.
"""
from __future__ import annotations

import json
import sqlite3

CARD_ID = "demo-b18-interview"
FRONT = ("Mastery interview: read this aloud as if defending `add` in an oral exam "
         "\u2014 what it does, why it is shaped this way, what breaks without it. "
         "Then write down the explanation you just spoke.\n```\ndef add(a, b):\n    return a + b\n```")
BACK = "add; calc.py"
PAYLOAD = {"rubric": ["add", "calc.py"],
           "code": "def add(a, b):\n    return a + b", "grounded": True}
ANSWER = "add is a function in calc.py that returns the sum of its inputs"

SCENARIO = {
    "id": "interview",
    "kind": "feature",
    "batch": 18,
    "item": "F-69",
    "title": "Mastery interview",
    "blurb": "Defend a concept aloud like an oral exam -- speak it, write it, and clear half the rubric points.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 18 - Feature F-69",
         "title": "Mastery interview",
         "subtitle": "Defend the concept aloud, write what you spoke, clear half the rubric."},
        {"type": "terminal", "duration": 7,
         "caption": "The bar in one call: cover half the key points; silence says nothing.",
         "commands": [
             ["python3", "-c",
              "from groundwork import interview as m; "
              "ex = {'payload': {'rubric': ['add', 'calc.py']}}; "
              "print(m.grade(ex, 'add is a function in calc.py')['feedback']); "
              "print(m.grade(ex, 'something about numbers')['feedback']); "
              "print(m.grade(ex, '')['feedback'])"],
         ]},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b18-interview",
         "caption": "Status homes the type: spoken-style rubric, half-or-more passes.",
         "assert_js": "() => !!document.querySelector('#status-b18-interview')",
         "assert_want": "True"},
        {"type": "chrome", "duration": 8,
         "url_path": "/due",
         "focus": "#card-{seed_card_id} h3",
         "caption": "The interview card: defend the concept aloud, then write it down.",
         "assert_js": "() => { const f = document.querySelector("
                      "\"form[action='/cards/{seed_card_id}/review']\"); "
                      "return !!f && document.body.innerText.includes('oral exam'); }",
         "assert_want": "True"},
        {"type": "chrome", "duration": 13,
         "url_path": "/due",
         "caption": "A covering explanation -- every key point named, the bar cleared.",
         "js": ["() => { const f = document.querySelector(\"form[action='/cards/{seed_card_id}/review']\"); "
                "if (!f) return 'seed-form-missing'; "
                "f.querySelectorAll(\"input[name='answer']\").forEach(i => i.value = {seed_answer_js}); "
                "const conf = f.querySelector(\"input[name='confidence'][value='4']\"); "
                "if (conf) conf.checked = true; "
                "f.submit(); return 'submitted'; }"],
         "poll_js": "() => document.body.innerText.slice(0, 12000)",
         "poll_want": "oral-exam bar cleared",
         "poll_required": True,
         "poll_timeout": 25,
         "assert_js": "() => !!document.querySelector('.verdict-stamp') && "
                      "document.body.innerText.includes('Covered 2/2 key points')",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 18",
         "title": "Say it, then write it.",
         "subtitle": "interview.py grades the spoken rubric -- speech first, coverage after."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Plant the generated type-73 card (pipeline shape) as the sole due card."""
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
            " VALUES(?, ?, '73', ?, ?, ?, '2000-01-01T00:00:00Z')",
            (CARD_ID, row[0], FRONT, BACK, json.dumps(PAYLOAD)))
        con.commit()
        return {"seeded": True, "card_id": CARD_ID,
                "answer_js": json.dumps(json.dumps(ANSWER))[1:-1]}
    finally:
        con.close()
