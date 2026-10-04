"""Feature demo: dead-code elimination (F-15, type 38).

Full behavior: cut one flagged dead node -- an unused import, a
never-called function, or a constant-false branch -- so the
remaining hidden tests stay green. seed_db plants a static greet()
card (pipeline shape, no harness so no sandbox is needed) as the
sole due card; the /due beat deletes the helper and polls the pass verdict.
"""
from __future__ import annotations

import json
import sqlite3

CARD_ID = "demo-deadcode-38"

SCENARIO = {
    "id": "deadcode",
    "kind": "feature",
    "batch": 7,
    "item": "F-15",
    "title": "Dead-code elimination",
    "blurb": "Cut the flagged dead function, branch, or import -- remaining tests stay green.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 7 - Feature F-15",
         "title": "Dead-code elimination",
         "subtitle": "Nothing calls it -- prove it by deleting it."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b7-deadcode",
         "caption": "Status homes the type: AST-checked removal, remaining tests stay green.",
         "assert_js": "() => !!document.querySelector('#status-b7-deadcode')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "The rule in one line: the dead node must be gone, the live function must stay.",
         "commands": [
             ["python3", "-c",
              "from groundwork import deadcode as m; "
              "ex = {'payload': {'kind': 'function', 'target': '_unused_helper', 'func': 'greet', 'tests': ''}}; "
              "print(m.grade(ex, 'def greet(name):\\n    return \\'hi \\' + name\\n')['feedback']); "
              "print(m.grade(ex, 'def greet(name):\\n    return 1\\n\\n\\ndef _unused_helper():\\n    return None\\n')['feedback'])"],
         ]},
        {"type": "chrome", "duration": 8,
         "url_path": "/due",
         "focus": "#card-{seed_card_id}",
         "caption": "The pruning card: greet() plus its never-called helper.",
         "assert_js": "() => { const f = document.querySelector("
                      "\"form[action='/cards/{seed_card_id}/review']\"); "
                      "return !!f && !!f.querySelector(\"textarea[name='answer']\") && "
                      "document.body.innerText.includes('never-called'); }",
         "assert_want": "True"},
        {"type": "chrome", "duration": 13,
         "url_path": "/due",
         "caption": "Helper deleted, greet() intact -- the verdict confirms the prune.",
         "js": ["() => { const f = document.querySelector(\"form[action='/cards/{seed_card_id}/review']\"); "
                "if (!f) return 'seed-form-missing'; "
                "const ta = f.querySelector(\"textarea[name='answer']\"); "
                "if (!ta) return 'no-textarea'; ta.value = {seed_answer_js}; "
                "const conf = f.querySelector(\"input[name='confidence'][value='4']\"); "
                "if (conf) conf.checked = true; "
                "f.submit(); return 'submitted'; }"],
         "poll_js": "() => document.body.innerText.slice(0, 12000)",
         "poll_want": "Pruned",
         "poll_required": True,
         "poll_timeout": 25,
         "assert_js": "() => !!document.querySelector('.verdict-stamp') && "
                      "document.body.innerText.includes('Pruned')",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 7",
         "title": "Cut what never runs.",
         "subtitle": "deadcode.py checks the AST -- imports, helpers, dead branches all count."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Plant one type-38 card (pipeline shape) as the sole due card.

    Static literals carrying the exact bytes generate() deals (front,
    back, payload); the filmed /due answer and verdict prove the card
    live, so the seed stays stdlib-only like the rest of the module.
    """
    body = ('def greet(name):\n    return "hi " + name\n\n\n'
            'def _unused_helper():\n    return None\n')
    front = ('Delete the never-called helper `_unused_helper` — nothing '
             'uses it. `greet` and everything else must stay, and the '
             'hidden tests must keep passing.\n```python\n' + body + '```')
    back = 'def greet(name):\n    return "hi " + name\n'
    payload = {"kind": "function", "target": "_unused_helper",
               "func": "greet", "original": body, "reference": back,
               "tests": "", "seeded": True, "grounded": False}
    answer = 'def greet(name):\n    return "hi " + name\n'
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
            " VALUES(?, ?, '38', ?, ?, ?, '2000-01-01T00:00:00Z')",
            (CARD_ID, row[0], front, back, json.dumps(payload)))
        con.commit()
        return {"seeded": True, "card_id": CARD_ID,
                "answer_js": json.dumps(json.dumps(answer))[1:-1]}
    finally:
        con.close()
