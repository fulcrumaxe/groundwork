"""Feature demo: prerequisite unlock quests (F-54).

Full behavior: a three-skill module where one owned concept unlocks
its dependent path step by step -- the module page renders the live
quest section, and the terminal re-runs the pure path builder.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone

MODULE_ID = "demo-quests-54"
SKILLS = [
    ("demo/quest.py:read", "Read lessons", 0.9, []),
    ("demo/quest.py:grade", "Grade cards", 0.0, ["Read lessons"]),
    ("demo/quest.py:serve", "Serve the queue", 0.0,
     ["Grade cards", "Read lessons"]),
]

SCENARIO = {
    "id": "quests",
    "kind": "feature",
    "batch": 12,
    "item": "F-54",
    "title": "Unlock quests",
    "blurb": "Own X to unlock Y -- each locked skill shows its unlock path.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 12 - Feature F-54",
         "title": "Unlock quests",
         "subtitle": "Own X to unlock Y -- the path shows each step."},
        {"type": "chrome", "duration": 7,
         "url_path": "/status",
         "focus": "#status-b12-quests",
         "caption": "Status demos the path: unlocked steps, then the locked rest.",
         "assert_js": "() => { const el = document.querySelector("
                      "\"#status-b12-quests\"); return !!el && "
                      "!!document.querySelector('ol.quest-path'); }",
         "assert_want": "True"},
        {"type": "terminal", "duration": 9,
         "caption": "The rule in one line: chain longest-first, next is first unowned.",
         "commands": [
             ["python3", "-c",
              "from groundwork import quests as m; "
              "edges = {'Serve the queue': ['Grade cards', 'Read lessons'], "
              "'Grade cards': ['Read lessons'], 'Read lessons': []}; "
              "p = m.quest_path('Serve the queue', edges, {'Read lessons'}); "
              "print('chain:', p['chain']); "
              "print('unlocked:', p['unlocked'], 'next:', p['next']); "
              "h = m.quests_html(p); "
              "print('classes:', 'quest-unlocked' in h, 'quest-locked' in h)"],
         ]},
        {"type": "chrome", "duration": 10,
         "url_path": "/modules/{seed_module_id}",
         "focus": "#quests",
         "caption": "The module quests: one skill unlocked, two locked with next steps.",
         "assert_js": "() => { const el = document.querySelector('#quests');"
                      " return !!el && el.innerText.includes('locked'); }",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 12",
         "title": "Follow the path.",
         "subtitle": "quests.py linearises prereqs -- owned steps unlock."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Plant a three-skill module: Read owned, Grade and Serve locked."""
    con = sqlite3.connect(db_path)
    try:
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        cids = [f"{MODULE_ID}:{node}" for node, _n, _m, _c in SKILLS]
        for cid in cids:
            con.execute("DELETE FROM cards WHERE concept_id=?", (cid,))
            con.execute("DELETE FROM concepts WHERE id=?", (cid,))
        con.execute("DELETE FROM modules WHERE id=?", (MODULE_ID,))
        lessons = [
            {"concept_id": node, "name": name, "kind": "function",
             "file": "demo/quest.py", "line": 1,
             "summary": f"Quest skill: {name.lower()}.",
             "docstring": f"{name}, quest edition.",
             "callees": callees}
            for node, name, _m, callees in SKILLS
        ]
        con.execute(
            "INSERT INTO modules(id, repo, task_summary, created_at, lessons)"
            " VALUES(?, ?, ?, ?, ?)",
            (MODULE_ID, "demo/quests", "Unlock quest module", now,
             json.dumps(lessons)))
        for (node, name, mastery, _c), cid in zip(SKILLS, cids):
            con.execute(
                "INSERT INTO concepts(id, module_id, name, kind, file,"
                " line, mastery) VALUES(?, ?, ?, ?, ?, ?, ?)",
                (cid, MODULE_ID, name, "function", "demo/quest.py", 1,
                 mastery))
        con.commit()
        return {"seeded": True, "module_id": MODULE_ID}
    finally:
        con.close()
