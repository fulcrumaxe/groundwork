"""Improvement demo: per-blank partial credit for cloze (I-160).

Full behavior: a failed type-2 cloze names which blanks passed in
the feedback line plus a checklist; clean cards render as before.
seed_db plants one two-blank cloze as the sole due card.
"""
from __future__ import annotations

import json
import sqlite3

CARD_ID = "demo-partial-160"

PAYLOAD = {"template": "Set ___(0) and ___(1) before launch.",
           "blanks": [{"id": 0, "answers": ["timeout"]},
                      {"id": 1, "answers": ["retries"]}]}

SCENARIO = {
    "id": "partial",
    "kind": "improvement",
    "batch": 24,
    "item": "I-160",
    "title": "Per-blank partial credit",
    "blurb": "Miss a cloze and the result names which blanks passed.",
    "beats": [
        {"type": "title", "duration": 4,
         "kicker": "Batch 24 - Improvement I-160",
         "title": "Per-blank partial credit",
         "subtitle": "Two blanks right, one to retry -- named, not graded whole."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b24-partial",
         "caption": "Status shows the fixed fixture: summary plus checklist.",
         "assert_js": "() => !!document.querySelector('#status-b24-partial') "
                      "&& document.body.innerText.includes('blanks right')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 8,
         "caption": "One record per blank; the verdict names the misses.",
         "commands": [
             ["python3", "-c",
              "from groundwork import partial as m; "
              "p = {'blanks': [{'id': 0, 'answers': ['timeout']}, {'id': 1, 'answers': ['retries']}]}; "
              "rows = m.per_blank(p, '0=timeout\\n1=wrng'); "
              "print(m.summary_line(rows)); "
              "print(m.checklist_html(rows)[:150])"],
         ]},
        {"type": "chrome", "duration": 9,
         "url_path": "/due",
         "focus": "form[action='/cards/{seed_card_id}/review']",
         "caption": "The lead cloze card asks per blank -- the surface partial grades.",
         "assert_js": "() => !!document.querySelector(\"input[name='b0']\") "
                      "&& !!document.querySelector(\"input[name='b1']\")",
         "assert_want": "True"},
        {"type": "title", "duration": 4,
         "kicker": "Groundwork - Batch 24",
         "title": "Right is right, per blank.",
         "subtitle": "partial.py names the miss -- retry only that."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Plant one two-blank cloze as the sole due card."""
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
            " VALUES(?, ?, '2', ?, ?, ?, '2000-01-01T00:00:00Z')",
            (CARD_ID, row[0],
             "Fill the blanks: Set ___(0) and ___(1) before launch.",
             "timeout, retries",
             json.dumps(PAYLOAD)))
        con.commit()
        return {"seeded": True, "card_id": CARD_ID}
    finally:
        con.close()
