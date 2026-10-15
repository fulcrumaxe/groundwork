"""Feature demo: pre-interview recap track (F-134).

Full behavior: a capped weakest-first slice over known concepts --
lowest mastery first, stalest due breaks ties -- with study links
beside the Due queue. seed_db pins every concept's mastery high
except one, so the track leads with a known shakiest idea.
"""
from __future__ import annotations

import sqlite3

SCENARIO = {
    "id": "interviewprep",
    "kind": "feature",
    "batch": 25,
    "item": "F-134",
    "title": "Interview recap track",
    "blurb": "Your shakiest ideas first, capped, with study links.",
    "beats": [
        {"type": "title", "duration": 4,
         "kicker": "Batch 25 - Feature F-134",
         "title": "Interview recap track",
         "subtitle": "Weakest first -- recap before the interview."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b25-interviewprep",
         "caption": "Status names the order: weakest mastery, stalest due.",
         "assert_js": "() => !!document.querySelector('#status-b25-interviewprep') "
                      "&& document.body.innerText.includes('Weakest mastery first')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "Unknown mastery counts as 0 -- the unknown surfaces.",
         "commands": [
             ["python3", "-c",
              "from groundwork import interviewprep as m; "
              "cs = [{'id': 'a', 'name': 'A', 'mastery': 0.9}, {'id': 'b', 'name': 'B'}]; "
              "t = m.pick_track(cs, [{'concept_id': 'a', 'due': '2026-01-01'}], size=2); "
              "print([p['name'] for p in t]); "
              "print(t[0]['reason'])"],
         ]},
        {"type": "chrome", "duration": 10,
         "url_path": "/due",
         "focus": "#preptrack",
         "caption": "Due leads the recap with the known shakiest idea.",
         "assert_js": "() => { const s = document.querySelector('#preptrack'); "
                      "return s ? s.innerText : 'missing'; }",
         "assert_want": "{seed_name}"},
        {"type": "title", "duration": 4,
         "kicker": "Groundwork - Batch 25",
         "title": "Study the shakiest.",
         "subtitle": "interviewprep.py slices weakest-first -- empty, silent."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Pin mastery: all high but one known-shakiest concept."""
    con = sqlite3.connect(db_path)
    try:
        row = con.execute(
            "SELECT id, name FROM concepts ORDER BY rowid LIMIT 1").fetchone()
        if not row:
            return {"seeded": False, "reason": "no concepts"}
        con.execute("UPDATE concepts SET mastery=0.9")
        con.execute("UPDATE concepts SET mastery=0.01 WHERE id=?", (row[0],))
        con.commit()
        return {"seeded": True, "name": row[1]}
    finally:
        con.close()
