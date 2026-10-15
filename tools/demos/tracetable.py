"""Improvement demo: trace tables (I-165).

Full behavior: trace cards pre-fill each step row with its source
line, and a miss marks every cell -- "2/3 steps right -- step 2:
expected '3', you gave '4'". seed_db plants one etype-9 card as the
sole due card; the verdict beat submits one wrong cell.
"""
from __future__ import annotations

import json
import sqlite3

CARD_ID = "demo-tracetable-165"

PAYLOAD = {"expected": ["1", "3", "9"],
           "code": "x = 1\nx = x + 2\nx = x * 3",
           "var": "x"}

SCENARIO = {
    "id": "tracetable",
    "kind": "improvement",
    "batch": 25,
    "item": "I-165",
    "title": "Trace tables",
    "blurb": "Prefilled step rows; a miss marks every cell.",
    "beats": [
        {"type": "title", "duration": 4,
         "kicker": "Batch 25 - Improvement I-165",
         "title": "Trace tables",
         "subtitle": "Each step shows its line -- fill only the values."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b25-tracetable",
         "caption": "Status carries the fixed fixture: summary plus cells.",
         "assert_js": "() => !!document.querySelector('#status-b25-tracetable') "
                      "&& document.body.innerText.includes('steps right')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "Display-only: cell marks reuse the grader verdict.",
         "commands": [
             ["python3", "-c",
              "from groundwork import tracetable as m; "
              "rows = m.per_cell(['1', '3', '9'], '1\\n4\\n9'); "
              "print(m.summary_line(rows)); "
              "print('cells:', sum(1 for r in rows if r['passed']), 'of', len(rows))"],
         ]},
        {"type": "chrome", "duration": 10,
         "url_path": "/due",
         "js": ["() => { const f = document.querySelector(\"form[action='/cards/{seed_card_id}/review']\"); "
                "if (!f) return 'seed-form-missing'; "
                "f.querySelector('input[name=s0]').value = '1'; "
                "f.querySelector('input[name=s1]').value = '4'; "
                "f.querySelector('input[name=s2]').value = '9'; "
                "const conf = f.querySelector(\"input[name='confidence'][value='3']\"); "
                "if (conf) conf.checked = true; "
                "f.submit(); return 'submitted'; }"],
         "caption": "One wrong cell -- the verdict names exactly which step.",
         "poll_js": "() => document.body.innerText.slice(0, 12000)",
         "poll_want": "steps right",
         "poll_required": True,
         "poll_timeout": 25,
         "assert_js": "() => document.body.innerText.includes(\"step 2: expected '3', you gave '4'\")",
         "assert_want": "True"},
        {"type": "title", "duration": 4,
         "kicker": "Groundwork - Batch 25",
         "title": "See the divergence.",
         "subtitle": "tracetable.py explains -- pass/fail stays with grade."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Plant one trace card as the sole due card."""
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
            " VALUES(?, ?, '9', ?, ?, ?, '2000-01-01T00:00:00Z')",
            (CARD_ID, row[0],
             "Trace x: x = 1; x = x + 2; x = x * 3.",
             "1, 3, 9",
             json.dumps(PAYLOAD)))
        con.commit()
        return {"seeded": True, "card_id": CARD_ID}
    finally:
        con.close()
