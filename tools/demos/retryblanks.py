"""Improvement demo: retry wrong blanks only (I-161).

Full behavior: after a failed type-2 cloze the result offers a retry
form with correct blanks locked+filled and only missed ids open;
all-correct or non-cloze cards offer nothing. seed_db plants one cloze.
"""
from __future__ import annotations

import json
import sqlite3

CARD_ID = "demo-retryblanks-161"

PAYLOAD = {"template": "Set ___(0) and ___(1) before launch.",
           "blanks": [{"id": 0, "answers": ["timeout"]},
                      {"id": 1, "answers": ["retries"]}]}

SCENARIO = {
    "id": "retryblanks",
    "kind": "improvement",
    "batch": 24,
    "item": "I-161",
    "title": "Retry wrong blanks only",
    "blurb": "Correct blanks stay locked -- retry only the miss.",
    "beats": [
        {"type": "title", "duration": 4,
         "kicker": "Batch 24 - Improvement I-161",
         "title": "Retry wrong blanks only",
         "subtitle": "Keep what you knew -- re-ask only the miss."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b24-retryblanks",
         "caption": "Status pins the rule: locked correct, open wrong.",
         "assert_js": "() => !!document.querySelector("
                      "'#status-b24-retryblanks')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 8,
         "caption": "The split names wrong ids; the form locks the rest.",
         "commands": [
             ["python3", "-c",
              "from groundwork import retryblanks as m; "
              "card = {'id': 'c1', 'payload': {'blanks': [{'id': 0, 'answers': ['timeout']}, {'id': 1, 'answers': ['retries']}]}}; "
              "print('split:', m.split_blanks(card, '0=timeout\\n1=wrng')); "
              "print(m.retry_form(card, '0=timeout\\n1=wrng')[:200])"],
         ]},
        {"type": "chrome", "duration": 9,
         "url_path": "/due",
         "focus": "form[action='/cards/{seed_card_id}/review']",
         "caption": "The lead cloze card: two blanks in, retry asks for misses.",
         "assert_js": "() => !!document.querySelector(\"input[name='b0']\") "
                      "&& !!document.querySelector(\"input[name='b1']\")",
         "assert_want": "True"},
        {"type": "title", "duration": 4,
         "kicker": "Groundwork - Batch 24",
         "title": "Only the miss, again.",
         "subtitle": "retryblanks.py locks the known -- practice the gap."},
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
