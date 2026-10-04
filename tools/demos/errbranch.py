"""Feature demo: error-handling retrofit (F-6, type 28).

Full behavior: add the missing error branch -- a fault-injection
harness fails on the shown code until the guard handles it, and old
behavior must hold. seed_db plants a static card (pipeline shape: verified-breaking
mutation with its fault harness). The /due beat answers with the fix natively
and polls the green verdict.
"""
from __future__ import annotations

import json
import sqlite3

CARD_ID = "demo-errbranch-28"

SCENARIO = {
    "id": "errbranch",
    "kind": "feature",
    "batch": 6,
    "item": "F-6",
    "title": "Error-handling retrofit",
    "blurb": "Add the missing error branch: the fault harness fails until you do.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 6 - Feature F-6",
         "title": "Error-handling retrofit",
         "subtitle": "The fault fails first -- your guard turns it green."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b6-errbranch",
         "caption": "Status homes the type: verified-breaking mutation, live card.",
         "assert_js": "() => !!document.querySelector('#status-b6-errbranch')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 8,
         "caption": "The rule in one line: base must FAIL the harness, the fix goes GREEN.",
         "commands": [
             ["python3", "-c",
              "from groundwork import sandbox as s; r = s.SandboxRunner(); "
              "base = 'def divide(a, b):\\n    return a / b\\n'; "
              "fix = 'def divide(a, b):\\n    if b == 0:\\n        return None\\n    return a / b\\n'; "
              "t = 'print(divide(1, 0))\\n'; "
              "print('base ok:', r.run(base + t).ok, '| fix ok:', r.run(fix + t).ok)"],
         ]},
        {"type": "chrome", "duration": 7,
         "url_path": "/due",
         "caption": "The retrofit card: unguarded code, fault named, fix below.",
         "assert_js": "() => { const f = document.querySelector("
                      "\"form[action='/cards/{seed_card_id}/review']\"); "
                      "return !!f && !!f.querySelector(\"textarea[name='answer']\") && "
                      "document.body.innerText.includes('ZeroDivisionError'); }",
         "assert_want": "True"},
        {"type": "chrome", "duration": 13,
         "url_path": "/due",
         "caption": "Guard the zero -- the fault harness runs your fix live.",
         "js": ["() => { const f = document.querySelector(\"form[action='/cards/{seed_card_id}/review']\"); "
                "if (!f) return 'seed-form-missing'; "
                "const ta = f.querySelector(\"textarea[name='answer']\"); "
                "if (!ta) return 'no-textarea'; ta.value = {seed_answer_js}; "
                "const conf = f.querySelector(\"input[name='confidence'][value='4']\"); "
                "if (conf) conf.checked = true; "
                "f.submit(); return 'submitted'; }"],
         "poll_js": "() => document.body.innerText.slice(0, 12000)",
         "poll_want": "Fault handled",
         "poll_required": True,
         "poll_timeout": 25,
         "assert_js": "() => !!document.querySelector('.verdict-stamp') && "
                      "document.body.innerText.includes('Fault handled')",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 6",
         "title": "Handle the fault.",
         "subtitle": "errbranch.py grades base-red then fix-green -- stale cards fail shut."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Plant one type-28 card (pipeline shape) as the sole due card.

    Static literals carrying the exact bytes generate() deals (front,
    back, payload); the filmed /due answer and verdict prove the card
    live, so the seed stays stdlib-only like the rest of the module.
    """
    front = 'Add the missing error-handling branch to `divide`: it currently fails on ZeroDivisionError on b=0. Handle the fault without changing normal behavior.\n```python\ndef divide(a, b):\n    return a / b\n\n```'
    back = 'def divide(a, b):\n    if b == 0:\n        return None\n    return a / b\n'
    payload = {'code': 'def divide(a, b):\n    return a / b\n', 'tests': 'print(divide(1, 0))\n', 'reference': 'def divide(a, b):\n    if b == 0:\n        return None\n    return a / b\n', 'fault': 'ZeroDivisionError on b=0', 'grounded': True}
    answer = 'def divide(a, b):\n    if b == 0:\n        return None\n    return a / b\n'
    con = sqlite3.connect(db_path)
    try:
        row = con.execute(
            "SELECT id FROM concepts ORDER BY rowid LIMIT 1").fetchone()
        if not row:
            return {"seeded": False, "reason": "no concepts"}
        con.execute("UPDATE cards SET due='2030-01-01T00:00:00Z'")
        con.execute("DELETE FROM reviews WHERE card_id=?", ('demo-errbranch-28',))
        con.execute(
            "INSERT OR REPLACE INTO cards(id, concept_id, exercise_type,"
            " front, back, payload, due)"
            " VALUES(?, ?, '28', ?, ?, ?, '2000-01-01T00:00:00Z')",
            ('demo-errbranch-28', row[0], front, back, json.dumps(payload)))
        con.commit()
        return {"seeded": True, "card_id": 'demo-errbranch-28',
                "answer_js": json.dumps(json.dumps(answer))[1:-1]}
    finally:
        con.close()
