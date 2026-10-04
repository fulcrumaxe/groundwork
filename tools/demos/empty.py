"""Improvement demo: empty states with next action (I-12).

Full functionality: no page runs dry without offering a next step --
empty.py owns the contract and every dry surface keeps it. seed_db pushes
every card's due date to 2099 (and drops stability so no probe cards
leak in), so /due renders its empty state; the beats film the calm
all-caught-up hero plus the dry-project library page.
"""
from __future__ import annotations

import sqlite3

SCENARIO = {
    "id": "empty",
    "kind": "improvement",
    "batch": 5,
    "item": "I-12",
    "title": "Empty states with next action",
    "blurb": "No dead ends: every dry page offers a next step.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 5 - Improvement I-12",
         "title": "Empty states with next action",
         "subtitle": "No dead ends: every dry page offers a next step."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b5-empty",
         "caption": "Status documents the improvement with its live anchor.",
         "assert_js": "() => !!document.querySelector('#status-b5-empty')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "The contract in one helper: message plus a next-action link, per page.",
         "commands": [
             ["python3", "-c",
              "from groundwork import empty as m; "
              "print(m.empty_state('due')); "
              "print(m.empty_state('history'))"],
         ]},
        {"type": "chrome", "duration": 12,
         "url_path": "/due",
         "focus": "#done-hero",
         "caption": "A dry Due queue celebrates and offers next actions -- never a dead end.",
         "assert_js": "() => { const h = document.querySelector('#done-hero'); "
                      "return !!h && h.innerText.includes('Study the library'); }",
         "assert_want": "True"},
        {"type": "chrome", "duration": 6,
         "url_path": "/modules?repo=zzz-no-such-project",
         "focus": "svg.empty-art",
         "caption": "A project with no modules says so plainly, with art -- no dead end.",
         "assert_js": "() => document.body.innerText.includes("
                      "'No modules for this project yet.')",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 5",
         "title": "No dead ends.",
         "subtitle": "empty.py owns the contract -- dry pages always offer a next step."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Empty the Due queue: all dues to 2099, stability below probe line.

    The queue query is due <= now AND stale = 0; probes need stability
    >= 7.0, so dropping stability to 1.0 keeps them out too. Fixture
    copy only; the served library DB is never touched.
    """
    con = sqlite3.connect(db_path)
    try:
        cur = con.execute(
            "UPDATE cards SET due='2099-01-01T00:00:00Z', stability=1.0")
        con.commit()
        left = con.execute(
            "SELECT COUNT(*) FROM cards WHERE due <= '2099-00-00' "
            "AND stale = 0").fetchone()
        return {"seeded": True, "pushed": cur.rowcount,
                "still_due": left[0] if left else -1}
    finally:
        con.close()
