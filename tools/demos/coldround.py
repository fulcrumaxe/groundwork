"""Feature demo: attempt cold, then study (F-56 integration).

Full behavior: /due?mode=cold swaps the queue for a primed round
over unseen concepts -- owned and due stay out, each pick carries
its priming line and a study link, and a Full-queue link leads back.
The plain queue waits one click behind.
"""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone

MODULE_ID = "demo-b17-cold"
CONCEPTS = [
    "Brave guess",
    "Stuck point",
    "Retry path",
]
CONTRAST_FRONT = "Cold contrast: the live queue behind the round."
CONTRAST_BACK = "The full queue waits one click back."

SCENARIO = {
    "id": "coldround",
    "kind": "feature",
    "batch": 17,
    "item": "F-56",
    "title": "Attempt cold, then study",
    "blurb": "mode=cold swaps the queue for primed unseen concepts -- owned and due stay out.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 17 - Feature F-56",
         "title": "Attempt cold, then study",
         "subtitle": "mode=cold swaps the queue for primed unseen concepts -- owned and due stay out."},
        {"type": "terminal", "duration": 7,
         "caption": "The rule in one call: owned and due never enter, adjacent modules first.",
         "commands": [
             ["python3", "-c",
              "from groundwork import coldattempt as m; "
              "pool = [{'id': 'a', 'module_id': 'm1'}, "
              "{'id': 'b', 'module_id': 'm1'}, "
              "{'id': 'c', 'module_id': 'm2'}]; "
              "s = m.cold_session(pool, owned_ids={'a'}, due_ids=set()); "
              "print('picks:', [i['concept_id'] for i in s['items']]); "
              "print('prime:', s['items'][0]['prime']); "
              "print('note:', s['note']); "
              "e = m.cold_session([], set(), set()); "
              "print('empty:', e['note'])"],
         ]},
        {"type": "chrome", "duration": 11,
         "url_path": "/due?mode=cold",
         "caption": "The cold round: three unseen concepts, primed, study-linked -- no queue cards.",
         "assert_js": "() => document.body.innerText.includes('Cold round')"
                      " && document.body.innerText.includes('{seed_first}')"
                      " && document.body.innerText.includes('Full queue')"
                      " && !document.querySelector('article')",
         "assert_want": "True"},
        {"type": "chrome", "duration": 7,
         "url_path": "/due",
         "caption": "Full queue behind it: the live queue waits one click back.",
         "assert_js": "() => document.body.innerText.includes('Card 1 of 1')"
                      " && document.body.innerText.includes('Cold contrast')",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 17",
         "title": "Struggle first.",
         "subtitle": "cold_box renders unseen concepts -- mastered and due excluded."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Plant three unseen concepts; own everything else.

    Owning all pre-existing concepts empties the cold pool of
    strangers, so the round holds exactly the three seeded picks.
    One live card stays due as the behind-the-round queue; probes
    are suppressed globally (last_probe=now) so it stands alone.
    """
    con = sqlite3.connect(db_path)
    try:
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        nodes = [f"demo/cold.py:{i}" for i in range(len(CONCEPTS))]
        cids = [f"{MODULE_ID}:{node}" for node in nodes]
        for cid in cids:
            con.execute("DELETE FROM cards WHERE concept_id=?", (cid,))
            con.execute("DELETE FROM concepts WHERE id=?", (cid,))
        con.execute("DELETE FROM modules WHERE id=?", (MODULE_ID,))
        con.execute(
            "INSERT INTO modules(id, repo, task_summary, created_at)"
            " VALUES(?, ?, ?, ?)",
            (MODULE_ID, "demo/b17-cold", "Cold round module", now))
        for (node, name), cid in zip(zip(nodes, CONCEPTS), cids):
            con.execute(
                "INSERT INTO concepts(id, module_id, name, kind, file,"
                " line, mastery) VALUES(?, ?, ?, ?, ?, ?, ?)",
                (cid, MODULE_ID, name, "function", "demo/cold.py", 1, 0.0))
        con.execute("UPDATE concepts SET mastery=0.9"
                    " WHERE module_id != ?", (MODULE_ID,))
        con.execute("UPDATE cards SET due='2030-01-01T00:00:00Z',"
                    " last_probe=?", (now,))
        row = con.execute(
            "SELECT id FROM cards WHERE stale = 0"
            " ORDER BY rowid LIMIT 1").fetchone()
        if row:
            con.execute(
                "UPDATE cards SET due='2000-01-01T00:00:00Z', front=?,"
                " back=? WHERE id=?",
                (CONTRAST_FRONT, CONTRAST_BACK, row[0]))
        con.commit()
        by_cid = sorted(zip(cids, CONCEPTS))
        return {"seeded": True, "module_id": MODULE_ID,
                "first": by_cid[0][1],
                "contrast": row[0] if row else None}
    finally:
        con.close()
