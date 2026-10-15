"""Improvement demo: line comments on code review (I-168).

Full behavior: type-21 cards render each snippet line with a
clickable gutter; per-line notes serialize as L{n}: text into the
existing answer field, so the legacy grader reads them unchanged.
seed_db plants one snippeted etype-21 card as the sole due card.
"""
from __future__ import annotations

import json
import sqlite3

CARD_ID = "demo-linecomment-168"

PAYLOAD = {"snippet": "1: def total(xs):\n2:     s = 0\n3:     return s"}

SCENARIO = {
    "id": "linecomment",
    "kind": "improvement",
    "batch": 25,
    "item": "I-168",
    "title": "Line comments on review",
    "blurb": "Click a line number to pin a note, like real review.",
    "beats": [
        {"type": "title", "duration": 4,
         "kicker": "Batch 25 - Improvement I-168",
         "title": "Line comments on review",
         "subtitle": "Gutters you can click -- notes land as L-lines."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b25-linecomment",
         "caption": "Status pins the format: L{n} lines, legacy grader.",
         "assert_js": "() => !!document.querySelector('#status-b25-linecomment') "
                      "&& document.body.innerText.includes('L{n}')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "Notes round-trip; the accused line is the first integer.",
         "commands": [
             ["python3", "-c",
              "from groundwork import linecomment as m; "
              "print(repr(m.serialize_notes([(2, 'off-by-one')]))); "
              "print(m.accused_line('L2: off-by-one')); "
              "print(m.snippet_lines('1: a\\n2: b'))"],
         ]},
        {"type": "chrome", "duration": 10,
         "url_path": "/due",
         "js": ["() => { const f = document.querySelector(\"form[action='/cards/{seed_card_id}/review']\"); "
                "if (!f) return 'seed-form-missing'; "
                "const n = f.querySelector(\"input.lc-note[data-l='2']\"); "
                "if (!n) return 'no-note'; n.value = 'off-by-one'; "
                "n.setAttribute('value', n.value); "
                "n.dispatchEvent(new Event('input', {bubbles: true})); "
                "var a = f.querySelector('textarea.lc-sync'); "
                "a.textContent = a.value; return a.value; }"],
         "focus": "form[action='/cards/{seed_card_id}/review']",
         "caption": "Note line 2 -- the answer box gains an L2 line.",
         "poll_js": "() => document.querySelector(\"form[action='/cards/{seed_card_id}/review'] textarea.lc-sync\").value",
         "poll_want": "L2: off-by-one",
         "poll_required": True,
         "assert_js": "() => document.querySelector(\"form[action='/cards/{seed_card_id}/review'] textarea.lc-sync\")"
                      ".value.includes('L2: off-by-one')",
         "assert_want": "True"},
        {"type": "title", "duration": 4,
         "kicker": "Groundwork - Batch 25",
         "title": "Review like it is real.",
         "subtitle": "linecomment.py syncs notes -- same field, same grade."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Plant one snippeted review card as the sole due card."""
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
            " VALUES(?, ?, '21', ?, ?, ?, '2000-01-01T00:00:00Z')",
            (CARD_ID, row[0],
             "Review this code: which line is wrong, and why?",
             "Line 2 never accumulates; the loop body is missing.",
             json.dumps(PAYLOAD)))
        con.commit()
        return {"seeded": True, "card_id": CARD_ID}
    finally:
        con.close()
