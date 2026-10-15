"""Improvement demo: touch + keyboard Parsons reorder (I-162).

Full behavior: Parsons rows carry a 44px fingertip grip
(touch-action:none), roving tabindex with Arrow/Home/End moves, and
pointer-drag -- all reusing the existing order sync. seed_db plants
one etype-11 card (lines, no solution, so the parcheck hook stays
quiet) as the sole due card.
"""
from __future__ import annotations

import json
import sqlite3

CARD_ID = "demo-parkeys-162"

PAYLOAD = {"lines": ["total = 0", "for n in nums:", "    total += n",
                     "print(total)"]}

SCENARIO = {
    "id": "parkeys",
    "kind": "improvement",
    "batch": 25,
    "item": "I-162",
    "title": "Touch + keyboard Parsons",
    "blurb": "Drag from a fat grip or reorder by keyboard -- one order sync.",
    "beats": [
        {"type": "title", "duration": 4,
         "kicker": "Batch 25 - Improvement I-162",
         "title": "Touch + keyboard Parsons",
         "subtitle": "Tab in once, arrows move the row -- or drag the grip."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b25-parkeys",
         "caption": "Status pins the contract: 44px grip, roving tabindex.",
         "assert_js": "() => !!document.querySelector('#status-b25-parkeys') "
                      "&& document.body.innerText.includes('.pkgrip')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "Fat grips, one tab stop; empty lists keep legacy bytes.",
         "commands": [
             ["python3", "-c",
              "from groundwork import parkeys as m; "
              "print('grip min px:', m.GRAB_MIN_PX); "
              "h = m.list_html('c1', ['a', 'b']); "
              "print('enhanced:', 'parkeys' in h and 'pkgrip' in h); "
              "print('legacy fallback:', 'parkeys' not in m.block_html('c1', []))"],
         ]},
        {"type": "chrome", "duration": 10,
         "url_path": "/due",
         "focus": "form[action='/cards/{seed_card_id}/review']",
         "caption": "The due Parsons card: grips, focus ring, typed fallback.",
         "assert_js": "() => !!document.querySelector("
                      "\"form[action='/cards/{seed_card_id}/review'] ol.parkeys\") "
                      "&& !!document.querySelector('.pkgrip')",
         "assert_want": "True"},
        {"type": "title", "duration": 4,
         "kicker": "Groundwork - Batch 25",
         "title": "Every input, one order.",
         "subtitle": "parkeys.py reorders DOM nodes, parsonsSync posts."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Plant one grip-enabled Parsons card as the sole due card."""
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
             "Put the lines in order: sum nums, then print the total.",
             "total = 0; for n in nums: total += n; print(total)",
             json.dumps(PAYLOAD)))
        con.commit()
        return {"seeded": True, "card_id": CARD_ID}
    finally:
        con.close()
