"""Improvement demo: lesson pager (I-8).

Full behavior: each lesson article ends with a previous/next pager --
deep #lesson-{slug} links plus a "Lesson i of n" position note, no JS
needed. Beats show the Status home, the pure neighbors() rule, the
live pager, and a real pager click that moves the hash.
"""
from __future__ import annotations

import sqlite3

SCENARIO = {
    "id": "pager",
    "kind": "improvement",
    "batch": 6,
    "item": "I-8",
    "title": "Lesson pager",
    "blurb": "Walk a module one lesson at a time -- previous, next, position.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 6 - Improvement I-8",
         "title": "Lesson pager",
         "subtitle": "Each lesson ends with previous/next -- walk, don't scroll."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b6-pager",
         "caption": "Status names the parts: neighbours plus a position note.",
         "assert_js": "() => !!document.querySelector('#status-b6-pager')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "The rule in one line: ends have one neighbour, middles two.",
         "commands": [
             ["python3", "-c",
              "from groundwork import pager as m; "
              "print(m.neighbors(['a', 'b', 'c'], 0)); "
              "print(m.neighbors(['a', 'b', 'c'], 1)); "
              "print(m.neighbors(['a'], 0))"],
         ]},
        {"type": "chrome", "duration": 7,
         "url_path": "/modules/{seed_mid}",
         "focus": "#pager",
         "caption": "The live pager: neighbours as deep links, position in words.",
         "assert_js": "() => { const n = document.querySelector('#pager'); "
                      "return !!n && n.textContent.includes('Lesson 1 of'); }",
         "assert_want": "True"},
        {"type": "chrome", "duration": 13,
         "url_path": "/modules/{seed_mid}",
         "focus": "#pager",
         "caption": "Click next -- the hash walks to the neighbouring lesson.",
         "js": ["() => { const a = document.querySelector("
                "'nav.lesson-pager a[rel=\"next\"]'); "
                "if (!a) return 'no-next'; a.click(); return 'clicked'; }"],
         "poll_js": "() => location.hash",
         "poll_want": "lesson-",
         "poll_required": True,
         "poll_timeout": 25,
         "assert_js": "() => location.hash.includes('lesson-')",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 6",
         "title": "One card at a time.",
         "subtitle": "pager.py is pure HTML -- deep links work with no JS."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Pick the module with the most concepts (needs 2+ lessons)."""
    con = sqlite3.connect(db_path)
    try:
        row = con.execute(
            "SELECT module_id FROM concepts GROUP BY module_id"
            " ORDER BY COUNT(*) DESC LIMIT 1").fetchone()
        if not row:
            row = con.execute("SELECT id FROM modules LIMIT 1").fetchone()
        if not row:
            return {"seeded": False, "reason": "no modules"}
        return {"seeded": True, "mid": row[0]}
    finally:
        con.close()
