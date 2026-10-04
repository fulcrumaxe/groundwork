"""Improvement demo: primary-left button order + audit (I-35).

Full behavior: buttons.group() builds primary-first rows and
buttons.audit() flags reversed source order; the live reset
confirm (GET only, no state change) and journal form already
comply. seed_db touches no tables (module id for the reset
beat); Status shows the pattern, terminal runs group+audit,
two live forms prove compliance in source order.
"""
from __future__ import annotations

import sqlite3

SCENARIO = {
    "id": "buttons",
    "kind": "improvement",
    "batch": 8,
    "item": "I-35",
    "title": "Primary button first",
    "blurb": ("Every form leads with its primary action -- tab order "
              "matches visual order."),
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 8 - Improvement I-35",
         "title": "Primary button first",
         "subtitle": ("The primary action leads in source order -- tab "
                      "order matches what you see.")},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b8-buttons",
         "caption": "Status shows the pattern live: Save first, Cancel after.",
         "assert_js": "() => { const f = document.querySelector("
                      "'main form[action=\"/journal\"]'); return !!f && "
                      "f.innerHTML.indexOf('<button') < f.innerHTML.indexOf('<a '); }",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": ("The rule in one line: group() leads primary, audit() "
                     "flags the reverse."),
         "commands": [
             ["python3", "-c",
              "from groundwork import buttons as m; "
              "print(m.group('<button>Save</button>', [\"<a href='/x'>Cancel</a>\"])); "
              "print(m.audit(\"<form><a href='/x'>C</a><button>S</button></form>\")); "
              "print(m.audit(\"<form><button>S</button><a href='/x'>C</a></form>\"))"],
         ]},
        {"type": "chrome", "duration": 8,
         "url_path": "/modules/{seed_mid}/reset",
         "focus": "#reset-confirm",
         "caption": ("The real reset confirm: Yes-first, Keep-it second -- "
                     "in the source, not just the CSS."),
         "assert_js": "() => { const f = document.querySelector("
                      "\"form[action='/modules/{seed_mid}/reset']\"); return !!f && "
                      "f.innerHTML.indexOf('<button') < f.innerHTML.indexOf('<a'); }",
         "assert_want": "True"},
        {"type": "chrome", "duration": 9,
         "url_path": "/journal",
         "focus": "#journal",
         "caption": ("Single-action forms comply trivially -- the Save "
                     "button stands alone."),
         "assert_js": "() => { const f = document.querySelector("
                      "\"#journal form[action='/journal']\"); return !!f && "
                      "!!f.querySelector('button') && !f.querySelector('a'); }",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 8",
         "title": "Tab meets primary first.",
         "subtitle": ("buttons.py builds the row and audits the order -- "
                      "keyboard and readers agree.")},
    ],
}


def seed_db(db_path: str) -> dict:
    """Db-free module: return a live module id, write nothing."""
    con = sqlite3.connect(db_path)
    try:
        row = con.execute("SELECT id FROM modules LIMIT 1").fetchone()
    finally:
        con.close()
    if not row:
        return {"seeded": False, "reason": "no modules"}
    return {"seeded": True, "mid": row[0]}
