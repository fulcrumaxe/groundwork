"""Improvement demo: Parsons partial-order check (I-163).

Full behavior: an ungraded "Check partial order" button reports the
longest submitted block that also sits contiguously in truth --
"longest correct run: 2 of 4" -- without grading or revealing the
answer. seed_db plants one etype-11 card whose shown order holds a
2-long correct run as the sole due card.
"""
from __future__ import annotations

import json
import sqlite3

CARD_ID = "demo-parcheck-163"

LINES = ["import os", "def main():", "    run()", "main()"]
PAYLOAD = {"lines": LINES,
           "solution": [LINES[0], LINES[1], LINES[3], LINES[2]]}

SCENARIO = {
    "id": "parcheck",
    "kind": "improvement",
    "batch": 25,
    "item": "I-163",
    "title": "Parsons partial-order check",
    "blurb": "Stuck mid-reorder? See your longest correct run, ungraded.",
    "beats": [
        {"type": "title", "duration": 4,
         "kicker": "Batch 25 - Improvement I-163",
         "title": "Parsons partial-order check",
         "subtitle": "Keep that block, move the rest -- no grade, no reveal."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b25-parcheck",
         "caption": "Status names the scan: longest run, client-side.",
         "assert_js": "() => !!document.querySelector('#status-b25-parcheck') "
                      "&& document.body.innerText.includes('longest correct run')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "Truth-adjacency scan: only contiguous blocks count.",
         "commands": [
             ["python3", "-c",
              "from groundwork import parcheck as m; "
              "print(m.longest_correct_run([0, 1, 2, 3], [0, 1, 3, 2])); "
              "print(m.message(2, 4)); "
              "print('truth idx:', m.truth_indices(list('abcd'), list('abdc')))"],
         ]},
        {"type": "chrome", "duration": 10,
         "url_path": "/due",
         "js": ["() => { const f = document.querySelector(\"form[action='/cards/{seed_card_id}/review']\"); "
                "if (!f) return 'seed-form-missing'; "
                "const b = f.querySelector('button[data-parcheck]'); "
                "if (!b) return 'no-button'; b.click(); return 'clicked'; }"],
         "focus": "form[action='/cards/{seed_card_id}/review']",
         "caption": "One click names the run: 2 of 4 -- keep it, move the rest.",
         "poll_js": "() => document.querySelector(\"form[action='/cards/{seed_card_id}/review']\").innerText",
         "poll_want": "longest correct run",
         "poll_required": True,
         "assert_js": "() => document.querySelector(\"form[action='/cards/{seed_card_id}/review']\").innerText"
                      ".includes('longest correct run: 2 of 4')",
         "assert_want": "True"},
        {"type": "title", "duration": 4,
         "kicker": "Groundwork - Batch 25",
         "title": "Hints, not verdicts.",
         "subtitle": "parcheck.py scans client-side -- grading stays server-side."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Plant one Parsons card holding a 2-long correct run, sole due."""
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
            " VALUES(?, ?, '11', ?, ?, ?, '2000-01-01T00:00:00Z')",
            (CARD_ID, row[0],
             "Put the lines in order: import, define main, run it.",
             "import os; def main(): run(); main()",
             json.dumps(PAYLOAD)))
        con.commit()
        return {"seeded": True, "card_id": CARD_ID}
    finally:
        con.close()
