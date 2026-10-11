"""Feature demo: counterexample hunting (F-83, type 87).

Full behavior: state the belief, then break it -- one input
expression replayed live against the real function; falsifying
the check passes, surviving inputs say what happened. seed_db
plants the generated counterexample card as the sole due card;
the /due beat submits the breaking input and polls the
claim-broken verdict.
"""
from __future__ import annotations

import json
import sqlite3

CARD_ID = "demo-b19-counterex"
CODE = "def head(xs):\n    return xs[0]\n"
CLAIM = "`head` never raises for small inputs."
FRONT = (f"Claim: {CLAIM}\nBreak it with one input expression.\n"
         f"```python\n{CODE}```")
BACK = "Breaker: `[]` — raised IndexError"
PAYLOAD = {"func": "head", "arity": 1, "claim": CLAIM, "code": CODE,
           "check": "no-raise", "choices": None,
           "answer": "[]", "reference": "[]", "grounded": True}
ANSWER = "[]"

SCENARIO = {
    "id": "counterex",
    "kind": "feature",
    "batch": 19,
    "item": "F-83",
    "title": "Counterexample hunting",
    "blurb": "State the belief, then break it: name one input where the claim about a real function fails.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 19 - Feature F-83",
         "title": "Counterexample hunting",
         "subtitle": "One input that breaks the claim -- replayed live against the code."},
        {"type": "terminal", "duration": 7,
         "caption": "Live replay: the empty list raises, a good input survives and says so.",
         "commands": [
             ["python3", "-c",
              "from groundwork import counterex as m; "
              "ex = {'payload': {'func': 'head', 'arity': 1, "
              "'code': 'def head(xs):\\n    return xs[0]\\n', 'check': 'no-raise'}}; "
              "print(m.grade(ex, '[]')['feedback']); "
              "print(m.grade(ex, '[1]')['feedback'])"],
         ]},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b19-counterex",
         "caption": "Status homes the type: stated claim, one breaker input, live replay.",
         "assert_js": "() => !!document.querySelector('#status-b19-counterex')",
         "assert_want": "True"},
        {"type": "chrome", "duration": 8,
         "url_path": "/due",
         "focus": "#card-{seed_card_id} h3",
         "caption": "The hunt card: the claim stands until one input breaks it.",
         "assert_js": "() => { const f = document.querySelector("
                     "\"form[action='/cards/{seed_card_id}/review']\"); "
                     "return !!f && document.body.innerText.includes('Break it with one input'); }",
         "assert_want": "True"},
        {"type": "chrome", "duration": 13,
         "url_path": "/due",
         "caption": "The empty list breaks it -- head raises IndexError, claim falsified.",
         "js": ["() => { const f = document.querySelector(\"form[action='/cards/{seed_card_id}/review']\"); "
                "if (!f) return 'seed-form-missing'; "
                "f.querySelectorAll(\"input[name='answer']\").forEach(i => i.value = {seed_answer_js}); "
                "const conf = f.querySelector(\"input[name='confidence'][value='4']\"); "
                "if (conf) conf.checked = true; "
                "f.submit(); return 'submitted'; }"],
         "poll_js": "() => document.body.innerText.slice(0, 12000)",
         "poll_want": "Claim broken",
         "poll_required": True,
         "poll_timeout": 25,
         "assert_js": "() => !!document.querySelector('.verdict-stamp') && "
                      "document.body.innerText.includes('raised IndexError')",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 19",
         "title": "Beliefs need breakers.",
         "subtitle": "counterex.py replays your input -- falsifying passes."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Plant the generated type-87 card (pipeline shape) as the sole due card."""
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
            " VALUES(?, ?, '87', ?, ?, ?, '2000-01-01T00:00:00Z')",
            (CARD_ID, row[0], FRONT, BACK, json.dumps(PAYLOAD)))
        con.commit()
        return {"seeded": True, "card_id": CARD_ID,
                "answer_js": json.dumps(json.dumps(ANSWER))[1:-1]}
    finally:
        con.close()
