"""Feature demo: the dial filters Due (F-55 integration).

Full behavior: /due?dial=N filters the live queue by the level floor
and caps new cards -- gentle keeps one new card and drops the
ten-days-forgotten review, while an absent dial returns the legacy
queue untouched and the control always shows the active level.
"""
from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone

MODULE_ID = "demo-b17-dial"
FORGOTTEN_FRONT = "Dial fixture: ten days overdue at stability 2."
FRESH_FRONT = "Dial fixture fresh card %d."
BACK = "Answer to prove the dial let this card through."

SCENARIO = {
    "id": "dialqueue",
    "kind": "feature",
    "batch": 17,
    "item": "F-55",
    "title": "The dial filters Due",
    "blurb": "Gentle keeps one new card and drops the forgotten; absent dial returns the legacy queue untouched.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 17 - Feature F-55",
         "title": "The dial filters Due",
         "subtitle": "Gentle keeps one new card and drops the forgotten; absent dial returns the legacy queue untouched."},
        {"type": "terminal", "duration": 8,
         "caption": "The rule in one call: floors drop forgotten reviews, caps trim new cards, absent dial keeps legacy.",
         "commands": [
             ["python3", "-c",
              "from datetime import datetime, timedelta, timezone; "
              "from groundwork import minisession as m, sched as s; "
              "now = datetime.now(timezone.utc); "
              "iso = lambda d: (now - timedelta(days=d)).strftime("
              "'%Y-%m-%dT%H:%M:%SZ'); "
              "due = [{'id': 'r', 'stability': 2.0, 'due': iso(10)}] + "
              "[{'id': 'c%d' % i, 'stability': 1.0, 'due': iso(0)} "
              "for i in range(5)]; "
              "tries = {'r': 4}; "
              "print('forgotten R:', "
              "round(s.elapsed_retrievability(2.0, iso(10)), 2)); "
              "print('L1 keeps:', "
              "[c['id'] for c in m.apply_dial(due, '1', tries)]); "
              "print('L5 keeps:', "
              "len(m.apply_dial(due, '5', tries)), 'cards'); "
              "print('absent dial keeps legacy:', "
              "m.apply_dial(due, None, {}) is due); "
              "print('reviewed ignore cap:', len(m.apply_dial("
              "[{'id': 'v%d' % i, 'stability': 1.0, 'due': iso(0)} "
              "for i in range(4)], '1', "
              "{'v0': 2, 'v1': 3, 'v2': 1, 'v3': 5})) == 4)"],
         ]},
        {"type": "chrome", "duration": 10,
         "url_path": "/due?dial=1",
         "caption": "Gentle dialed: one new card survives, the forgotten review is gone.",
         "assert_js": "() => document.body.innerText.includes('Card 1 of 1')"
                      " && document.body.innerText.includes('(dialed)')"
                      " && document.body.innerText.includes('Gentle')",
         "assert_want": "True"},
        {"type": "chrome", "duration": 7,
         "url_path": "/due",
         "caption": "No dial, no filter: the full queue of four, control parked at balanced.",
         "assert_js": "() => document.body.innerText.includes('Card 1 of 4')"
                      " && document.body.innerText.includes('Difficulty dial')",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 17",
         "title": "Dial your struggle.",
         "subtitle": "apply_dial floors R and caps new cards -- order preserved."},
    ],
}


def seed_db(db_path: str) -> dict:
    """One forgotten card plus three fresh cards; everything else parked.

    No reviews on the planted cards, so the personal-decay fit finds
    no history (k=1.0) and the legacy sched curve rules the floors.
    Probes are suppressed globally (last_probe=now covers every
    review cycle) so the queue holds exactly the four planted cards.
    """
    con = sqlite3.connect(db_path)
    try:
        now = datetime.now(timezone.utc)
        fresh_due = now.strftime("%Y-%m-%dT%H:%M:%SZ")
        old_due = (now - timedelta(days=10)).strftime("%Y-%m-%dT%H:%M:%SZ")
        con.execute("UPDATE cards SET due='2030-01-01T00:00:00Z',"
                    " last_probe=?", (fresh_due,))
        cids = [f"{MODULE_ID}:c{i}" for i in range(4)]
        for cid in cids:
            con.execute("DELETE FROM reviews WHERE card_id LIKE ?",
                        (f"{MODULE_ID}-%",))
            con.execute("DELETE FROM cards WHERE concept_id=?", (cid,))
            con.execute("DELETE FROM concepts WHERE id=?", (cid,))
        con.execute("DELETE FROM modules WHERE id=?", (MODULE_ID,))
        con.execute(
            "INSERT INTO modules(id, repo, task_summary, created_at)"
            " VALUES(?, ?, ?, ?)",
            (MODULE_ID, "demo/b17-dial", "Difficulty dial module",
             fresh_due))
        specs = [("forgotten", 2.0, old_due, FORGOTTEN_FRONT)]
        specs += [(f"fresh{i}", 1.0, fresh_due, FRESH_FRONT % i)
                  for i in range(3)]
        for (name, stability, due, front), cid in zip(specs, cids):
            con.execute(
                "INSERT INTO concepts(id, module_id, name, kind, file,"
                " line, mastery) VALUES(?, ?, ?, ?, ?, ?, ?)",
                (cid, MODULE_ID, name, "function", "demo/dial.py", 1,
                 0.0))
            con.execute(
                "INSERT INTO cards(id, concept_id, exercise_type, front,"
                " back, stability, due) VALUES(?, ?, '1', ?, ?, ?, ?)",
                (f"{MODULE_ID}-{name}", cid, front, BACK, stability,
                 due))
        con.commit()
        return {"seeded": True, "module_id": MODULE_ID,
                "forgotten": f"{MODULE_ID}-forgotten"}
    finally:
        con.close()
