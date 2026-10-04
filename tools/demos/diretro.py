"""Feature demo: dependency-injection swap (F-5, type 27).

Full behavior: rewrite a hardcoded dependency as an injected
parameter defaulting to the original -- old callers keep working.
seed_db plants a static card (pipeline shape, no harness so no
sandbox is needed) as the sole due card.
"""
from __future__ import annotations

import json
import sqlite3

CARD_ID = "demo-diretro-27"

SCENARIO = {
    "id": "diretro",
    "kind": "feature",
    "batch": 6,
    "item": "F-5",
    "title": "Dependency-injection swap",
    "blurb": "Rewrite a hardcoded dependency as a parameter; callers stay green.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 6 - Feature F-5",
         "title": "Dependency-injection swap",
         "subtitle": "Hardcoded inside, parameter on top -- defaults preserve callers."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b6-diretro",
         "caption": "Status homes the type: AST-checked injection, green harness.",
         "assert_js": "() => !!document.querySelector('#status-b6-diretro')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "The rule in one line: the default must name the original.",
         "commands": [
             ["python3", "-c",
              "from groundwork import diretro as m; "
              "ex = {'payload': {'dep': 'deliver', 'param': 'sender', 'func': 'greet', 'tests': ''}}; "
              "print(m.grade(ex, 'def greet(name, sender=deliver):\\n    return sender(name)')['feedback']); "
              "print(m.grade(ex, 'def greet(name):\\n    return deliver(name)')['feedback'])"],
         ]},
        {"type": "chrome", "duration": 8,
         "url_path": "/due",
         "caption": "The swap card: hardcoded call on the front, injection below.",
         "assert_js": "() => { const f = document.querySelector("
                      "\"form[action='/cards/{seed_card_id}/review']\"); "
                      "return !!f && !!f.querySelector(\"textarea[name='answer']\") && "
                      "document.body.innerText.includes('parameter'); }",
         "assert_want": "True"},
        {"type": "chrome", "duration": 13,
         "url_path": "/due",
         "caption": "Inject it -- the default keeps every old caller working.",
         "js": ["() => { const f = document.querySelector(\"form[action='/cards/{seed_card_id}/review']\"); "
                "if (!f) return 'seed-form-missing'; "
                "const ta = f.querySelector(\"textarea[name='answer']\"); "
                "if (!ta) return 'no-textarea'; ta.value = {seed_answer_js}; "
                "const conf = f.querySelector(\"input[name='confidence'][value='4']\"); "
                "if (conf) conf.checked = true; "
                "f.submit(); return 'submitted'; }"],
         "poll_js": "() => document.body.innerText.slice(0, 12000)",
         "poll_want": "defaults preserved",
         "poll_required": True,
         "poll_timeout": 25,
         "assert_js": "() => !!document.querySelector('.verdict-stamp') && "
                      "document.body.innerText.includes('defaults preserved')",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 6",
         "title": "Inject, don't hardcode.",
         "subtitle": "diretro.py checks the AST -- the default is the contract."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Plant one type-27 card (pipeline shape) as the sole due card.

    Static literals carrying the exact bytes generate() deals (front,
    back, payload); the filmed /due answer and verdict prove the card
    live, so the seed stays stdlib-only like the rest of the module.
    """
    front = 'Rewrite `greet` so its hardcoded `deliver` arrives as a parameter `sender=deliver` — old callers must keep working.\n```python\ndef greet(name):\n    msg = make_greeting(name)\n    return deliver(msg)\n\n```'
    back = 'def greet(name, sender=deliver):\n    msg = make_greeting(name)\n    return deliver(msg)'
    payload = {'dep': 'deliver', 'param': 'sender', 'func': 'greet', 'original': 'def greet(name):\n    msg = make_greeting(name)\n    return deliver(msg)\n', 'reference': 'def greet(name, sender=deliver):\n    msg = make_greeting(name)\n    return deliver(msg)', 'tests': '', 'grounded': False}
    answer = 'def greet(name, sender=deliver):\n    msg = make_greeting(name)\n    return deliver(msg)'
    con = sqlite3.connect(db_path)
    try:
        row = con.execute(
            "SELECT id FROM concepts ORDER BY rowid LIMIT 1").fetchone()
        if not row:
            return {"seeded": False, "reason": "no concepts"}
        con.execute("UPDATE cards SET due='2030-01-01T00:00:00Z'")
        con.execute("DELETE FROM reviews WHERE card_id=?", ('demo-diretro-27',))
        con.execute(
            "INSERT OR REPLACE INTO cards(id, concept_id, exercise_type,"
            " front, back, payload, due)"
            " VALUES(?, ?, '27', ?, ?, ?, '2000-01-01T00:00:00Z')",
            ('demo-diretro-27', row[0], front, back, json.dumps(payload)))
        con.commit()
        return {"seeded": True, "card_id": 'demo-diretro-27',
                "answer_js": json.dumps(json.dumps(answer))[1:-1]}
    finally:
        con.close()
