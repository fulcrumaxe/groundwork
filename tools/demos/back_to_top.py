"""Improvement demo: back-to-top link (Batch 2, I-5).

Full functionality: long module pages end with a floating Back to
top link targeting the page header. seed_db picks the module with
the most concepts (the longest page); the beats film the footer
link, measure the page length, and click the link home.
"""
from __future__ import annotations

import sqlite3

SCENARIO = {
    "id": "back-to-top",
    "kind": "improvement",
    "batch": 2,
    "item": "I-5",
    "title": "Back-to-top link",
    "blurb": "Long module pages grow a floating Back to top link.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 2 - Improvement I-5",
         "title": "Back-to-top link",
         "subtitle": "Long module pages grow a floating Back to top link."},
        {"type": "chrome", "duration": 8,
         "url_path": "/modules/{seed_mid}",
         "focus": "a.totop",
         "caption": "Long module pages end with a floating Back to top link.",
         "assert_js": "() => { const a = document.querySelector('a.totop'); "
                      "return a ? a.textContent + '|' + a.getAttribute('href') : 'missing'; }",
         "assert_want": "Back to top|#top"},
        {"type": "terminal", "duration": 7,
         "caption": "A long page earns the link: {seed_concepts} concepts, {seed_cards} cards.",
         "commands": [
             ["python3", "-c",
              "import os, sqlite3; from groundwork import emoji as e; "
              "con = sqlite3.connect(os.environ.get('DEMO_DB', 'groundwork.db')); "
              "print('concepts:', con.execute(\"SELECT COUNT(*) FROM concepts WHERE module_id='{seed_mid}'\").fetchone()[0]); "
              "print('cards:', con.execute(\"SELECT COUNT(*) FROM cards JOIN concepts ON concepts.id = cards.concept_id WHERE concepts.module_id='{seed_mid}'\").fetchone()[0]); "
              "print('footer link:', e.totop_html())"],
         ]},
        {"type": "chrome", "duration": 10,
         "url_path": "/modules/{seed_mid}",
         "caption": "One click returns to the page header.",
         "js": ["() => { const a = document.querySelector('a.totop'); "
                "if (!a) return 'totop-missing'; a.click(); return 'clicked'; }"],
         "poll_js": "() => location.hash",
         "poll_want": "#top",
         "poll_required": True,
         "poll_timeout": 25,
         "assert_js": "() => location.hash",
         "assert_want": "#top"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 2",
         "title": "Long pages, short trips.",
         "subtitle": "totop_html() anchors every module page to its header."},
    ],
}


def seed_db(db_path: str) -> dict:
    """The module with the most concepts -- the longest page wins the link."""
    con = sqlite3.connect(db_path)
    try:
        m = con.execute(
            "SELECT module_id, COUNT(*) FROM concepts GROUP BY module_id"
            " ORDER BY COUNT(*) DESC LIMIT 1").fetchone()
        if not m:
            return {"seeded": False, "reason": "no concepts"}
        mid = m[0]
        n_cards = con.execute(
            "SELECT COUNT(*) FROM cards JOIN concepts"
            " ON concepts.id = cards.concept_id"
            " WHERE concepts.module_id=?", (mid,)).fetchone()[0]
        return {"seeded": True, "mid": mid,
                "concepts": m[1], "cards": n_cards}
    finally:
        con.close()
