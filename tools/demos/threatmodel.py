"""Feature demo: threat-model the function (F-26, type 49).

Full behavior: list a function's abuse cases against the static
checklist -- code injection plus unvalidated input here -- graded
with per-item partial credit. seed_db plants a static type-49 card
(generate() bytes) as the sole due card; terminal runs accept +
reject, /due submits the short answer and polls the 2/2 verdict.
"""
from __future__ import annotations

import json
import sqlite3

CARD_ID = "demo-threatmodel-49"

SCENARIO = {
    "id": "threatmodel",
    "kind": "feature",
    "batch": 9,
    "item": "F-26",
    "title": "Threat modelling",
    "blurb": "List a function's abuse cases -- injections, auth gaps, secrets.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 9 - Feature F-26",
         "title": "Threat modelling",
         "subtitle": "Name the abuse cases -- injections, auth gaps, secrets."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b9-threatmodel",
         "caption": "Status homes the type: abuse cases against a static checklist.",
         "assert_js": "() => !!document.querySelector('#status-b9-threatmodel')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "The rule in one line: name at least half the checklist, keys folded.",
         "commands": [
             ["python3", "-c",
              "from types import SimpleNamespace; "
              "from groundwork import threatmodel as m; "
              "c = SimpleNamespace(node_id='n-run_query', "
              "name='run_query', kind='function', file='svc.py', line=1); "
              "e = m.generate('demo-threatmodel-49', c, ['def run_query(q):', '    return eval(q)'], {}); "
              "print(m.grade(e, 'code injection and unvalidated input')['feedback']); "
              "print(m.grade(e, 'uses encryption')['feedback'])"],
         ]},
        {"type": "chrome", "duration": 8,
         "url_path": "/due",
         "focus": "#card-{seed_card_id}",
         "caption": "The threat card: the function on the front, your list below.",
         "assert_js": "() => { const f = document.querySelector("
                      "\"form[action='/cards/{seed_card_id}/review']\"); "
                      "return !!f && !!f.querySelector(\"input[name='answer']\") && "
                      "document.body.innerText.includes('Threat-model'); }",
         "assert_want": "True"},
        {"type": "chrome", "duration": 13,
         "url_path": "/due",
         "caption": "Code injection plus unvalidated input -- the verdict takes the model.",
         "js": ["() => { const f = document.querySelector(\"form[action='/cards/{seed_card_id}/review']\"); "
                "if (!f) return 'seed-form-missing'; "
                "const inp = f.querySelector(\"input[name='answer']\"); "
                "if (!inp) return 'no-input'; inp.value = {seed_answer_js}; "
                "const conf = f.querySelector(\"input[name='confidence'][value='4']\"); "
                "if (conf) conf.checked = true; "
                "f.submit(); return 'submitted'; }"],
         "poll_js": "() => document.body.innerText.slice(0, 12000)",
         "poll_want": "Full threat model (2/2 items).",
         "poll_required": True,
         "poll_timeout": 25,
         "assert_js": "() => !!document.querySelector('.verdict-stamp') && "
                      "document.body.innerText.includes('Full threat model (2/2 items).')",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 9",
         "title": "Threats, named.",
         "subtitle": "threatmodel.py checklists abuse cases -- eval, shell, SQL, URLs, files."},
    ],
}

FRONT = 'Threat-model `run_query`: list its abuse cases (2 threat-model items, one per line).\n```python\ndef run_query(q):\n    return eval(q)\n```'
BACK = '1. Code injection: untrusted input reaches eval()/exec()/compile()\n2. Unvalidated input: parameter reaches a sink unguarded'
PAYLOAD = {'items': ['Code injection: untrusted input reaches eval()/exec()/compile()', 'Unvalidated input: parameter reaches a sink unguarded'], 'keys': [['code injection', 'eval', 'exec'], ['unvalidated', 'validation', 'sanitize', 'no check']], 'solution': ['Code injection: untrusted input reaches eval()/exec()/compile()', 'Unvalidated input: parameter reaches a sink unguarded'], 'surface': ['code-injection', 'unvalidated-input'], 'grounded': True}
ANSWER = 'code injection and unvalidated input'


def seed_db(db_path: str) -> dict:
    """Plant one type-49 card (generate() bytes) as the sole due card."""
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
            " VALUES(?, ?, '49', ?, ?, ?, '2000-01-01T00:00:00Z')",
            (CARD_ID, row[0], FRONT, BACK, json.dumps(PAYLOAD)))
        con.commit()
        return {"seeded": True, "card_id": CARD_ID,
                "answer_js": json.dumps(json.dumps(ANSWER))[1:-1]}
    finally:
        con.close()
