"""Improvement demo: char/line counts (I-153).

Pure server-side count helper: count_meta(text) returns chars,
lines and words; textarea_hint renders the one-line size hint.
Video: Status anchor, live counts, edge cases, tour catalog.
"""
from __future__ import annotations

import sqlite3

SCENARIO = {
    "id": "charcount",
    "kind": "improvement",
    "batch": 5,
    "item": "I-153",
    "title": "Char and line counts",
    "blurb": "Code textareas report chars, lines and words as you type.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 5 - Improvement I-153",
         "title": "Char and line counts",
         "subtitle": "Code textareas report chars, lines and words as you type."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b5-charcount",
         "caption": "Status documents the improvement with its live anchor.",
         "assert_js": "() => !!document.querySelector('#status-b5-charcount')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 8,
         "caption": "The helper in one call: chars, lines and words for textarea text.",
         "commands": [
             ["python3", "-c",
              "from groundwork import charcount as m; "
              "print(m.count_meta('hi\\nthere you')); "
              "print(m.textarea_hint('hi\\nthere you'))"],
         ]},
        {"type": "terminal", "duration": 7,
         "caption": "Empty and missing text count as zero -- the hint still renders.",
         "commands": [
             ["python3", "-c",
              "from groundwork import charcount as m; "
              "print(m.count_meta('')); "
              "print(m.count_meta(None)); "
              "print(m.textarea_hint(''))"],
         ]},
        {"type": "chrome", "duration": 6,
         "url_path": "/tour",
         "caption": "The tour catalog lists Char counts with a Show-me link.",
         "js": ["() => { const li = [...document.querySelectorAll('li')].find("
                "l => l.innerText.includes('Char counts')); "
                "if (!li) return 'missing'; li.id = 'tour-hit'; return 'tagged'; }"],
         "focus": "#tour-hit",
         "assert_js": "() => { const li = document.querySelector('#tour-hit'); "
                      "return !!li && li.innerText.includes('Show me'); }",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 5",
         "title": "Writer size feedback.",
         "subtitle": "charcount.py counts the text -- no I/O, no DB changes."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Pure helper: no fixture state needed; verify the library opens."""
    con = sqlite3.connect(db_path)
    try:
        row = con.execute("SELECT COUNT(*) FROM cards").fetchone()
        return {"seeded": True, "cards": row[0] if row else 0}
    finally:
        con.close()
