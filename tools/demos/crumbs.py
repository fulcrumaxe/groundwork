"""Improvement demo: page breadcrumbs (I-3).

Full behavior: every nested page opens with its trail -- ledger page
(Due, Modules, History) first, then module, lesson, card -- with the
current page marked aria-current. Beats show the Status home, the
pure trail() helper, and the live trail on two module pages.
"""
from __future__ import annotations

import sqlite3

SCENARIO = {
    "id": "crumbs",
    "kind": "improvement",
    "batch": 6,
    "item": "I-3",
    "title": "Page breadcrumbs",
    "blurb": "Every nested page opens with its trail -- ledger first, then module.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 6 - Improvement I-3",
         "title": "Page breadcrumbs",
         "subtitle": "Where in the site am I? Answered at the top of every nested page."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b6-crumbs",
         "caption": "Status documents the trail with a live sample beside the copy.",
         "assert_js": "() => !!document.querySelector('#status-b6-crumbs')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "The rule in one line: unsafe hrefs render as text, never links.",
         "commands": [
             ["python3", "-c",
              "from groundwork import crumbs as m; "
              "print(m.trail([('Modules', '/modules'), ('Example module', None)])); "
              "print(repr(m.trail([('X', 'https://evil.example'), ('Here', None)])))"],
         ]},
        {"type": "chrome", "duration": 8,
         "url_path": "/modules/{seed_mid}",
         "focus": "#crumbs",
         "caption": "A module page opens with its trail -- Modules first, then this module.",
         "assert_js": "() => { const n = document.querySelector('nav#crumbs'); "
                      "return !!n && n.textContent.includes('Modules'); }",
         "assert_want": "True"},
        {"type": "chrome", "duration": 8,
         "url_path": "/modules/{seed_mid2}",
         "focus": "#crumbs",
         "caption": "Every module page carries one -- the current page marked, not linked.",
         "assert_js": "() => { const n = document.querySelector('nav#crumbs'); "
                      "return !!n && !!n.querySelector(\"[aria-current='page']\"); }",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 6",
         "title": "Never lost in the site.",
         "subtitle": "crumbs.py is pure HTML -- repo-tree position stays with filemap."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Pick the module with the most concepts for the trail beats."""
    con = sqlite3.connect(db_path)
    try:
        rows = con.execute(
            "SELECT module_id FROM concepts GROUP BY module_id"
            " ORDER BY COUNT(*) DESC LIMIT 2").fetchall()
        if len(rows) < 2:
            rows = con.execute("SELECT id FROM modules LIMIT 2").fetchall()
        if len(rows) < 2:
            return {"seeded": False, "reason": "no modules"}
        return {"seeded": True, "mid": rows[0][0], "mid2": rows[1][0]}
    finally:
        con.close()
