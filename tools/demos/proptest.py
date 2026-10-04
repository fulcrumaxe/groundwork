"""Feature demo: property-test authoring (F-10, type 33).

Full behavior: write 2+ `assert` invariant lines for the concept
function -- each line execs against the shown code in a fresh
namespace, and every line must hold. seed_db plants a static add()
card (pipeline shape) as the sole due card; the /due beat submits
two holding invariants and polls the pass verdict.
"""
from __future__ import annotations

import json
import sqlite3

CARD_ID = "demo-proptest-33"

SCENARIO = {
    "id": "proptest",
    "kind": "feature",
    "batch": 7,
    "item": "F-10",
    "title": "Property-test authoring",
    "blurb": "State assert invariants for a function -- each one runs green or tells you which failed.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 7 - Feature F-10",
         "title": "Property-test authoring",
         "subtitle": "State what must always hold -- every assert runs, every failure names its line."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b7-proptest",
         "caption": "Status homes the type: per-invariant grading, fresh namespace, no Hypothesis.",
         "assert_js": "() => !!document.querySelector('#status-b7-proptest')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "The rule in one line: every assert must hold, and one must call the function.",
         "commands": [
             ["python3", "-c",
              "from groundwork import proptest as m; "
              "ex = {'payload': {'code': 'def add(a, b):\\n    return a + b', 'func': 'add'}}; "
              "print(m.grade(ex, 'assert add(2, 3) == 5\\nassert add(1, 1) == 2')['feedback']); "
              "print(m.grade(ex, 'assert add(2, 3) == 6')['feedback'])"],
         ]},
        {"type": "chrome", "duration": 8,
         "url_path": "/due",
         "focus": "#card-{seed_card_id}",
         "caption": "The invariants card: add() on the front, your asserts below.",
         "assert_js": "() => { const f = document.querySelector("
                      "\"form[action='/cards/{seed_card_id}/review']\"); "
                      "return !!f && !!f.querySelector(\"textarea[name='answer']\") && "
                      "document.body.innerText.includes('invariant'); }",
         "assert_want": "True"},
        {"type": "chrome", "duration": 13,
         "url_path": "/due",
         "caption": "Two holding invariants -- the verdict runs each one green.",
         "js": ["() => { const f = document.querySelector(\"form[action='/cards/{seed_card_id}/review']\"); "
                "if (!f) return 'seed-form-missing'; "
                "const ta = f.querySelector(\"textarea[name='answer']\"); "
                "if (!ta) return 'no-textarea'; ta.value = {seed_answer_js}; "
                "const conf = f.querySelector(\"input[name='confidence'][value='4']\"); "
                "if (conf) conf.checked = true; "
                "f.submit(); return 'submitted'; }"],
         "poll_js": "() => document.body.innerText.slice(0, 12000)",
         "poll_want": "invariants hold",
         "poll_required": True,
         "poll_timeout": 25,
         "assert_js": "() => !!document.querySelector('.verdict-stamp') && "
                      "document.body.innerText.includes('invariants hold')",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 7",
         "title": "Properties, not examples.",
         "subtitle": "proptest.py execs each line -- holdings pass, failures name the line."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Plant one type-33 card (pipeline shape) as the sole due card.

    Static literals carrying the exact bytes generate() deals (front,
    back, payload); the filmed /due answer and verdict prove the card
    live, so the seed stays stdlib-only like the rest of the module.
    """
    code = "def add(a, b):\n    return a + b"
    front = ('Write 2+ `assert` invariant lines for `add` — properties '
             'that hold for every valid input:\n```python\n' + code +
             '\n```\nReply with `assert` lines only, each calling `add`.')
    back = ('assert add(2, 3) == 5\n'
            'assert add(2, 3) == add(2, 3)  # deterministic'
            '  (model answer — any holding set counts).')
    payload = {"code": code, "func": "add", "call": "add(2, 3)",
               "expected": "5",
               "reference": ["assert add(2, 3) == 5",
                             "assert add(2, 3) == add(2, 3)  # deterministic"],
               "grounded": True}
    answer = "assert add(2, 3) == 5\nassert add(0, 0) == 0"
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
            " VALUES(?, ?, '33', ?, ?, ?, '2000-01-01T00:00:00Z')",
            (CARD_ID, row[0], front, back, json.dumps(payload)))
        con.commit()
        return {"seeded": True, "card_id": CARD_ID,
                "answer_js": json.dumps(json.dumps(answer))[1:-1]}
    finally:
        con.close()
