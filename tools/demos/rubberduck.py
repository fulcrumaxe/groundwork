"""Feature demo: rubber-duck mode (F-79, type 83).

Full behavior: explain the concept to a patient bot that only asks
questions -- three fixed prompts, keyword half-bar grading, the
thinnest answer named in the feedback. seed_db plants the generated
rubber-duck card as the sole due card; the /due beat answers all
three prompts and polls the duck-nods verdict.
"""
from __future__ import annotations

import json
import sqlite3

CARD_ID = "demo-b19-rubberduck"
FRONT = ("Explain `add` to the duck — it only asks questions:\n"
         "Q1 — What does it do, in one sentence?\n"
         "Q2 — Show one concrete input → output walk-through.\n"
         "Q3 — What breaks if one key line were removed?\n"
         "```python\ndef add(a, b):\n    return a + b\n```")
BACK = "The duck accepts any complete explanation covering: sum, inputs, return"
PAYLOAD = {"questions": ["Q1 — What does it do, in one sentence?",
                         "Q2 — Show one concrete input → output walk-through.",
                         "Q3 — What breaks if one key line were removed?"],
           "rubric": ["sum", "inputs", "return"],
           "code": "def add(a, b):\n    return a + b",
           "grounded": True}
ANSWER = ("add returns the sum of its two inputs: add(2, 3) gives 5, "
          "and without the return line callers get nothing back")

SCENARIO = {
    "id": "rubberduck",
    "kind": "feature",
    "batch": 19,
    "item": "F-79",
    "title": "Rubber-duck mode",
    "blurb": "Explain it to a patient bot that only asks questions -- three prompts, no answers given.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 19 - Feature F-79",
         "title": "Rubber-duck mode",
         "subtitle": "The duck only asks -- covering half the key points passes."},
        {"type": "terminal", "duration": 7,
         "caption": "Half-bar grading: key points covered passes, thin answers name what is missing.",
         "commands": [
             ["python3", "-c",
              "from groundwork import rubberduck as m; "
              "ex = {'payload': {'rubric': ['sum', 'inputs', 'return']}}; "
              "print(m.grade(ex, 'add returns the sum of its inputs')['feedback']); "
              "print(m.grade(ex, 'it does stuff')['feedback']); "
              "print(m.grade(ex, '')['feedback'])"],
         ]},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b19-rubberduck",
         "caption": "Status homes the type: three prompts, half-bar coverage, no answers given.",
         "assert_js": "() => !!document.querySelector('#status-b19-rubberduck')",
         "assert_want": "True"},
        {"type": "chrome", "duration": 8,
         "url_path": "/due",
         "focus": "#card-{seed_card_id} h3",
         "caption": "The duck card: three questions asked, zero answered -- explaining is yours.",
         "assert_js": "() => { const f = document.querySelector("
                     "\"form[action='/cards/{seed_card_id}/review']\"); "
                     "return !!f && document.body.innerText.includes('only asks'); }",
         "assert_want": "True"},
        {"type": "chrome", "duration": 13,
         "url_path": "/due",
         "caption": "All three questions answered -- every key point covered.",
         "js": ["() => { const f = document.querySelector(\"form[action='/cards/{seed_card_id}/review']\"); "
                "if (!f) return 'seed-form-missing'; "
                "const nf = document.createElement('form'); nf.method = 'post'; nf.action = f.action; "
                "const ta = document.createElement('textarea'); ta.name = 'answer'; ta.value = {seed_answer_js}; "
                "const cf = document.createElement('input'); cf.type = 'hidden'; cf.name = 'confidence'; cf.value = '4'; "
                "const og = document.createElement('input'); og.type = 'hidden'; og.name = 'origin'; og.value = '/due'; "
                "nf.appendChild(ta); nf.appendChild(cf); nf.appendChild(og); "
                "document.body.appendChild(nf); nf.submit(); return 'submitted'; }"],
         "poll_js": "() => document.body.innerText.slice(0, 12000)",
         "poll_want": "duck nods",
         "poll_required": True,
         "poll_timeout": 25,
         "assert_js": "() => !!document.querySelector('.verdict-stamp') && "
                      "document.body.innerText.includes('key points covered')",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 19",
         "title": "Answer the duck.",
         "subtitle": "rubberduck.py asks three questions -- coverage does the rest."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Plant the generated type-83 card (pipeline shape) as the sole due card."""
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
            " VALUES(?, ?, '83', ?, ?, ?, '2000-01-01T00:00:00Z')",
            (CARD_ID, row[0], FRONT, BACK, json.dumps(PAYLOAD)))
        con.commit()
        return {"seeded": True, "card_id": CARD_ID,
                "answer_js": json.dumps(json.dumps(ANSWER))[1:-1]}
    finally:
        con.close()
