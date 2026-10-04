"""Feature demo: complexity golf (F-4, type 26).

Full behavior: rewrite a nested function so it nests less --
AST-measured against a target depth, same behavior required. seed_db plants a static card
(pipeline shape, no harness so no sandbox is needed) as the sole
due card.
"""
from __future__ import annotations

import json
import sqlite3

CARD_ID = "demo-golf-26"

SCENARIO = {
    "id": "golf",
    "kind": "feature",
    "batch": 6,
    "item": "F-4",
    "title": "Complexity golf",
    "blurb": "Rewrite a nested function so it nests less -- tests stay green.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 6 - Feature F-4",
         "title": "Complexity golf",
         "subtitle": "Depth 3 in, depth 1 out -- the AST keeps score."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b6-golf",
         "caption": "Status homes the type: measured depth, target, same behavior.",
         "assert_js": "() => !!document.querySelector('#status-b6-golf')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "The rule in one line: max nesting is counted, not guessed.",
         "commands": [
             ["python3", "-c",
              "from groundwork import golf as m; "
              "a = 'def f(x):\\n    if x:\\n        if x > 1:\\n            return 1\\n    return 0\\n'; "
              "b = 'def f(x):\\n    if not x:\\n        return 0\\n    return 1 if x > 1 else 0\\n'; "
              "print('before:', m.max_nesting(a), 'after:', m.max_nesting(b))"],
         ]},
        {"type": "chrome", "duration": 8,
         "url_path": "/due",
         "caption": "The golf card: depth, target, and the nested original.",
         "assert_js": "() => { const f = document.querySelector("
                      "\"form[action='/cards/{seed_card_id}/review']\"); "
                      "return !!f && !!f.querySelector(\"textarea[name='answer']\") && "
                      "document.body.innerText.includes('Complexity golf'); }",
         "assert_want": "True"},
        {"type": "chrome", "duration": 13,
         "url_path": "/due",
         "caption": "Flatten it with guard clauses -- depth down, function intact.",
         "js": ["() => { const f = document.querySelector(\"form[action='/cards/{seed_card_id}/review']\"); "
                "if (!f) return 'seed-form-missing'; "
                "const ta = f.querySelector(\"textarea[name='answer']\"); "
                "if (!ta) return 'no-textarea'; ta.value = {seed_answer_js}; "
                "const conf = f.querySelector(\"input[name='confidence'][value='4']\"); "
                "if (conf) conf.checked = true; "
                "f.submit(); return 'submitted'; }"],
         "poll_js": "() => document.body.innerText.slice(0, 12000)",
         "poll_want": "intact",
         "poll_required": True,
         "poll_timeout": 25,
         "assert_js": "() => !!document.querySelector('.verdict-stamp') && "
                      "document.body.innerText.includes('intact')",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 6",
         "title": "Par is lower.",
         "subtitle": "golf.py measures depth -- a bare pass defines nothing."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Plant one type-26 card (pipeline shape) as the sole due card.

    Static literals carrying the exact bytes generate() deals (front,
    back, payload); the filmed /due answer and verdict prove the card
    live, so the seed stays stdlib-only like the rest of the module.
    """
    front = 'Complexity golf: rewrite `check` so its max nesting depth drops from 3 to 2 or less — same behavior.\n```python\ndef check(user):\n    if user:\n        if user.active:\n            if user.verified:\n                return True\n    return False\n\n```'
    back = 'def check(user):\n    if user:\n        if user.active:\n            if user.verified:\n                return True\n    return False\n'
    payload = {'original': 'def check(user):\n    if user:\n        if user.active:\n            if user.verified:\n                return True\n    return False\n', 'depth': 3, 'target': 2, 'tests': '', 'reference': 'def check(user):\n    if user:\n        if user.active:\n            if user.verified:\n                return True\n    return False\n', 'func': 'check', 'grounded': False}
    answer = 'def check(user):\n    if not user:\n        return False\n    if not user.active:\n        return False\n    return bool(user.verified)\n'
    con = sqlite3.connect(db_path)
    try:
        row = con.execute(
            "SELECT id FROM concepts ORDER BY rowid LIMIT 1").fetchone()
        if not row:
            return {"seeded": False, "reason": "no concepts"}
        con.execute("UPDATE cards SET due='2030-01-01T00:00:00Z'")
        con.execute("DELETE FROM reviews WHERE card_id=?", ('demo-golf-26',))
        con.execute(
            "INSERT OR REPLACE INTO cards(id, concept_id, exercise_type,"
            " front, back, payload, due)"
            " VALUES(?, ?, '26', ?, ?, ?, '2000-01-01T00:00:00Z')",
            ('demo-golf-26', row[0], front, back, json.dumps(payload)))
        con.commit()
        return {"seeded": True, "card_id": 'demo-golf-26',
                "answer_js": json.dumps(json.dumps(answer))[1:-1]}
    finally:
        con.close()
