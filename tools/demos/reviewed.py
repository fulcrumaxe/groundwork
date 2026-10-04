"""Improvement demo: mark as reviewed (I-17).

Full behavior: re-reading a lesson ticks it reviewed without
answering -- a per-lesson button stores a private mark in
localStorage, with no grade, no scheduling change, and no database
write. The interaction beat clicks the control and polls the stored
mark plus the Reviewed label.
"""
from __future__ import annotations

import sqlite3

SCENARIO = {
    "id": "reviewed",
    "kind": "improvement",
    "batch": 7,
    "item": "I-17",
    "title": "Mark as reviewed",
    "blurb": "Re-read a lesson? Tick it reviewed -- no answer, no grade, kept in your browser.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 7 - Improvement I-17",
         "title": "Mark as reviewed",
         "subtitle": "Re-read it, tick it -- no answer, no grade, no due-date moved."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b7-reviewed",
         "caption": "Status documents the improvement: browser-local marks, never known_skips.",
         "assert_js": "() => !!document.querySelector('#status-b7-reviewed')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "The rule in one line: one localStorage key per concept, nothing on the server.",
         "commands": [
             ["python3", "-c",
              "from groundwork import reviewed as m; "
              "print(m.storage_key('groundwork/web.py:page')); "
              "print('no POST, no grade -- localStorage only')"],
         ]},
        {"type": "chrome", "duration": 7,
         "url_path": "/modules/{seed_module_id}",
         "focus": ".reviewed-control",
         "caption": "Each lesson carries its tick -- button plus a quiet explainer.",
         "assert_js": "() => !!document.querySelector('.reviewed-control') && "
                      "!!document.querySelector('[data-reviewed-btn]')",
         "assert_want": "True"},
        {"type": "chrome", "duration": 13,
         "url_path": "/modules/{seed_module_id}",
         "focus": ".reviewed-control",
         "caption": "Tick it -- the mark lands in localStorage and the label flips.",
         "js": ["() => { const b = document.querySelector('[data-reviewed-btn]'); "
                "if (!b) return 'no-button'; b.click(); return 'ticked'; }"],
         "poll_js": "() => localStorage.getItem(document.querySelector("
                    "'.reviewed-control').getAttribute('data-reviewed-key')) || 'empty'",
         "poll_want": "1",
         "poll_required": True,
         "poll_timeout": 25,
         "assert_js": "() => document.querySelector('[data-reviewed-btn]').textContent === 'Reviewed'",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 7",
         "title": "Re-reads count quietly.",
         "subtitle": "reviewed.py hydrates from localStorage -- click again to clear."},
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
