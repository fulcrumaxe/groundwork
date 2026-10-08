"""Feature demo: skills unlock from live mastery (F-54 integration).

Full behavior: skills_view builds unlock paths over lesson callees
with >=0.85 mastery owning, rendered as a live section on the module
page -- one skill unlocked, two locked with the next step named.
Owning everything clears the locks; empty input renders nothing.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone

MODULE_ID = "demo-b17-quests"
SKILLS = [
    ("add", "add", 0.9, []),
    ("total", "total", 0.1, ["add"]),
    ("main", "main", 0.0, ["total"]),
]

SCENARIO = {
    "id": "skillquests",
    "kind": "feature",
    "batch": 17,
    "item": "F-54",
    "title": "Skills unlock from live mastery",
    "blurb": "Own the dependencies to unlock the rest -- the module page renders live unlock paths.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 17 - Feature F-54",
         "title": "Skills unlock from live mastery",
         "subtitle": "Own the dependencies to unlock the rest -- the module page renders live unlock paths."},
        {"type": "terminal", "duration": 7,
         "caption": "The rule in one call: 0.85+ owns it, callees chain the path, next names the step.",
         "commands": [
             ["python3", "-c",
              "from groundwork import quests as q; "
              "rows = [{'cid': 'm:add', 'name': 'add'}, "
              "{'cid': 'm:total', 'name': 'total'}, "
              "{'cid': 'm:main', 'name': 'main'}]; "
              "lm = {'add': {'callees': []}, 'total': {'callees': ['add']}, "
              "'main': {'callees': ['total']}}; "
              "b = q.skills_view(rows, lm, "
              "{'add': 0.9, 'total': 0.1, 'main': 0.0}); "
              "print('1 of 3 unlocked:', '1 of 3 skills unlocked' in b); "
              "print('locked steps:', 'quest-locked' in b); "
              "print('next named:', 'next: total' in b)"],
         ]},
        {"type": "chrome", "duration": 11,
         "url_path": "/modules/{seed_module_id}",
         "focus": "#quests",
         "caption": "The live section: one skill unlocked, two locked with their next step named.",
         "assert_js": "() => { const el = document.querySelector('#quests');"
                      " return !!el && el.innerText.includes("
                      "'1 of 3 skills unlocked') && el.innerText.includes("
                      "'locked'); }",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "Own everything and the locks clear; empty or hostile input renders nothing.",
         "commands": [
             ["python3", "-c",
              "from groundwork import quests as q; "
              "rows = [{'cid': 'm:add', 'name': 'add'}, "
              "{'cid': 'm:total', 'name': 'total'}]; "
              "lm = {'add': {'callees': []}, "
              "'total': {'callees': ['add']}}; "
              "b = q.skills_view(rows, lm, {'add': 0.95, 'total': 0.9}); "
              "print('all owned:', '2 of 2 skills unlocked' in b); "
              "print('no locks:', 'quest-locked' not in b); "
              "print('empty/hostile render nothing:', "
              "q.skills_view([], {}, {}) == '' "
              "and q.skills_view('nope') == '')"],
         ]},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 17",
         "title": "Follow the path.",
         "subtitle": "skills_view renders live mastery -- owned steps unlock."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Plant a three-skill module: add owned, total and main locked."""
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
             "summary": f"Quest skill: {name}.",
             "docstring": f"{name}, quest edition.",
             "callees": callees}
            for node, name, _m, callees in SKILLS
        ]
        con.execute(
            "INSERT INTO modules(id, repo, task_summary, created_at, lessons)"
            " VALUES(?, ?, ?, ?, ?)",
            (MODULE_ID, "demo/b17-quests", "Unlock quest module", now,
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
