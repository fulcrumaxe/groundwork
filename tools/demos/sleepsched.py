"""Feature demo: sleep-aware dues (F-93).

Full behavior: new cards due in quiet hours (22:00-07:00 UTC) display at
next-morning 07:00 in the due queue instead of seeding 3am reviews; reviewed
cards keep their stored due and queue order never moves. seed_db parks one
new and one reviewed card at night dues; the MCP beat shows the split.
"""
from __future__ import annotations

import sqlite3

NIGHT_NEW = "2000-01-01T02:30:00Z"
NIGHT_SEEN = "2000-01-01T03:15:00Z"

SCENARIO = {
    "id": "sleepsched",
    "kind": "feature",
    "batch": 21,
    "item": "F-93",
    "title": "Sleep-aware dues",
    "blurb": "New cards reviewed late at night wake up with a morning due, not a 3am one.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 21 - Feature F-93",
         "title": "Sleep-aware dues",
         "subtitle": "Late-night study should never seed a 3am review."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b21-sleepsched",
         "caption": "Status documents the quiet-hours window and the morning rule.",
         "assert_js": "() => !!document.querySelector('#status-b21-sleepsched')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 8,
         "caption": "The rule in one line: night dues move to 07:00, day dues stand.",
         "commands": [
             ["python3", "-c",
              "from groundwork import sleepsched as m; "
              "print('night:', m.adjust_due('2000-01-01T02:30:00Z')); "
              "print('day:', m.adjust_due('2000-01-01T14:00:00Z')); "
              "print('quiet at 23h:', m.in_quiet_hours(hour=23), "
              "'| quiet at 9h:', m.in_quiet_hours(hour=9))"],
         ]},
        {"type": "terminal", "duration": 11,
         "caption": "The live queue: the new night card defers, the reviewed one stands.",
         "commands": [
             ["python3", "-c",
              "import os; from groundwork import mcp as mcpmod; "
              "db = os.environ.get('DEMO_DB', 'groundwork.db'); "
              "out = mcpmod.MCPServer(db).tool_list_due_reviews({'limit': 2000}); "
              "by_id = {c['id']: c['due'] for c in out['due']}; "
              "print('new card due:', by_id.get('{seed_new_id}')); "
              "print('reviewed due:', by_id.get('{seed_seen_id}'))"],
         ]},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 21",
         "title": "Sleep first, review at seven.",
         "subtitle": "sleepsched.py defers new night dues -- order untouched."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Park one new and one reviewed card at night dues."""
    con = sqlite3.connect(db_path)
    try:
        new = con.execute(
            "SELECT id FROM cards WHERE id NOT IN"
            " (SELECT card_id FROM reviews) LIMIT 1").fetchone()
        other = con.execute(
            "SELECT id FROM cards WHERE id NOT IN"
            " (SELECT card_id FROM reviews) LIMIT 1 OFFSET 1").fetchone()
        if not new or not other:
            return {"seeded": False, "reason": "too few new cards"}
        new_id, seen_id = new[0], other[0]
        con.execute("UPDATE cards SET due=? WHERE id=?", (NIGHT_NEW, new_id))
        con.execute("UPDATE cards SET due=? WHERE id=?", (NIGHT_SEEN, seen_id))
        con.execute(
            "INSERT INTO reviews(card_id, grade, confidence, submission)"
            " VALUES(?, 4, 3, 'sleepsched seed')", (seen_id,))
        con.commit()
        return {"seeded": True, "new_id": new_id, "seen_id": seen_id}
    finally:
        con.close()
