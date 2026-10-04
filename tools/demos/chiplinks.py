"""Improvement demo: concept-chip lesson links (I-22).

Full behavior: every concept's status chip on its module page links
to /modules/<mid>#lesson-<slug> -- the lesson section it already
sits in -- so chips are deep links, not plain text. The click beat
follows a chip and polls the lesson fragment.
"""
from __future__ import annotations

import sqlite3

SCENARIO = {
    "id": "chiplinks",
    "kind": "improvement",
    "batch": 7,
    "item": "I-22",
    "title": "Concept chips link to lessons",
    "blurb": "Every concept's status chip jumps straight to its lesson section.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 7 - Improvement I-22",
         "title": "Concept chips link to lessons",
         "subtitle": "The chip is the deep link -- jump straight to its lesson."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b7-chiplinks",
         "caption": "Status documents the improvement: chips point at their lesson anchors.",
         "assert_js": "() => !!document.querySelector('#status-b7-chiplinks')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "The rule in one line: slug mirrors lessons.slug, blank ids fail closed.",
         "commands": [
             ["python3", "-c",
              "from groundwork import chiplinks as m; "
              "print(m.chip_href('abc123', 'Answer Widget')); "
              "print(repr(m.chip_href('', 'Answer Widget')))"],
         ]},
        {"type": "chrome", "duration": 7,
         "url_path": "/modules/{seed_module_id}",
         "focus": "section[id^='lesson-']",
         "caption": "Chips beside each lesson -- wrapped in links, not plain text.",
         "assert_js": "() => !!document.querySelector(\"a[href*='/modules/'][href*='#lesson-']\")",
         "assert_want": "True"},
        {"type": "chrome", "duration": 13,
         "url_path": "/modules/{seed_module_id}",
         "focus": "#demo-target",
         "caption": "Click a chip -- the page jumps to its lesson section.",
         "js": ["() => { const a = document.querySelector(\"a[href*='/modules/'][href*='#lesson-']\"); "
                "if (!a) return 'no-chip-link'; a.click(); "
                "const t = document.getElementById(location.hash.slice(1)); "
                "if (!t) return 'no-target'; t.id = 'demo-target'; return 'clicked'; }"],
         "poll_js": "() => location.hash",
         "poll_want": "lesson-",
         "poll_required": True,
         "poll_timeout": 25,
         "assert_js": "() => location.hash.indexOf('lesson-') === 1",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 7",
         "title": "Chips go somewhere.",
         "subtitle": "chiplinks.py mirrors the lesson slug -- hrefs always match anchors."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Return one module id with at least one concept for the lesson page."""
    con = sqlite3.connect(db_path)
    try:
        row = con.execute(
            "SELECT m.id FROM modules m JOIN concepts c"
            " ON c.module_id = m.id ORDER BY m.rowid LIMIT 1").fetchone()
        if not row:
            return {"seeded": False, "reason": "no modules"}
        return {"seeded": True, "module_id": row[0]}
    finally:
        con.close()
