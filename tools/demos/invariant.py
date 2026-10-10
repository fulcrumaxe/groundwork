"""Feature demo: invariant stating (F-85, type 89).

Full behavior: a for-range loop card asks for the bound the loop
maintains; the exact normalized bound passes and anything else fails
with the shape as hint. seed_db plants the generated type-89 card as
the sole due card; the /due beat states the bound and polls the
Bound-holds verdict on the full result page.
"""
from __future__ import annotations

import json
import sqlite3

CARD_ID = "demo-b20-invariant"
CODE = "for i in range(10):\n    use(i)"
REFERENCE = "0<=i<=10"
FRONT = ("State the loop invariant \u2014 the bound it maintains. "
         "Reply with the bound, e.g. `0<=i<=10`.\n```python\n" + CODE + "\n```")
BACK = ("0<=i<=10: the loop maintains this bound on every pass \u2014 "
        "check it before and after the body.")
PAYLOAD = {"answer": REFERENCE,
           "site": "for i in range(10):\n    use(i)",
           "kind": "for-range",
           "reference": REFERENCE, "grounded": True}
ANSWER = "0<=i<=10"

SCENARIO = {
    "id": "invariant",
    "kind": "feature",
    "batch": 20,
    "item": "F-85",
    "title": "Invariant stating",
    "blurb": "State the loop invariant -- the exact bound wins, the verifier checks the rest.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 20 - Feature F-85",
         "title": "Invariant stating",
         "subtitle": "Name the bound the loop maintains -- for-range edges and while guards."},
        {"type": "terminal", "duration": 7,
         "caption": "Exact normalized text wins; spacing and case are free, a wrong edge fails.",
         "commands": [
             ["python3", "-c",
              "from groundwork import invariant as m; "
              "ex = {'payload': {'reference': '0<=i<=10'}}; "
              "print(m.grade(ex, '0<=i<=10')['feedback']); "
              "print(m.grade(ex, ' 0 <= I <= 10 ')['feedback']); "
              "print(m.grade(ex, '0<=i<10')['feedback'])"],
         ]},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b20-invariant",
         "caption": "Status homes the type: type 89 drills for-range bounds and while guards.",
         "assert_js": "() => !!document.querySelector('#status-b20-invariant')",
         "assert_want": "True"},
        {"type": "chrome", "duration": 8,
         "url_path": "/due",
         "focus": "#card-{seed_card_id} h3",
         "caption": "The drill card: one for-range loop, one bound to state.",
         "assert_js": "() => { const f = document.querySelector("
                     "\"form[action='/cards/{seed_card_id}/review']\"); "
                     "return !!f && document.body.innerText.includes('Reply with the bound'); }",
         "assert_want": "True"},
        {"type": "chrome", "duration": 13,
         "url_path": "/due",
         "caption": "Zero to ten holds on every pass -- state it and the verifier agrees.",
         "js": ["() => { const f = document.querySelector(\"form[action='/cards/{seed_card_id}/review']\"); "
                "if (!f) return 'seed-form-missing'; "
                "f.querySelectorAll(\"input[name='answer']\").forEach(i => i.value = {seed_answer_js}); "
                "const conf = f.querySelector(\"input[name='confidence'][value='4']\"); "
                "if (conf) conf.checked = true; "
                "f.submit(); return 'submitted'; }"],
         "poll_js": "() => document.body.innerText.slice(0, 12000)",
         "poll_want": "Bound holds",
         "poll_required": True,
         "poll_timeout": 25,
         "assert_js": "() => !!document.querySelector('.verdict-stamp') && "
                      "document.body.innerText.includes('maintains this bound')",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 20",
         "title": "The bound is yours.",
         "subtitle": "invariant.py derives the reference statically -- no sandbox, exact match."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Plant the generated type-89 card (pipeline shape) as the sole due card."""
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
            " VALUES(?, ?, '89', ?, ?, ?, '2000-01-01T00:00:00Z')",
            (CARD_ID, row[0], FRONT, BACK, json.dumps(PAYLOAD)))
        con.commit()
        return {"seeded": True, "card_id": CARD_ID,
                "answer_js": json.dumps(json.dumps(ANSWER))[1:-1]}
    finally:
        con.close()
