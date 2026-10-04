"""Feature demo: config extraction (F-16, type 39).

Full behavior: hoist magic numbers and strings out of a function
body into named module-level constants, so the code reads as intent
instead of literals. seed_db plants a static charge() card (pipeline
shape, no harness so no sandbox is needed) as the sole due card;
the /due beat extracts N_0P2 and N_3 and polls the pass verdict.
"""
from __future__ import annotations

import json
import sqlite3

CARD_ID = "demo-configex-39"

SCENARIO = {
    "id": "configex",
    "kind": "feature",
    "batch": 7,
    "item": "F-16",
    "title": "Config extraction",
    "blurb": "Hoist magic values into named constants; hidden tests stay green.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 7 - Feature F-16",
         "title": "Config extraction",
         "subtitle": "0.2 and 3 become N_0P2 and N_3 -- intent, not literals."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b7-configex",
         "caption": "Status homes the type: AST-checked hoist, behavior identical.",
         "assert_js": "() => !!document.querySelector('#status-b7-configex')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "The rule in one line: each literal needs a named home, and none may stay inline.",
         "commands": [
             ["python3", "-c",
              "from groundwork import configex as m; "
              "ex = {'payload': {'magics': ['0.2', '3'], 'tests': ''}}; "
              "print(m.grade(ex, 'N_0P2 = 0.2\\nN_3 = 3\\n\\n\\ndef charge(n):\\n    return n * N_0P2 + N_3\\n')['feedback']); "
              "print(m.grade(ex, 'def charge(n):\\n    return n * 0.2 + 3\\n')['feedback'])"],
         ]},
        {"type": "chrome", "duration": 8,
         "url_path": "/due",
         "focus": "#card-{seed_card_id}",
         "caption": "The magic card: two bare literals hiding inside charge().",
         "assert_js": "() => { const f = document.querySelector("
                      "\"form[action='/cards/{seed_card_id}/review']\"); "
                      "return !!f && !!f.querySelector(\"textarea[name='answer']\") && "
                      "document.body.innerText.includes('magic values'); }",
         "assert_want": "True"},
        {"type": "chrome", "duration": 13,
         "url_path": "/due",
         "caption": "Hoisted to module level -- the verdict confirms the extraction.",
         "js": ["() => { const f = document.querySelector(\"form[action='/cards/{seed_card_id}/review']\"); "
                "if (!f) return 'seed-form-missing'; "
                "const ta = f.querySelector(\"textarea[name='answer']\"); "
                "if (!ta) return 'no-textarea'; ta.value = {seed_answer_js}; "
                "const conf = f.querySelector(\"input[name='confidence'][value='4']\"); "
                "if (conf) conf.checked = true; "
                "f.submit(); return 'submitted'; }"],
         "poll_js": "() => document.body.innerText.slice(0, 12000)",
         "poll_want": "Magics extracted",
         "poll_required": True,
         "poll_timeout": 25,
         "assert_js": "() => !!document.querySelector('.verdict-stamp') && "
                      "document.body.innerText.includes('Magics extracted')",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 7",
         "title": "Name every magic.",
         "subtitle": "configex.py checks the AST -- UPPER_SNAKE homes or a CONFIG dict."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Plant one type-39 card (pipeline shape) as the sole due card.

    Static literals carrying the exact bytes generate() deals (front,
    back, payload); the filmed /due answer and verdict prove the card
    live, so the seed stays stdlib-only like the rest of the module.
    """
    body = "def charge(n):\n    return n * 0.2 + 3\n"
    front = ('Move the magic values out of `charge` into named constants '
             '(N_0P2, N_3 or a CONFIG dict) — behavior must stay identical.\n'
             '```python\n' + body + '```')
    back = ("N_0P2 = 0.2\nN_3 = 3\n\n\ndef charge(n):\n"
            "    return n * N_0P2 + N_3")
    payload = {"func": "charge", "original": body, "reference": back,
               "magics": ["0.2", "3"],
               "consts": {"0.2": "N_0P2", "3": "N_3"},
               "tests": "", "grounded": False}
    answer = ("N_0P2 = 0.2\nN_3 = 3\n\n\ndef charge(n):\n"
              "    return n * N_0P2 + N_3\n")
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
            " VALUES(?, ?, '39', ?, ?, ?, '2000-01-01T00:00:00Z')",
            (CARD_ID, row[0], front, back, json.dumps(payload)))
        con.commit()
        return {"seeded": True, "card_id": CARD_ID,
                "answer_js": json.dumps(json.dumps(answer))[1:-1]}
    finally:
        con.close()
