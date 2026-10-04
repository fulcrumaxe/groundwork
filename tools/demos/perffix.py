"""Feature demo: perf fix (F-12, type 35).

Full behavior: rewrite a loop-heavy function so its AST complexity
(nesting + loops) drops to the target or less -- same behavior, no
timing involved. seed_db plants a static total() card (pipeline
shape, no harness so no sandbox is needed) as the sole due card;
the /due beat submits a comprehension rewrite and polls the verdict.
"""
from __future__ import annotations

import json
import sqlite3

CARD_ID = "demo-perffix-35"

SCENARIO = {
    "id": "perffix",
    "kind": "feature",
    "batch": 7,
    "item": "F-12",
    "title": "Perf-fix exercises",
    "blurb": "Rewrite a loop-heavy function so it scores lower -- AST-measured, tests stay green.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 7 - Feature F-12",
         "title": "Perf-fix exercises",
         "subtitle": "Complexity 5 in, 0 out -- the AST keeps score, not the clock."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b7-perffix",
         "caption": "Status homes the type: measured score, lower target, function intact.",
         "assert_js": "() => !!document.querySelector('#status-b7-perffix')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "The rule in one line: nesting plus loops is the score -- comprehensions cost nothing.",
         "commands": [
             ["python3", "-c",
              "from groundwork import perffix as m; "
              "a = 'def total(rows):\\n    out = 0\\n    for r in rows:\\n        for c in r:\\n            if c:\\n                out += c\\n    return out\\n'; "
              "b = 'def total(rows):\\n    return sum(c for r in rows for c in r if c)\\n'; "
              "print('before:', m.complexity(a), 'after:', m.complexity(b))"],
         ]},
        {"type": "chrome", "duration": 8,
         "url_path": "/due",
         "focus": "#card-{seed_card_id}",
         "caption": "The perf card: score 5 to beat, nested loops on the front.",
         "assert_js": "() => { const f = document.querySelector("
                      "\"form[action='/cards/{seed_card_id}/review']\"); "
                      "return !!f && !!f.querySelector(\"textarea[name='answer']\") && "
                      "document.body.innerText.includes('Perf fix'); }",
         "assert_want": "True"},
        {"type": "chrome", "duration": 13,
         "url_path": "/due",
         "caption": "One comprehension -- score down, total() intact.",
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
         "kicker": "Groundwork - Batch 7",
         "title": "Simpler and green.",
         "subtitle": "perffix.py measures nesting plus loops -- a bare pass defines nothing."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Plant one type-35 card (pipeline shape) as the sole due card.

    Static literals carrying the exact bytes generate() deals (front,
    back, payload); the filmed /due answer and verdict prove the card
    live, so the seed stays stdlib-only like the rest of the module.
    """
    code = ("def total(rows):\n    out = 0\n    for r in rows:\n"
            "        for c in r:\n            if c:\n"
            "                out += c\n    return out\n")
    front = ('Perf fix: rewrite `total` so its complexity drops from 5 to '
             '4 or less — same behavior, no timing involved (AST-measured, '
             'tests stay green).\n```python\n' + code + '```')
    back = code
    payload = {"original": code, "score": 5, "target": 4, "loops": 2,
               "tests": "", "reference": code, "func": "total",
               "grounded": False}
    answer = ("def total(rows):\n"
              "    return sum(c for r in rows for c in r if c)\n")
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
            " VALUES(?, ?, '35', ?, ?, ?, '2000-01-01T00:00:00Z')",
            (CARD_ID, row[0], front, back, json.dumps(payload)))
        con.commit()
        return {"seeded": True, "card_id": CARD_ID,
                "answer_js": json.dumps(json.dumps(answer))[1:-1]}
    finally:
        con.close()
