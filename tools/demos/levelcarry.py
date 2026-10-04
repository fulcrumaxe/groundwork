"""Improvement demo: explainer level carry-over (I-4).

Full behavior: pick Plain words once and every link keeps it -- the
active level rides the URL as ?level=1..4, bookmarkable, no cookies.
Beats show the Status home, the pure carry() rule, the carried links
on a real ?level=2 page, and the carry_html rewrite pass.
"""
from __future__ import annotations

import sqlite3

SCENARIO = {
    "id": "levelcarry",
    "kind": "improvement",
    "batch": 6,
    "item": "I-4",
    "title": "Explainer level carry-over",
    "blurb": "Pick Plain words once and every link keeps it.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 6 - Improvement I-4",
         "title": "Explainer level carry-over",
         "subtitle": "Your reading level rides the URL -- every link keeps it."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b6-levelcarry",
         "caption": "Status names the contract: ?level=1..4, per-browser, no cookies.",
         "assert_js": "() => !!document.querySelector('#status-b6-levelcarry')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 8,
         "caption": "The rule in one line: explicit levels attach, auto never doubles.",
         "commands": [
             ["python3", "-c",
              "from groundwork import levelcarry as m; "
              "print(m.carry('/modules/abc', '2')); "
              "print(m.carry('/modules/abc?level=2', '3')); "
              "print(m.carry('/modules/abc', 'auto')); "
              "print(m.carry('https://x.example/y', '2'))"],
         ]},
        {"type": "chrome", "duration": 8,
         "url_path": "/modules/{seed_mid}?level=2",
         "caption": "A ?level=2 page: internal links carry the level forward.",
         "assert_js": "() => document.body.innerHTML.split('level=2').length > 5",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "Whole pages rewrite the same way -- externals and fragments survive.",
         "commands": [
             ["python3", "-c",
              "from groundwork import levelcarry as m; "
              "print(m.carry_html('<a href=\"/due\">Q</a> <a href=\"https://x.example\">X</a>', '1'))"],
         ]},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 6",
         "title": "Set it once, read everywhere.",
         "subtitle": "levelcarry.py rewrites hrefs -- tabs still come from lessons."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Pick the module with the most concepts for the carry beats."""
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
