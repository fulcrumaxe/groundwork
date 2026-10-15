"""Improvement demo: side-by-side compare panes (I-169).

Full behavior: type-22 cards show Version A against Version B in
paired panes that scroll in step (independent panes without JS).
seed_db plants one fenced-front etype-22 card as the sole due card.
"""
from __future__ import annotations

import json
import sqlite3

CARD_ID = "demo-comparesplit-169"

FRONT = ("Which version is correct, and why?\n\n"
         "**Version A:**\n```python\nx = 1\ny = 2\n```\n\n"
         "**Version B:**\n```python\nx = 1\ny = 3\n```")

SCENARIO = {
    "id": "comparesplit",
    "kind": "improvement",
    "batch": 25,
    "item": "I-169",
    "title": "Compare panes, in step",
    "blurb": "A vs B side by side, scrolling together.",
    "beats": [
        {"type": "title", "duration": 4,
         "kicker": "Batch 25 - Improvement I-169",
         "title": "Compare panes, in step",
         "subtitle": "No more stacked blob -- A against B, synced."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b25-comparesplit",
         "caption": "Status shows live panes on a two-line fixture.",
         "assert_js": "() => !!document.querySelector('#status-b25-comparesplit') "
                      "&& !!document.querySelector('.csplit')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "Fences parse to versions; diff rows align and pad.",
         "commands": [
             ["python3", "-c",
              "from groundwork import comparesplit as m; "
              "a, b = m.parse_versions('**Version A:**\\n```\\nx\\n```\\n**Version B:**\\n```\\ny\\n```'); print('A:', repr(a), '| B:', repr(b)); "
              "print('unparseable:', m.parse_versions('no fences here')); "
              "print('blank panes:', repr(m.panes_html('', '')))"],
         ]},
        {"type": "chrome", "duration": 10,
         "url_path": "/due",
         "focus": "form[action='/cards/{seed_card_id}/review']",
         "caption": "The due compare card: A left, B right, diffs bold.",
         "assert_js": "() => !!document.querySelector(\"form[action='/cards/{seed_card_id}/review'] .csplit\") "
                      "&& document.body.innerText.includes('Version A') "
                      "&& document.body.innerText.includes('Version B')",
         "assert_want": "True"},
        {"type": "title", "duration": 4,
         "kicker": "Groundwork - Batch 25",
         "title": "Compare, don't scroll-hunt.",
         "subtitle": "comparesplit.py links the panes -- degrades clean."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Plant one fenced compare card as the sole due card."""
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
            " VALUES(?, ?, '22', ?, ?, ?, '2000-01-01T00:00:00Z')",
            (CARD_ID, row[0], FRONT, "B: y must be 3.",
             json.dumps({})))
        con.commit()
        return {"seeded": True, "card_id": CARD_ID}
    finally:
        con.close()
