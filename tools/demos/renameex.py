"""Feature demo: rename-symbol exercises (F-3, type 17).

Full behavior: propose a clearer name for a weak identifier --
convention-checked (snake_case, no shadowing) and rubric-justified
(half the key points passes). seed_db plants a static card
(pipeline shape) as the sole due card.
"""
from __future__ import annotations

import json
import sqlite3

CARD_ID = "demo-renameex-17"

SCENARIO = {
    "id": "renameex",
    "kind": "feature",
    "batch": 6,
    "item": "F-3",
    "title": "Rename-symbol exercise",
    "blurb": "Propose a clearer name; convention-checked, rubric-justified.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 6 - Feature F-3",
         "title": "Rename-symbol exercise",
         "subtitle": "Weak name in, intention-revealing name out -- plus the why."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b6-renameex",
         "caption": "Status homes the type: machine-checked, human-justified.",
         "assert_js": "() => !!document.querySelector('#status-b6-renameex')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "The rule in one line: conventions gate, rubric words score.",
         "commands": [
             ["python3", "-c",
              "from groundwork import renameex as m; "
              "print(m.convention_failures('running_total', 'x')); "
              "print(m.convention_failures('x', 'x'))"],
         ]},
        {"type": "chrome", "duration": 8,
         "url_path": "/due",
         "caption": "The rename card: weak identifier on the front, name-plus-why below.",
         "assert_js": "() => { const f = document.querySelector("
                      "\"form[action='/cards/{seed_card_id}/review']\"); "
                      "return !!f && !!f.querySelector(\"input[name='answer']\") && "
                      "document.body.innerText.includes('better name'); }",
         "assert_want": "True"},
        {"type": "chrome", "duration": 13,
         "url_path": "/due",
         "caption": "Propose the name with the why -- both halves must pass.",
         "js": ["() => { const f = document.querySelector(\"form[action='/cards/{seed_card_id}/review']\"); "
                "if (!f) return 'seed-form-missing'; "
                "const ta = f.querySelector(\"input[name='answer']\"); "
                "if (!ta) return 'no-field'; ta.value = {seed_answer_js}; "
                "const conf = f.querySelector(\"input[name='confidence'][value='4']\"); "
                "if (conf) conf.checked = true; "
                "f.submit(); return 'submitted'; }"],
         "poll_js": "() => document.body.innerText.slice(0, 12000)",
         "poll_want": "Clear name, well justified",
         "poll_required": True,
         "poll_timeout": 25,
         "assert_js": "() => !!document.querySelector('.verdict-stamp') && "
                      "document.body.innerText.includes('Clear name, well justified')",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 6",
         "title": "Names are documentation.",
         "subtitle": "renameex.py checks the shape -- you supply the meaning."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Plant one type-17 card (pipeline shape) as the sole due card.

    Static literals carrying the exact bytes generate() deals (front,
    back, payload); the filmed /due answer and verdict prove the card
    live, so the seed stays stdlib-only like the rest of the module.
    """
    front = 'Propose a better name for `x` (variable) — then one line saying why it fits.\n```python\ndef total(items):\n    x = 0\n    for i in items:\n        x = x + i\n    return x\n```'
    back = 'Rename `x` to an intention-revealing snake_case name and justify it against: total, variable, pricing.py.'
    payload = {'target': 'x', 'kind': 'variable', 'code': 'def total(items):\n    x = 0\n    for i in items:\n        x = x + i\n    return x', 'rubric': ['total', 'variable', 'pricing.py'], 'grounded': True}
    answer = 'running_total — total variable in pricing.py'
    con = sqlite3.connect(db_path)
    try:
        row = con.execute(
            "SELECT id FROM concepts ORDER BY rowid LIMIT 1").fetchone()
        if not row:
            return {"seeded": False, "reason": "no concepts"}
        con.execute("UPDATE cards SET due='2030-01-01T00:00:00Z'")
        con.execute("DELETE FROM reviews WHERE card_id=?", ('demo-renameex-17',))
        con.execute(
            "INSERT OR REPLACE INTO cards(id, concept_id, exercise_type,"
            " front, back, payload, due)"
            " VALUES(?, ?, '17', ?, ?, ?, '2000-01-01T00:00:00Z')",
            ('demo-renameex-17', row[0], front, back, json.dumps(payload)))
        con.commit()
        return {"seeded": True, "card_id": 'demo-renameex-17',
                "answer_js": json.dumps(json.dumps(answer))[1:-1]}
    finally:
        con.close()
