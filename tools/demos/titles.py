"""Improvement demo: unique page titles (I-1).

Full functionality: every page carries a distinct <title> so browser
tabs and history entries stay distinct, and titles.page_title() composes
the page-plus-context form. seed_db changes no rows (titles are static
per route); the chrome beats read the live document.title on two pages
and inject a visible readout so the tab name shows in the frame.
"""
from __future__ import annotations

import sqlite3

SCENARIO = {
    "id": "titles",
    "kind": "improvement",
    "batch": 5,
    "item": "I-1",
    "title": "Unique page titles",
    "blurb": "Every page names its context; browser tabs stay distinct.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 5 - Improvement I-1",
         "title": "Unique page titles",
         "subtitle": "Every page names its context -- browser tabs stay distinct."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b5-titles",
         "caption": "Status documents the improvement with its live anchor.",
         "assert_js": "() => !!document.querySelector('#status-b5-titles')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "The rule in one line: page plus context, collapsed and suffixed.",
         "commands": [
             ["python3", "-c",
              "from groundwork import titles as m; "
              "print(repr(m.page_title('Due', '3 cards'))); "
              "print(repr(m.page_title('History'))); "
              "print(repr(m.page_title('', '')))"],
         ]},
        {"type": "chrome", "duration": 8,
         "url_path": "/due",
         "caption": "The Due queue tab names itself -- the readout shows the live document.title.",
         "js": ["() => { const p = document.createElement('p'); "
                "p.id = 'title-readout'; "
                "p.textContent = 'Tab title: ' + document.title; "
                "p.setAttribute('style', 'border:2px solid var(--accent-due);"
                "padding:8px 12px;font-weight:bold'); "
                "document.querySelector('main').prepend(p); "
                "return document.title; }"],
         "assert_js": "() => document.title",
         "assert_want": "Due"},
        {"type": "chrome", "duration": 8,
         "url_path": "/modules",
         "caption": "The library tab names itself too -- open tabs stay distinct.",
         "js": ["() => { const p = document.createElement('p'); "
                "p.id = 'title-readout'; "
                "p.textContent = 'Tab title: ' + document.title; "
                "p.setAttribute('style', 'border:2px solid var(--accent-modules);"
                "padding:8px 12px;font-weight:bold'); "
                "document.querySelector('main').prepend(p); "
                "return document.title; }"],
         "assert_js": "() => document.title",
         "assert_want": "Modules"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 5",
         "title": "Tabs stay distinct.",
         "subtitle": "titles.py composes page-plus-context -- every route names itself."},
    ],
}


def seed_db(db_path: str) -> dict:
    """No fixture rows change: titles are static per route.

    Touches the fixture copy read-only (counts modules to prove the
    served library is intact); the beats read live document.title
    values, which need no manipulated data.
    """
    con = sqlite3.connect(db_path)
    try:
        row = con.execute("SELECT COUNT(*) FROM modules").fetchone()
        return {"seeded": True, "modules": row[0] if row else 0}
    finally:
        con.close()
