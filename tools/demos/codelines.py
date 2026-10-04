"""Improvement demo: code block line numbers (I-61).

Full behavior: every lesson and exercise code block numbers its
lines via CSS counters -- each pre resets, each .codeline span
increments, the gutter paints the value -- with no JavaScript and
no web.py edits. Gutter numbers carry user-select:none so copies
stay clean, and the Batch 1 Copy button is untouched. seed_db finds
a module whose lessons carry fenced code; the module page numbers it.
"""
from __future__ import annotations

import json
import sqlite3

SCENARIO = {
    "id": "codelines",
    "kind": "improvement",
    "batch": 10,
    "item": "I-61",
    "title": "Code line numbers",
    "blurb": "Every code block numbers its lines -- CSS counters, clean copies.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 10 - Improvement I-61",
         "title": "Code line numbers",
         "subtitle": "Lines, numbered -- counters paint the gutter, copies stay clean."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b10-codelines",
         "caption": "Status documents the counters: reset, increment, selection-proof gutter.",
         "assert_js": "() => !!document.querySelector('#status-b10-codelines')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "The rule in one line: escaped lines in spans, innerText unchanged, copies clean.",
         "commands": [
             ["python3", "-c",
              "from groundwork import codelines as m; "
              "print(m.numbered_html('a = 1\\nb = 2')); "
              "print('lines:', m.line_count('a\\nb\\nc'), m.line_count(''))"],
         ]},
        {"type": "chrome", "duration": 12,
         "url_path": "/modules/{seed_module_id}?level=3",
         "focus": "pre:has(.codeline)",
         "caption": "Lesson source numbers itself -- the same blocks keep their Copy button.",
         "assert_js": "() => !!document.querySelector('pre .codeline')",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 10",
         "title": "Count on every line.",
         "subtitle": "codelines.py wraps the lines -- CSS paints the numbers."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Return one module id whose lessons carry source to number.

    Level 3 renders each lesson's Source block through numbered_html,
    so the seed picks the first module with a non-empty lesson source.
    """
    con = sqlite3.connect(db_path)
    try:
        for mid, lessons in con.execute(
                "SELECT id, lessons FROM modules ORDER BY rowid"):
            try:
                items = json.loads(lessons or "[]")
            except ValueError:
                continue
            if any(isinstance(L, dict) and str(L.get("source") or "").strip()
                   for L in items):
                return {"seeded": True, "module_id": mid}
        return {"seeded": False, "reason": "no sourced lessons"}
    finally:
        con.close()
