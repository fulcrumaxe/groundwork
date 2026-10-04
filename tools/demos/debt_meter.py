"""Feature demo: comprehension debt meter (Batch 1).

Full functionality: /debt renders the overall debt meter (what changed
vs what the learner can prove they own) plus a per-repo, per-file table
of owned counts and debt percent. The fixture ships fully unowned, so
no mutation is needed -- the meter honestly reads 100%.
"""
from __future__ import annotations

import sqlite3

SCENARIO = {
    "id": "debt-meter",
    "kind": "feature",
    "batch": 1,
    "item": "F-251",
    "title": "Comprehension debt meter",
    "blurb": "What changed versus what you can prove you own, per repo and file.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 1 - Feature debt-meter",
         "title": "Comprehension debt meter",
         "subtitle": "What changed versus what you can prove you own, per repo and file."},
        {"type": "chrome", "duration": 8,
         "url_path": "/debt#debt-meter",
         "focus": "#debt-meter",
         "caption": "The meter reads live data: zero owned, so debt is 100 percent.",
         "assert_js": "() => document.querySelector('#debt-meter').getAttribute('aria-label')",
         "assert_want": "comprehension debt"},
        {"type": "terminal", "duration": 7,
         "caption": "The meter is a pure renderer over the DB path -- same HTML the page serves.",
         "commands": [
             ["python3", "-c",
              "import os, re; from groundwork import debt as m; "
              "h = m.debt_html(os.environ.get('DEMO_DB', 'groundwork.db')); "
              "t = re.sub(r'<[^>]+>', '', h); "
              "print(re.search(r'[0-9]+% comprehension debt \\([0-9/]+ concepts owned\\)', t).group(0))"],
         ]},
        {"type": "chrome", "duration": 8,
         "url_path": "/debt",
         "focus": "main h2",
         "caption": "Below the meter: each repo's files with owned counts and debt percent.",
         "assert_js": "() => !!document.querySelector('table.log')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 6,
         "caption": "The denominator: every concept in every module counts toward debt.",
         "commands": [
             ["python3", "-c",
              "import os, sqlite3; con = sqlite3.connect(os.environ.get('DEMO_DB', 'groundwork.db')); "
              "n, m = con.execute('SELECT COUNT(*), COUNT(DISTINCT module_id) FROM concepts').fetchone(); "
              "print(f'{n} concepts across {m} modules')"],
         ]},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 1",
         "title": "Pay it down, file by file.",
         "subtitle": "debt.py renders the meter -- ownership proofs move it."},
    ],
}


def seed_db(db_path: str) -> dict:
    """No mutation needed: the fixture ships fully unowned, so the meter
    reads 100% and every file row agrees. Only verifies modules exist."""
    con = sqlite3.connect(db_path)
    try:
        try:
            n = con.execute("SELECT COUNT(*) FROM modules").fetchone()
        except Exception:
            return {"seeded": False, "reason": "no modules table"}
        if not n or not n[0]:
            return {"seeded": False, "reason": "no modules"}
        return {"seeded": True}
    finally:
        con.close()
