"""Feature demo: input-validation audit (F-28, type 51).

Full behavior: read one function, list every input that reaches a
sensitive sink without validation -- path reaches open() here --
graded against the AST checklist with per-name partial credit.
seed_db plants a static type-51 card (generate() bytes) as the sole
due card; terminal runs accept + reject, /due submits the name and
polls the 1/1 verdict.
"""
from __future__ import annotations

import json
import sqlite3

CARD_ID = "demo-inputaudit-51"

SCENARIO = {
    "id": "inputaudit",
    "kind": "feature",
    "batch": 9,
    "item": "F-28",
    "title": "Input-validation audit",
    "blurb": "Spot the inputs that reach dangerous sinks without validation.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 9 - Feature F-28",
         "title": "Input-validation audit",
         "subtitle": "Which inputs reach the sinks unvalidated?"},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b9-inputaudit",
         "caption": "Status homes the type: inputs vs sinks, AST-graded.",
         "assert_js": "() => !!document.querySelector('#status-b9-inputaudit')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "The rule in one line: exact unvalidated set -- partial credit per name.",
         "commands": [
             ["python3", "-c",
              "from types import SimpleNamespace; "
              "from groundwork import inputaudit as m; "
              "c = SimpleNamespace(node_id='n-load', "
              "name='load', kind='function', file='svc.py', line=1); "
              "e = m.generate('demo-inputaudit-51', c, ['def load(path):', '    return open(path).read()'], {}); "
              "print(m.grade(e, 'path')['feedback']); "
              "print(m.grade(e, 'mode')['feedback'])"],
         ]},
        {"type": "chrome", "duration": 8,
         "url_path": "/due",
         "focus": "#card-{seed_card_id}",
         "caption": "The audit card: the function on the front, your names below.",
         "assert_js": "() => { const f = document.querySelector("
                      "\"form[action='/cards/{seed_card_id}/review']\"); "
                      "return !!f && !!f.querySelector(\"input[name='answer']\") && "
                      "document.body.innerText.includes('Audit the inputs'); }",
         "assert_want": "True"},
        {"type": "chrome", "duration": 13,
         "url_path": "/due",
         "caption": "path reaches open() unvalidated -- the verdict takes the audit.",
         "js": ["() => { const f = document.querySelector(\"form[action='/cards/{seed_card_id}/review']\"); "
                "if (!f) return 'seed-form-missing'; "
                "const inp = f.querySelector(\"input[name='answer']\"); "
                "if (!inp) return 'no-input'; inp.value = {seed_answer_js}; "
                "const conf = f.querySelector(\"input[name='confidence'][value='4']\"); "
                "if (conf) conf.checked = true; "
                "f.submit(); return 'submitted'; }"],
         "poll_js": "() => document.body.innerText.slice(0, 12000)",
         "poll_want": "Full audit (1/1 unvalidated inputs found).",
         "poll_required": True,
         "poll_timeout": 25,
         "assert_js": "() => !!document.querySelector('.verdict-stamp') && "
                      "document.body.innerText.includes('Full audit (1/1 unvalidated inputs found).')",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 9",
         "title": "Inputs, traced.",
         "subtitle": "inputaudit.py checklists sink-reaching inputs -- AST-derived, no sandbox."},
    ],
}

FRONT = 'Audit the inputs: list every input that reaches a sensitive sink (eval, exec, open, subprocess, sql) WITHOUT validation \u2014 one name per line.\n```python\n1: def load(path):\n2:     return open(path).read()\n```'
BACK = '0=path'
PAYLOAD = {'checklist': [{'id': 0, 'name': 'path', 'sink': 'open', 'line': 2}], 'sinks': ['eval', 'exec', 'open', 'subprocess', 'sql'], 'grounded': True}
ANSWER = 'path'


def seed_db(db_path: str) -> dict:
    """Plant one type-51 card (generate() bytes) as the sole due card."""
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
            " VALUES(?, ?, '51', ?, ?, ?, '2000-01-01T00:00:00Z')",
            (CARD_ID, row[0], FRONT, BACK, json.dumps(PAYLOAD)))
        con.commit()
        return {"seeded": True, "card_id": CARD_ID,
                "answer_js": json.dumps(json.dumps(ANSWER))[1:-1]}
    finally:
        con.close()
