"""Improvement demo: real code editor for code-writing cards (I-154).

Full behavior: code branches (12/14/19/20/23) answer in a monospace
editor with a line-number gutter and Tab-to-indent, posting the same
name='answer' field so grading is unchanged. seed_db plants one
type-12 card as the sole due card; /due shows the editor.
"""
from __future__ import annotations

import json
import sqlite3

CARD_ID = "demo-codeedit-154"

SCENARIO = {
    "id": "codeedit",
    "kind": "improvement",
    "batch": 24,
    "item": "I-154",
    "title": "Real code editor",
    "blurb": "Monospace, line numbers, Tab indents -- same answer field.",
    "beats": [
        {"type": "title", "duration": 4,
         "kicker": "Batch 24 - Improvement I-154",
         "title": "Real code editor",
         "subtitle": "Tab indents, the gutter counts -- grading never notices."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b24-codeedit",
         "caption": "Status homes the editor: gutter plus textarea, same POST.",
         "assert_js": "() => !!document.querySelector('#status-b24-codeedit')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "Five code branches upgrade; line counts and markup stay pure.",
         "commands": [
             ["python3", "-c",
              "from groundwork import codeedit as m; "
              "print('code12:', m.is_code_type('12'), '| text5:', m.is_code_type('5')); "
              "print('lines:', m.line_count('a\\nb\\nc')); "
              "print(m.editor_html('x = 1')[:140])"],
         ]},
        {"type": "chrome", "duration": 10,
         "url_path": "/due",
         "focus": ".codeedit",
         "caption": "The lead card answers in the editor: gutter, mono input, Tab.",
         "assert_js": "() => !!document.querySelector("
                      "'.codeedit .codeedit-input') "
                      "&& !!document.querySelector('.codeedit-gutter')",
         "assert_want": "True"},
        {"type": "title", "duration": 4,
         "kicker": "Groundwork - Batch 24",
         "title": "Write code like code.",
         "subtitle": "codeedit.py upgrades the box -- the field keeps its name."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Plant one type-12 card as the sole due card."""
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
            " VALUES(?, ?, '12', ?, ?, ?, '2000-01-01T00:00:00Z')",
            (CARD_ID, row[0],
             "Implement add(a, b) so the hidden tests pass.",
             "def add(a, b):\n    return a + b",
             json.dumps({"stub": "def add(a, b):\n    pass",
                         "tests": "assert add(1, 2) == 3"})))
        con.commit()
        return {"seeded": True, "card_id": CARD_ID}
    finally:
        con.close()
