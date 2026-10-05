"""Feature demo: cold-attempt sessions (F-56).

Full behavior: three unseen concepts surface on /due?mode=cold with
priming lines while everything already owned or due stays out -- the
fixture owns every other concept so the cold round is exactly ours.
"""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone

MODULE_ID = "demo-cold-56"
CONCEPTS = [
    ("demo/cold.py:brave", "Brave guess"),
    ("demo/cold.py:stuck", "Stuck point"),
    ("demo/cold.py:retry", "Retry path"),
]

SCENARIO = {
    "id": "coldattempt",
    "kind": "feature",
    "batch": 12,
    "item": "F-56",
    "title": "Cold-attempt sessions",
    "blurb": "Attempt unseen concepts cold -- struggle first, then learn.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 12 - Feature F-56",
         "title": "Cold-attempt sessions",
         "subtitle": "Struggle first, then learn."},
        {"type": "chrome", "duration": 7,
         "url_path": "/status",
         "focus": "#status-b12-coldattempt",
         "caption": "Status homes the picker: unseen, non-due, primed each.",
         "assert_js": "() => { const el = document.querySelector("
                      "\"#status-b12-coldattempt\"); return !!el && "
                      "document.body.innerText.includes('cold_session'); }",
         "assert_want": "True"},
        {"type": "terminal", "duration": 9,
         "caption": "The rule in one line: owned and due never enter, adjacent first.",
         "commands": [
             ["python3", "-c",
              "from groundwork import coldattempt as m; "
              "pool = [{'id': 'a', 'module_id': 'm1'}, "
              "{'id': 'b', 'module_id': 'm1'}, "
              "{'id': 'c', 'module_id': 'm2'}]; "
              "s = m.cold_session(pool, owned_ids={'a'}, due_ids=set()); "
              "print('picks:', [i['concept_id'] for i in s['items']]); "
              "print('prime:', s['items'][0]['prime']); "
              "print('note:', s['note'])"],
         ]},
        {"type": "chrome", "duration": 10,
         "url_path": "/due?mode=cold",
         "focus": "#cold",
         "caption": "The cold round: three unseen concepts, primed, study-linked.",
         "assert_js": "() => { const el = document.querySelector('#cold');"
                      " return !!el && el.innerText.includes('struggle first')"
                      " && el.innerText.includes('{seed_first}'); }",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 12",
         "title": "Attempt cold.",
         "subtitle": "coldattempt.py picks unseen -- adjacent first."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Plant three unseen concepts; own everything else.

    Owning all pre-existing concepts empties the cold pool of
    strangers, so the round holds exactly the three seeded picks.
    """
    con = sqlite3.connect(db_path)
    try:
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        cids = [f"{MODULE_ID}:{node}" for node, _n in CONCEPTS]
        for cid in cids:
            con.execute("DELETE FROM cards WHERE concept_id=?", (cid,))
            con.execute("DELETE FROM concepts WHERE id=?", (cid,))
        con.execute("DELETE FROM modules WHERE id=?", (MODULE_ID,))
        con.execute(
            "INSERT INTO modules(id, repo, task_summary, created_at)"
            " VALUES(?, ?, ?, ?)",
            (MODULE_ID, "demo/cold", "Cold attempt module", now))
        for (node, name), cid in zip(CONCEPTS, cids):
            con.execute(
                "INSERT INTO concepts(id, module_id, name, kind, file,"
                " line, mastery) VALUES(?, ?, ?, ?, ?, ?, ?)",
                (cid, MODULE_ID, name, "function", "demo/cold.py", 1, 0.0))
        con.execute("UPDATE concepts SET mastery=0.9"
                    " WHERE module_id != ?", (MODULE_ID,))
        con.commit()
        return {"seeded": True, "module_id": MODULE_ID,
                "first": CONCEPTS[0][1]}
    finally:
        con.close()
