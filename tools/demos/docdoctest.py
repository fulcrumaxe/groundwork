"""Feature demo: doc-example doctest (F-9, type 32).

Full behavior: write a >>> example that passes as a real doctest run
against the shown code -- pure stdlib grading, no sandbox. seed_db
plants a static card (pipeline shape) as the sole due card.
"""
from __future__ import annotations

import json
import sqlite3

CARD_ID = "demo-docdoctest-32"

SCENARIO = {
    "id": "docdoctest",
    "kind": "feature",
    "batch": 6,
    "item": "F-9",
    "title": "Doc-example doctest",
    "blurb": "Write a >>> example that passes as a real doctest run.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 6 - Feature F-9",
         "title": "Doc-example doctest",
         "subtitle": "Your example runs as doctest -- exact output or nothing."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b6-docdoctest",
         "caption": "Status homes the type: real doctest run, pure stdlib.",
         "assert_js": "() => !!document.querySelector('#status-b6-docdoctest')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "The rule in one line: call it in a >>> line, match output exactly.",
         "commands": [
             ["python3", "-c",
              "from groundwork import docdoctest as m; "
              "ex = {'payload': {'code': 'def f():\\n    return 1\\n', 'func': 'f'}}; "
              "print(m.grade(ex, \">>> f()\\n1\")['feedback']); "
              "print(m.grade(ex, \">>> f()\\n2\")['feedback'][:60])"],
         ]},
        {"type": "chrome", "duration": 8,
         "url_path": "/due",
         "caption": "The doctest card: code on the front, example below.",
         "assert_js": "() => { const f = document.querySelector("
                      "\"form[action='/cards/{seed_card_id}/review']\"); "
                      "return !!f && !!f.querySelector(\"textarea[name='answer']\") && "
                      "document.body.innerText.includes('doctest'); }",
         "assert_want": "True"},
        {"type": "chrome", "duration": 13,
         "url_path": "/due",
         "caption": "Write the example -- it runs against the code right now.",
         "js": ["() => { const f = document.querySelector(\"form[action='/cards/{seed_card_id}/review']\"); "
                "if (!f) return 'seed-form-missing'; "
                "const ta = f.querySelector(\"textarea[name='answer']\"); "
                "if (!ta) return 'no-textarea'; ta.value = {seed_answer_js}; "
                "const conf = f.querySelector(\"input[name='confidence'][value='4']\"); "
                "if (conf) conf.checked = true; "
                "f.submit(); return 'submitted'; }"],
         "poll_js": "() => document.body.innerText.slice(0, 12000)",
         "poll_want": "Doctest green",
         "poll_required": True,
         "poll_timeout": 25,
         "assert_js": "() => !!document.querySelector('.verdict-stamp') && "
                      "document.body.innerText.includes('Doctest green')",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 6",
         "title": "Examples that run.",
         "subtitle": "docdoctest.py execs the snippet -- your >>> must hold."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Plant one type-32 card (pipeline shape) as the sole due card.

    Static literals carrying the exact bytes generate() deals (front,
    back, payload); the filmed /due answer and verdict prove the card
    live, so the seed stays stdlib-only like the rest of the module.
    """
    front = "Write a doctest example for `shout` that passes as a real doctest run (`...` abbreviations allowed):\n```python\ndef shout(text):\n    return text.upper() + '!'\n```\nReply with `>>>` lines plus the exact expected output."
    back = ">>> shout()\n'HI!'  (model answer — any passing example calling it counts)."
    payload = {'code': "def shout(text):\n    return text.upper() + '!'", 'func': 'shout', 'call': 'shout()', 'reference': ">>> shout()\n'HI!'", 'expected': "'HI!'", 'grounded': True}
    answer = ">>> shout('hi')\n'HI!'"
    con = sqlite3.connect(db_path)
    try:
        row = con.execute(
            "SELECT id FROM concepts ORDER BY rowid LIMIT 1").fetchone()
        if not row:
            return {"seeded": False, "reason": "no concepts"}
        con.execute("UPDATE cards SET due='2030-01-01T00:00:00Z'")
        con.execute("DELETE FROM reviews WHERE card_id=?", ('demo-docdoctest-32',))
        con.execute(
            "INSERT OR REPLACE INTO cards(id, concept_id, exercise_type,"
            " front, back, payload, due)"
            " VALUES(?, ?, '32', ?, ?, ?, '2000-01-01T00:00:00Z')",
            ('demo-docdoctest-32', row[0], front, back, json.dumps(payload)))
        con.commit()
        return {"seeded": True, "card_id": 'demo-docdoctest-32',
                "answer_js": json.dumps(json.dumps(answer))[1:-1]}
    finally:
        con.close()
