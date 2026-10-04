"""Feature demo: regex authoring (F-31, type 54).

Full behavior: write a regex for the order-id shape -- ORD plus
exactly four digits -- fullmatched against the stored case-suite.
seed_db plants a static type-54 card (generate() bytes) as the sole
due card; terminal runs accept + loose-pattern reject, /due submits
the pattern and polls the 9/9 verdict.
"""
from __future__ import annotations

import json
import sqlite3

CARD_ID = "demo-regexex-54"

SCENARIO = {
    "id": "regexex",
    "kind": "feature",
    "batch": 9,
    "item": "F-31",
    "title": "Regex authoring",
    "blurb": "Write a regex that matches every required case and rejects the rest.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 9 - Feature F-31",
         "title": "Regex authoring",
         "subtitle": "One pattern -- every must-match green, every reject red."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b9-regexex",
         "caption": "Status homes the type: fixed case-suite, pure re fullmatch.",
         "assert_js": "() => !!document.querySelector('#status-b9-regexex')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "The rule in one line: fullmatch every case -- partial credit per case.",
         "commands": [
             ["python3", "-c",
              "from types import SimpleNamespace; "
              "from groundwork import regexex as m; "
              "c = SimpleNamespace(node_id='n-order', "
              "name='order', kind='function', file='svc.py', line=1); "
              "e = m.generate('demo-regexex-54', c, [], {}); "
              "print(m.grade(e, 'ORD-[0-9]{4}')['feedback']); "
              "print(m.grade(e, '.*')['feedback'])"],
         ]},
        {"type": "chrome", "duration": 8,
         "url_path": "/due",
         "focus": "#card-{seed_card_id}",
         "caption": "The regex card: the shape and cases on the front, your pattern below.",
         "assert_js": "() => { const f = document.querySelector("
                      "\"form[action='/cards/{seed_card_id}/review']\"); "
                      "return !!f && !!f.querySelector(\"input[name='answer']\") && "
                      "document.body.innerText.includes('regular expression'); }",
         "assert_want": "True"},
        {"type": "chrome", "duration": 13,
         "url_path": "/due",
         "caption": "ORD plus four digits, pinned -- the verdict takes the pattern.",
         "js": ["() => { const f = document.querySelector(\"form[action='/cards/{seed_card_id}/review']\"); "
                "if (!f) return 'seed-form-missing'; "
                "const inp = f.querySelector(\"input[name='answer']\"); "
                "if (!inp) return 'no-input'; inp.value = {seed_answer_js}; "
                "const conf = f.querySelector(\"input[name='confidence'][value='4']\"); "
                "if (conf) conf.checked = true; "
                "f.submit(); return 'submitted'; }"],
         "poll_js": "() => document.body.innerText.slice(0, 12000)",
         "poll_want": "All 9/9 cases green.",
         "poll_required": True,
         "poll_timeout": 25,
         "assert_js": "() => !!document.querySelector('.verdict-stamp') && "
                      "document.body.innerText.includes('All 9/9 cases green.')",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 9",
         "title": "Patterns, proven.",
         "subtitle": "regexex.py fullmatches the stored suite -- every case green passes."},
    ],
}

FRONT = 'Write a regular expression (Python `re` syntax) for `order` that matches exactly this shape: order id like `ORD-0001` (prefix `ORD-` plus exactly 4 digits).\nMust match:\n  + `ORD-0001`\n  + `ORD-8364`\n  + `ORD-1234`\n  + `ORD-9999`\nMust reject:\n  - `ORD-123`\n  - `ORD-12345`\n  - `ord-1234`\n  - `ORD-12AB`\n  - ` ORD-1234`\nReply with the pattern alone \u2014 bare, no `/slashes/`, no flags.'
BACK = 'ORD-[0-9]{4}  (model answer \u2014 any pattern going green on every case above counts).'
PAYLOAD = {'shape': 'order id like `ORD-0001` (prefix `ORD-` plus exactly 4 digits)', 'reference': 'ORD-[0-9]{4}', 'positives': ['ORD-0001', 'ORD-8364', 'ORD-1234', 'ORD-9999'], 'negatives': ['ORD-123', 'ORD-12345', 'ord-1234', 'ORD-12AB', ' ORD-1234'], 'grounded': True}
ANSWER = 'ORD-[0-9]{4}'


def seed_db(db_path: str) -> dict:
    """Plant one type-54 card (generate() bytes) as the sole due card."""
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
            " VALUES(?, ?, '54', ?, ?, ?, '2000-01-01T00:00:00Z')",
            (CARD_ID, row[0], FRONT, BACK, json.dumps(PAYLOAD)))
        con.commit()
        return {"seeded": True, "card_id": CARD_ID,
                "answer_js": json.dumps(json.dumps(ANSWER))[1:-1]}
    finally:
        con.close()
