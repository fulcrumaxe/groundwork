"""Feature demo: secret-scan (F-27, type 50).

Full behavior: one snippet line leaks a credential -- quote the
exact value (or its line). Exact match after quote/whitespace
normalization; snippet dumps never pass. seed_db plants a static
type-50 card (generate() bytes, found mode) as the sole due card;
terminal runs accept + reject, /due submits the value and polls
the exact-match verdict.
"""
from __future__ import annotations

import json
import sqlite3

CARD_ID = "demo-secretscan-50"

SCENARIO = {
    "id": "secretscan",
    "kind": "feature",
    "batch": 9,
    "item": "F-27",
    "title": "Secret-scan",
    "blurb": "Spot the leaked credential -- quote the exact value or its line.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 9 - Feature F-27",
         "title": "Secret-scan",
         "subtitle": "One line leaks -- quote the exact value or its line."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b9-secretscan",
         "caption": "Status homes the type: exact value-or-line, planted fakes.",
         "assert_js": "() => !!document.querySelector('#status-b9-secretscan')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "The rule in one line: exact match only -- substrings never pass.",
         "commands": [
             ["python3", "-c",
              "from types import SimpleNamespace; "
              "from groundwork import secretscan as m; "
              "c = SimpleNamespace(node_id='n-connect', "
              "name='connect', kind='function', file='svc.py', line=1); "
              "e = m.generate('demo-secretscan-50', c, ['def connect():', '    api_key = \"hunter2-readonly\"', '    return api_key'], {}); "
              "print(m.grade(e, 'hunter2-readonly')['feedback']); "
              "print(m.grade(e, 'password123')['feedback'])"],
         ]},
        {"type": "chrome", "duration": 8,
         "url_path": "/due",
         "focus": "#card-{seed_card_id}",
         "caption": "The scan card: the numbered snippet on the front, your quote below.",
         "assert_js": "() => { const f = document.querySelector("
                      "\"form[action='/cards/{seed_card_id}/review']\"); "
                      "return !!f && !!f.querySelector(\"input[name='answer']\") && "
                      "document.body.innerText.includes('leaks a credential'); }",
         "assert_want": "True"},
        {"type": "chrome", "duration": 13,
         "url_path": "/due",
         "caption": "The exact leaked value -- the verdict takes the quote.",
         "js": ["() => { const f = document.querySelector(\"form[action='/cards/{seed_card_id}/review']\"); "
                "if (!f) return 'seed-form-missing'; "
                "const inp = f.querySelector(\"input[name='answer']\"); "
                "if (!inp) return 'no-input'; inp.value = {seed_answer_js}; "
                "const conf = f.querySelector(\"input[name='confidence'][value='4']\"); "
                "if (conf) conf.checked = true; "
                "f.submit(); return 'submitted'; }"],
         "poll_js": "() => document.body.innerText.slice(0, 12000)",
         "poll_want": "Exact secret value.",
         "poll_required": True,
         "poll_timeout": 25,
         "assert_js": "() => !!document.querySelector('.verdict-stamp') && "
                      "document.body.innerText.includes('Exact secret value.')",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 9",
         "title": "Leaks, quoted.",
         "subtitle": "secretscan.py grades exact value-or-line -- dumps never pass."},
    ],
}

FRONT = 'One line below leaks a credential. Reply with the EXACT leaked value (or its line number).\n```python\n1: def connect():\n2:     api_key = "hunter2-readonly"\n3:     return api_key\n```'
BACK = 'Leaked value `hunter2-readonly` on line 2 (found).'
PAYLOAD = {'snippet': '1: def connect():\n2:     api_key = "hunter2-readonly"\n3:     return api_key', 'secret': 'hunter2-readonly', 'leak_line': 2, 'mode': 'found', 'grounded': True}
ANSWER = 'hunter2-readonly'


def seed_db(db_path: str) -> dict:
    """Plant one type-50 card (generate() bytes) as the sole due card."""
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
            " VALUES(?, ?, '50', ?, ?, ?, '2000-01-01T00:00:00Z')",
            (CARD_ID, row[0], FRONT, BACK, json.dumps(PAYLOAD)))
        con.commit()
        return {"seeded": True, "card_id": CARD_ID,
                "answer_js": json.dumps(json.dumps(ANSWER))[1:-1]}
    finally:
        con.close()
