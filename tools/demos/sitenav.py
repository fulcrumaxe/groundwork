"""Improvement demo: merged site nav table (I-39).

Full behavior: one sitenav.NAV table feeds the header on every
page -- active marked with aria-current, live (n) badges. seed_db
pins the due queue to exactly two cards and reads the live module
count; Status demos the table, terminal prints the renderers, the
live #sitenav header on /due and /modules proves mark + badges.
"""
from __future__ import annotations

import sqlite3

SCENARIO = {
    "id": "sitenav",
    "kind": "improvement",
    "batch": 8,
    "item": "I-39",
    "title": "Merged site nav",
    "blurb": ("Header and footer render from one nav table -- one active "
              "state, no drift."),
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 8 - Improvement I-39",
         "title": "Merged site nav",
         "subtitle": ("One NAV table feeds the header -- active marked, "
                      "counts badged.")},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b8-sitenav",
         "caption": ("Status demos the table: six items, active marked, "
                     "badges in the header."),
         "assert_js": "() => !!document.querySelector('#status-b8-sitenav') && "
                      "!!document.querySelector('#sitenav-demo')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": ("The rule in one line: one table, active marked, "
                     "badges optional."),
         "commands": [
             ["python3", "-c",
              "from groundwork import sitenav as m; "
              "print(len(m.items()), m.href_of('history'), repr(m.href_of('nope'))); "
              "print(m.header_nav('due', {'due': 3})); "
              "print(m.footer_nav('due')[:80])"],
         ]},
        {"type": "chrome", "duration": 8,
         "url_path": "/due",
         "caption": ("The live header on Due: Due carries aria-current, "
                     "badges count real rows."),
         "assert_js": "() => { const n = document.querySelector('#sitenav'); "
                      "return !!n && !!n.querySelector(\"a[href='/due'][aria-current]\") && "
                      "n.textContent.includes('Due ({seed_due_count})') && "
                      "n.textContent.includes('Modules ({seed_modules_count})'); }",
         "assert_want": "True"},
        {"type": "chrome", "duration": 8,
         "url_path": "/modules",
         "caption": "Same table on Modules: the mark moves, the badges persist.",
         "assert_js": "() => { const n = document.querySelector('#sitenav'); "
                      "return !!n && !!n.querySelector(\"a[href='/modules'][aria-current]\") && "
                      "!n.querySelector(\"a[href='/due'][aria-current]\"); }",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 8",
         "title": "One table, every page.",
         "subtitle": "sitenav.py owns NAV -- web.py renders it, badges included."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Pin the due queue to a known pair; read the live module count."""
    con = sqlite3.connect(db_path)
    try:
        rows = con.execute(
            "SELECT id FROM cards ORDER BY due LIMIT 2").fetchall()
        if not rows:
            return {"seeded": False, "reason": "no cards"}
        con.execute("UPDATE cards SET due='2030-01-01T00:00:00Z'")
        ids = [r[0] for r in rows]
        con.execute(
            "UPDATE cards SET due='2000-01-01T00:00:00Z' WHERE id IN (%s)"
            % ",".join("?" * len(ids)), ids)
        modules_n = con.execute("SELECT COUNT(*) FROM modules").fetchone()[0]
        con.commit()
        return {"seeded": True, "due_count": len(ids),
                "modules_count": modules_n}
    finally:
        con.close()
