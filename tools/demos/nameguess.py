"""Feature demo: naming fluency (F-76, type 80).

Full behavior: guess a function's purpose from its name alone, then
verify against the recorded docstring -- exact-choice grading with
sibling-then-pool distractors, no sandbox. seed_db plants the
generated naming card as the sole due card; the /due beat commits
the predicted purpose and polls the docstring-confirmed verdict.
"""
from __future__ import annotations

import json
import sqlite3

CARD_ID = "demo-b18-nameguess"
FRONT = ("What does `parse_args` do? Guess from the name alone \u2014 signature: `parse_args(argv)`. "
         "Commit to a choice, then verify against the recorded docstring.")
BACK = "parse_args: Parses command-line arguments into options. (calc.py:1)"
CHOICES = ["Opens a database connection and returns a handle.",
           "Renders an HTML page from a template and context.",
           "Parses command-line arguments into options.",
           "Retry fn until it succeeds."]
PAYLOAD = {"name": "parse_args", "signature": "parse_args(argv)",
           "choices": CHOICES,
           "answer": "Parses command-line arguments into options.",
           "docstring": "Parses command-line arguments into options.",
           "grounded": True}
ANSWER = "Parses command-line arguments into options."

SCENARIO = {
    "id": "nameguess",
    "kind": "feature",
    "batch": 18,
    "item": "F-76",
    "title": "Naming fluency",
    "blurb": "Guess what a name does before reading its docstring -- prediction then verify.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 18 - Feature F-76",
         "title": "Naming fluency",
         "subtitle": "Predict from the name, verify on the docstring."},
        {"type": "terminal", "duration": 7,
         "caption": "The match in one call: exact purpose wins, a misread quotes the truth.",
         "commands": [
             ["python3", "-c",
              "from groundwork import nameguess as m; "
              "ex = {'payload': {'answer': 'Parses command-line arguments into options.'}}; "
              "print(m.grade(ex, 'Parses command-line arguments into options.')['feedback']); "
              "print(m.grade(ex, 'Opens a database connection.')['feedback'])"],
         ]},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b18-nameguess",
         "caption": "Status homes the type: sibling distractors, docstring truth, no sandbox.",
         "assert_js": "() => !!document.querySelector('#status-b18-nameguess')",
         "assert_want": "True"},
        {"type": "chrome", "duration": 8,
         "url_path": "/due",
         "focus": "#card-{seed_card_id} h3",
         "caption": "The naming card: one name plus its signature, purpose hidden.",
         "assert_js": "() => { const f = document.querySelector("
                      "\"form[action='/cards/{seed_card_id}/review']\"); "
                      "return !!f && document.body.innerText.includes('Guess from the name'); }",
         "assert_want": "True"},
        {"type": "chrome", "duration": 13,
         "url_path": "/due",
         "caption": "Prediction committed -- the recorded docstring confirms it.",
         "js": ["() => { const f = document.querySelector(\"form[action='/cards/{seed_card_id}/review']\"); "
                "if (!f) return 'seed-form-missing'; "
                "f.querySelectorAll(\"input[name='answer']\").forEach(i => i.value = {seed_answer_js}); "
                "const conf = f.querySelector(\"input[name='confidence'][value='4']\"); "
                "if (conf) conf.checked = true; "
                "f.submit(); return 'submitted'; }"],
         "poll_js": "() => document.body.innerText.slice(0, 12000)",
         "poll_want": "Name read right",
         "poll_required": True,
         "poll_timeout": 25,
         "assert_js": "() => !!document.querySelector('.verdict-stamp') && "
                      "document.body.innerText.includes('docstring confirms it')",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 18",
         "title": "Read the name.",
         "subtitle": "nameguess.py deals four purposes -- the docstring first line wins."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Plant the generated type-80 card (pipeline shape) as the sole due card."""
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
            " VALUES(?, ?, '80', ?, ?, ?, '2000-01-01T00:00:00Z')",
            (CARD_ID, row[0], FRONT, BACK, json.dumps(PAYLOAD)))
        con.commit()
        return {"seeded": True, "card_id": CARD_ID,
                "answer_js": json.dumps(json.dumps(ANSWER))[1:-1]}
    finally:
        con.close()
