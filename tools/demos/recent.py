"""Improvement demo: recently visited strip (I-24).

Full behavior: the Due page opens with a recently-visited strip fed
only by browser localStorage (key gw-recent, capped at 8) -- module
pages log each visit, the strip renders from the log, and no cookie,
DB, or schema change is involved. The visit beat opens a module and
asserts the log entry; the strip beat reads it back on /due.
"""
from __future__ import annotations

import sqlite3

SCENARIO = {
    "id": "recent",
    "kind": "improvement",
    "batch": 7,
    "item": "I-24",
    "title": "Recently visited strip",
    "blurb": "Due opens with your last 8 modules -- kept in this browser only.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 7 - Improvement I-24",
         "title": "Recently visited strip",
         "subtitle": "Open a module, see it on Due -- the trail never leaves the browser."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b7-recent",
         "caption": "Status documents the improvement: localStorage only, capped at 8.",
         "assert_js": "() => !!document.querySelector('#status-b7-recent')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "The rule in one line: most-recent first, deduped by id, capped.",
         "commands": [
             ["python3", "-c",
              "from groundwork import recent as m; "
              "print(m.clip([{'id': 'b'}, {'id': 'a'}, {'id': 'b'}])); "
              "print(m.KEY, 'capped at', m.MAX)"],
         ]},
        {"type": "chrome", "duration": 8,
         "url_path": "/modules/{seed_module_id}",
         "caption": "Open a module -- the visit logs itself to localStorage.",
         "assert_js": "() => { const v = localStorage.getItem('gw-recent'); "
                      "return !!v && v.includes('{seed_module_id}'); }",
         "assert_want": "True"},
        {"type": "chrome", "duration": 8,
         "url_path": "/due",
         "focus": "#recent",
         "caption": "Due opens with the strip -- your last module, one click back.",
         "assert_js": "() => { const a = document.querySelector('#recent-list li a'); "
                      "return !!a && a.href.includes('{seed_module_id}'); }",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 7",
         "title": "Pick up where you left.",
         "subtitle": "recent.py renders with textContent -- titles cannot inject markup."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Return one module id with at least one concept to visit."""
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
