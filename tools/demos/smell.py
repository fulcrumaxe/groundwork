"""Feature demo: name-that-smell exercises (F-2, type 15).

Full behavior: read a real snippet and name its dominant code smell --
six smells, one choice, AST-detected and exact-match graded. seed_db plants a static broad-except card (pipeline shape) as
the sole due card; the /due beat answers it natively
and polls the pass verdict.
"""
from __future__ import annotations

import json
import sqlite3

CARD_ID = "demo-smell-15"

SCENARIO = {
    "id": "smell",
    "kind": "feature",
    "batch": 6,
    "item": "F-2",
    "title": "Name-that-smell",
    "blurb": "Read a real snippet and name its dominant code smell.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 6 - Feature F-2",
         "title": "Name-that-smell",
         "subtitle": "Six smells, one choice -- the snippet tells on itself."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b6-smell",
         "caption": "Status homes the type: six smells, AST-detected, exact-graded.",
         "assert_js": "() => !!document.querySelector('#status-b6-smell')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "The rule in one line: strongest detector wins, ties keep catalog order.",
         "commands": [
             ["python3", "-c",
              "from groundwork import smell as m; "
              "code = 'def handle(req):\\n    try:\\n        return process(req)\\n"
              "    except Exception:\\n        return None\\n'; "
              "print(m.choose(code)[0]['title']); "
              "print(sorted(m.detect_all(code).items()))"],
         ]},
        {"type": "chrome", "duration": 8,
         "url_path": "/due",
         "caption": "The smell card: snippet on the front, your verdict below.",
         "assert_js": "() => { const f = document.querySelector("
                      "\"form[action='/cards/{seed_card_id}/review']\"); "
                      "return !!f && !!f.querySelector(\"input[name='answer']\") && "
                      "document.body.innerText.includes('smell'); }",
         "assert_want": "True"},
        {"type": "chrome", "duration": 13,
         "url_path": "/due",
         "caption": "Name it -- the verdict checks the exact choice.",
         "js": ["() => { const f = document.querySelector(\"form[action='/cards/{seed_card_id}/review']\"); "
                "if (!f) return 'seed-form-missing'; "
                "const inp = f.querySelector(\"input[name='answer']\"); "
                "if (!inp) return 'no-input'; inp.value = {seed_answer_js}; "
                "const conf = f.querySelector(\"input[name='confidence'][value='4']\"); "
                "if (conf) conf.checked = true; "
                "f.submit(); return 'submitted'; }"],
         "poll_js": "() => document.body.innerText.slice(0, 12000)",
         "poll_want": "Correct choice",
         "poll_required": True,
         "poll_timeout": 25,
         "assert_js": "() => !!document.querySelector('.verdict-stamp') && "
                      "document.body.innerText.includes('Correct choice')",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 6",
         "title": "Trust the loudest smell.",
         "subtitle": "smell.py detects six -- grade() matches one exactly."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Plant one type-15 card (pipeline shape) as the sole due card.

    Static literals carrying the exact bytes generate() deals (front,
    back, payload); the filmed /due answer and verdict prove the card
    live, so the seed stays stdlib-only like the rest of the module.
    """
    front = 'Which code smell best describes this snippet from `handle_request`?\n```python\ndef handle(req):\n    try:\n        return process(req)\n    except Exception:\n        return None\n\n```'
    back = 'Overly Broad Except — a bare or Exception-wide handler swallows every failure. Fix: catch the narrowest error you can handle.'
    payload = {'choices': ['Long Function', 'Long Parameter List', 'Overly Broad Except'], 'answer': 'Overly Broad Except', 'smell': 'broad-except', 'grounded': True, 'detail': 'a bare or Exception-wide handler swallows every failure'}
    answer = 'Overly Broad Except'
    con = sqlite3.connect(db_path)
    try:
        row = con.execute(
            "SELECT id FROM concepts ORDER BY rowid LIMIT 1").fetchone()
        if not row:
            return {"seeded": False, "reason": "no concepts"}
        con.execute("UPDATE cards SET due='2030-01-01T00:00:00Z'")
        con.execute("DELETE FROM reviews WHERE card_id=?", ('demo-smell-15',))
        con.execute(
            "INSERT OR REPLACE INTO cards(id, concept_id, exercise_type,"
            " front, back, payload, due)"
            " VALUES(?, ?, '15', ?, ?, ?, '2000-01-01T00:00:00Z')",
            ('demo-smell-15', row[0], front, back, json.dumps(payload)))
        con.commit()
        return {"seeded": True, "card_id": 'demo-smell-15',
                "answer_js": json.dumps(json.dumps(answer))[1:-1]}
    finally:
        con.close()
