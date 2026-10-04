"""Improvement demo: collapse answered Due cards in place (I-42).

Full behavior: answering a Due card collapses its article to a
compact answered banner with inline undo (fetch POST, same route,
same grading) instead of a full reload. seed_db plants one
type-51 card as the sole due card; the interaction beat clicks
Submit for real (native submit would skip the interception), the
banner plus undo form is polled, and the fixture DB proves the
review graded.
"""
from __future__ import annotations

import json
import sqlite3

CARD_ID = "demo-collapse-42"

SCENARIO = {
    "id": "collapse",
    "kind": "improvement",
    "batch": 9,
    "item": "I-42",
    "title": "Collapse answered cards",
    "blurb": "Answered Due cards collapse in place with inline undo -- no reload.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 9 - Improvement I-42",
         "title": "Collapse answered cards",
         "subtitle": "Answer a card -- it folds to a banner with undo."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b9-collapse",
         "caption": "Status documents the flow: same POST, same grading, new presentation.",
         "assert_js": "() => !!document.querySelector('#status-b9-collapse')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "The pieces: a compact banner plus an undo form on the kept article.",
         "commands": [
             ["python3", "-c",
              "from groundwork import collapse as m; "
              "print(m.collapsed_html('Demo concept')); "
              "print(m.undo_form_html())"],
         ]},
        {"type": "chrome", "duration": 14,
         "url_path": "/due",
         "focus": "#card-{seed_card_id} div.collapsed-answer",
         "caption": "Submit for real -- fetch grades it and the card folds to Answered.",
         "js": ["() => { const f = document.querySelector(\"form[action='/cards/{seed_card_id}/review']\"); "
                "if (!f) return 'seed-form-missing'; "
                "const inp = f.querySelector(\"input[name='answer']\"); "
                "if (!inp) return 'no-input'; inp.value = 'path'; "
                "const conf = f.querySelector(\"input[name='confidence'][value='4']\"); "
                "if (conf) conf.checked = true; "
                "const btn = f.querySelector('button'); "
                "if (!btn) return 'no-button'; btn.click(); return 'clicked'; }"],
         "poll_js": "() => !!document.querySelector('#card-{seed_card_id} div.collapsed-answer')",
         "poll_want": "True",
         "poll_required": True,
         "poll_timeout": 25,
         "assert_js": "() => !!document.querySelector('div.collapsed-answer') && "
                      "!!document.querySelector(\"form[action='/reviews/undo']\") && "
                      "document.body.innerText.includes('Undo answer')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 6,
         "caption": "Proof it graded: the review landed in the fixture DB.",
         "commands": [
             ["python3", "-c",
              "import os, sqlite3; con = sqlite3.connect(os.environ.get('DEMO_DB', 'groundwork.db')); "
              "rows = con.execute(\"SELECT grade, confidence, submission FROM reviews WHERE card_id='demo-collapse-42'\").fetchall(); "
              "print(rows)"],
         ]},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 9",
         "title": "Answered, not gone.",
         "subtitle": "collapse.py folds the card -- undo reuses POST /reviews/undo."},
    ],
}

FRONT = 'Audit the inputs: list every input that reaches a sensitive sink (eval, exec, open, subprocess, sql) WITHOUT validation \u2014 one name per line.\n```python\n1: def load(path):\n2:     return open(path).read()\n```'
BACK = '0=path'
PAYLOAD = {'checklist': [{'id': 0, 'name': 'path', 'sink': 'open', 'line': 2}], 'sinks': ['eval', 'exec', 'open', 'subprocess', 'sql'], 'grounded': True}


def seed_db(db_path: str) -> dict:
    """Plant one answerable card as the sole due card."""
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
        return {"seeded": True, "card_id": CARD_ID}
    finally:
        con.close()
