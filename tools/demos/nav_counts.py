"""Demo: nav badge counts (Batch 1 improvement).

Full functionality: the header nav carries live counts -- Due,
Modules and History -- rendered from the single sitenav item table
on every page. seed_db only reads the fixture counts for caption
tokens (badges render even at zero, so no forcing is needed); the
beats film the nav on two pages and show the pure renderer plus
the DB queries behind the badges.
"""
from __future__ import annotations

import datetime
import sqlite3

SCENARIO = {
    "id": "nav-counts",
    "kind": "improvement",
    "batch": 1,
    "item": "I-11",
    "title": "Nav badge counts",
    "blurb": "Due, Modules and History counts live in the nav \u2014 no guessing.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 1 - Improvement nav-counts",
         "title": "Nav badge counts",
         "subtitle": "Due, Modules and History counts in the header -- no guessing."},
        {"type": "chrome", "duration": 8,
         "url_path": "/",
         "caption": "The header nav carries live counts: Due ({seed_due}), Modules ({seed_modules}), History ({seed_history}).",
         "assert_js": "() => { const n = document.querySelector('#sitenav'); return n && n.textContent.includes('Due (') && n.textContent.includes('Modules (') && n.textContent.includes('History ('); }",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "Badges are pure: header_nav adds (n) only when counts exist.",
         "commands": [
             ["python3", "-c",
              "from groundwork import sitenav as m; "
              "print([a for a in m.header_nav('due', {'due': 3}).split(' \u00b7 ') if 'Due' in a][0]); "
              "print([a for a in m.header_nav('due').split(' \u00b7 ') if 'Due' in a][0])"],
         ]},
        {"type": "chrome", "duration": 7,
         "url_path": "/due",
         "caption": "Same badges on every page -- one nav table renders the header.",
         "assert_js": "() => { const n = document.querySelector('#sitenav'); return n && n.textContent.includes('Due ('); }",
         "assert_want": "True"},
        {"type": "terminal", "duration": 8,
         "caption": "Counts come from the live DB: due cards, modules, reviews.",
         "commands": [
             ["python3", "-c",
              "import os, sqlite3, datetime; con = sqlite3.connect(os.environ.get('DEMO_DB', 'groundwork.db')); "
              "now = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'); "
              "print('due:', con.execute('SELECT COUNT(*) FROM cards WHERE due <= ? AND stale = 0', (now,)).fetchone()[0]); "
              "print('modules:', con.execute('SELECT COUNT(*) FROM modules').fetchone()[0]); "
              "print('history:', con.execute('SELECT COUNT(*) FROM reviews').fetchone()[0])"],
         ]},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 1",
         "title": "No guessing.",
         "subtitle": "sitenav.py owns the table; web.py feeds it live counts."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Read live nav counts for caption tokens (no forcing needed).

    The header renders badges even at zero, so an empty fixture still
    films; COUNT(*) never fails on empty tables and each query falls
    back to 0. Mirrors Handler._nav_counts (groundwork/web.py).
    """
    con = sqlite3.connect(db_path)
    try:
        now = datetime.datetime.now(datetime.timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ")
        try:
            due = con.execute(
                "SELECT COUNT(*) FROM cards WHERE due <= ? AND stale = 0",
                (now,)).fetchone()[0]
        except sqlite3.Error:
            due = 0
        try:
            mods = con.execute("SELECT COUNT(*) FROM modules").fetchone()[0]
        except sqlite3.Error:
            mods = 0
        try:
            tries = con.execute("SELECT COUNT(*) FROM reviews").fetchone()[0]
        except sqlite3.Error:
            tries = 0
        return {"seeded": True, "due": due, "modules": mods,
                "history": tries}
    finally:
        con.close()
