"""Feature demo: type-annotation retrofit (F-8, type 31).

Full behavior: unannotated function in, full annotations out --
AST-graded per slot, partial credit per match. seed_db plants a
static card (pipeline shape) as the sole due card.
"""
from __future__ import annotations

import json
import sqlite3

CARD_ID = "demo-typeanno-31"

SCENARIO = {
    "id": "typeanno",
    "kind": "feature",
    "batch": 6,
    "item": "F-8",
    "title": "Type-annotation retrofit",
    "blurb": "Unannotated function in, full annotations out -- AST-graded.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 6 - Feature F-8",
         "title": "Type-annotation retrofit",
         "subtitle": "Every parameter and the return -- the AST checks each slot."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b6-typeanno",
         "caption": "Status homes the type: slots, reference, per-slot credit.",
         "assert_js": "() => !!document.querySelector('#status-b6-typeanno')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "The rule in one line: annotations normalize, then compare.",
         "commands": [
             ["python3", "-c",
              "from groundwork import typeanno as m; "
              "print(m.norm_ann('List[int]')); "
              "print(m.norm_ann('list[int]'))"],
         ]},
        {"type": "chrome", "duration": 8,
         "url_path": "/due",
         "caption": "The annotation card: stripped signature on the front.",
         "assert_js": "() => { const f = document.querySelector("
                      "\"form[action='/cards/{seed_card_id}/review']\"); "
                      "return !!f && !!f.querySelector(\"textarea[name='answer']\") && "
                      "document.body.innerText.includes('annotations'); }",
         "assert_want": "True"},
        {"type": "chrome", "duration": 13,
         "url_path": "/due",
         "caption": "Annotate every slot -- params first, the return last.",
         "js": ["() => { const f = document.querySelector(\"form[action='/cards/{seed_card_id}/review']\"); "
                "if (!f) return 'seed-form-missing'; "
                "const ta = f.querySelector(\"textarea[name='answer']\"); "
                "if (!ta) return 'no-textarea'; ta.value = {seed_answer_js}; "
                "const conf = f.querySelector(\"input[name='confidence'][value='4']\"); "
                "if (conf) conf.checked = true; "
                "f.submit(); return 'submitted'; }"],
         "poll_js": "() => document.body.innerText.slice(0, 12000)",
         "poll_want": "All annotations match",
         "poll_required": True,
         "poll_timeout": 25,
         "assert_js": "() => !!document.querySelector('.verdict-stamp') && "
                      "document.body.innerText.includes('All annotations match')",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 6",
         "title": "Types are promises.",
         "subtitle": "typeanno.py strips the def -- you write it back typed."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Plant one type-31 card (pipeline shape) as the sole due card.

    Static literals carrying the exact bytes generate() deals (front,
    back, payload); the filmed /due answer and verdict prove the card
    live, so the seed stays stdlib-only like the rest of the module.
    """
    front = 'Add type annotations to `total` — every parameter and the return value.\n```python\ndef total(items, factor=1.0):\n    return sum(items) * factor\n```'
    back = 'def total(items: list, factor: float = 1.0) -> float:\n    return sum(items) * factor'
    payload = {'func': 'total', 'slots': ['factor', 'items'], 'want_return': True, 'annotations': {'items': 'list', 'factor': 'float'}, 'returns': 'float', 'stripped': 'def total(items, factor=1.0):\n    return sum(items) * factor', 'reference': 'def total(items: list, factor: float = 1.0) -> float:\n    return sum(items) * factor', 'grounded': True}
    answer = 'def total(items: list, factor: float = 1.0) -> float:\n    return sum(items) * factor'
    con = sqlite3.connect(db_path)
    try:
        row = con.execute(
            "SELECT id FROM concepts ORDER BY rowid LIMIT 1").fetchone()
        if not row:
            return {"seeded": False, "reason": "no concepts"}
        con.execute("UPDATE cards SET due='2030-01-01T00:00:00Z'")
        con.execute("DELETE FROM reviews WHERE card_id=?", ('demo-typeanno-31',))
        con.execute(
            "INSERT OR REPLACE INTO cards(id, concept_id, exercise_type,"
            " front, back, payload, due)"
            " VALUES(?, ?, '31', ?, ?, ?, '2000-01-01T00:00:00Z')",
            ('demo-typeanno-31', row[0], front, back, json.dumps(payload)))
        con.commit()
        return {"seeded": True, "card_id": 'demo-typeanno-31',
                "answer_js": json.dumps(json.dumps(answer))[1:-1]}
    finally:
        con.close()
