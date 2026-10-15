"""Feature demo: rabbit-hole free-explore mode (F-136).

Full behavior: the visited-concept chain rides in ?trail=a>b (no
tables); the module page renders a breadcrumb with a depth marker
plus an exit, and bonus wander-further links. seed_db builds a
two-concept trail from the first module's real concept names.
"""
from __future__ import annotations

import sqlite3
from urllib.parse import quote

SCENARIO = {
    "id": "rabbithole",
    "kind": "feature",
    "batch": 25,
    "item": "F-136",
    "title": "Rabbit-hole mode",
    "blurb": "Follow caller links freely -- bonus, never duty.",
    "beats": [
        {"type": "title", "duration": 4,
         "kicker": "Batch 25 - Feature F-136",
         "title": "Rabbit-hole mode",
         "subtitle": "Two concepts deep -- the breadcrumb shows the way out."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b25-rabbithole",
         "caption": "Status renders a live two-deep sample trail.",
         "assert_js": "() => !!document.querySelector('#status-b25-rabbithole') "
                      "&& !!document.querySelector('#rabbithole')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "Chains parse, cap at 8, and round-trip through quotes.",
         "commands": [
             ["python3", "-c",
              "from groundwork import rabbithole as m; "
              "print(m.parse_trail('add>total')); "
              "print(m.trail_qs(['a', 'b c'])); "
              "print('empty:', repr(m.trail_html('', 'm1')))"],
         ]},
        {"type": "chrome", "duration": 10,
         "url_path": "/modules/{seed_module}?trail={seed_trail}",
         "focus": "#rabbithole",
         "caption": "The module page in trail mode: depth 2, exit beside it.",
         "assert_js": "() => !!document.querySelector('#rabbithole') "
                      "&& document.body.innerText.includes('Rabbit hole (depth 2)')",
         "assert_want": "True"},
        {"type": "title", "duration": 4,
         "kicker": "Groundwork - Batch 25",
         "title": "Wander, then climb out.",
         "subtitle": "rabbithole.py rides the URL -- no grading impact."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Build a two-concept trail from the first module's concepts."""
    con = sqlite3.connect(db_path)
    try:
        mod = con.execute(
            "SELECT id FROM modules ORDER BY rowid LIMIT 1").fetchone()
        if not mod:
            return {"seeded": False, "reason": "no modules"}
        rows = con.execute(
            "SELECT name FROM concepts WHERE module_id=?"
            " ORDER BY rowid LIMIT 2", (mod[0],)).fetchall()
        if len(rows) < 2:
            return {"seeded": False, "reason": "module needs 2 concepts"}
        trail = f"{rows[0][0]}>{rows[1][0]}"
        return {"seeded": True, "module": mod[0],
                "trail": quote(trail, safe=">")}
    finally:
        con.close()
