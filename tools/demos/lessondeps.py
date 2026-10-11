"""Improvement demo: understand-first jump links (I-131).

Full behavior: a lesson declaring needs renders an "Understand first" list
whose jump links hit the earlier lessons' real section anchors (node slugs).
seed_db plants a two-lesson module where the second needs the first.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone

MODULE_ID = "demo-lessondeps-131"
NODE_A = "demo/loops.py:For Loops"
NODE_B = "demo/loops.py:Accumulators"
CID_A = f"{MODULE_ID}:{NODE_A}"
CID_B = f"{MODULE_ID}:{NODE_B}"

SCENARIO = {
    "id": "lessondeps",
    "kind": "improvement",
    "batch": 21,
    "item": "I-131",
    "title": "Understand-first jump links",
    "blurb": "Each lesson lists what to read first, with jump links that land.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 21 - Improvement I-131",
         "title": "Understand-first jump links",
         "subtitle": "Foundations first -- every jump link lands on a real section."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b21-lessondeps",
         "caption": "Status documents the dependency lists with a live sample.",
         "assert_js": "() => !!document.querySelector('#status-b21-lessondeps')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 8,
         "caption": "The rule in one line: needs resolve to earlier lessons, slug-matched.",
         "commands": [
             ["python3", "-c",
              "from groundwork import lessondeps as m; "
              "a = {'name': 'For Loops', 'concept_id': 'demo/loops.py:For Loops'}; "
              "b = {'name': 'Accumulators', 'needs': ['For Loops', 'Charts']}; "
              "print('needs:', m.needs_of(b)); "
              "print('deps:', m.deps_for(b, [a])); "
              "print(m.deps_html(b, [a])); "
              "print('no data:', repr(m.deps_html({'name': 'x'}, [a])))"],
         ]},
        {"type": "chrome", "duration": 10,
         "url_path": "/modules/{seed_mid}",
         "focus": "p.deps",
         "caption": "The second lesson lists its foundation -- node-slug anchor.",
         "assert_js": "() => { const a = document.querySelector('p.deps a'); "
                      "return !!a && a.getAttribute('href').includes("
                      "'demo-loops-py-for-loops'); }",
         "assert_want": "True"},
        {"type": "terminal", "duration": 6,
         "caption": "Every deps link on the live page lands on a real section.",
         "commands": [
             ["python3", "-c",
              "import os, re, sys; sys.path.insert(0, 'tests'); "
              "from test_web import handler_for; "
              "db = os.environ.get('DEMO_DB', 'groundwork.db'); "
              "body = handler_for(db).module_html('demo-lessondeps-131'); "
              "m = re.search(r\"<p class='deps'>.*?</p>\", body).group(0); "
              "hrefs = re.findall(r\"href='#(lesson-[^']+)'\", m); "
              "ids = set(re.findall(r\"id='(lesson-[^']+)'\", body)); "
              "print('links:', hrefs); "
              "print('all land:', all(h in ids for h in hrefs))"],
         ]},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 21",
         "title": "Foundations first.",
         "subtitle": "lessondeps.py links needs -- unmatched names never render."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Plant a two-lesson module where the second needs the first."""
    con = sqlite3.connect(db_path)
    try:
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        con.execute("DELETE FROM concepts WHERE module_id=?", (MODULE_ID,))
        con.execute("DELETE FROM modules WHERE id=?", (MODULE_ID,))
        lessons = [
            {"concept_id": NODE_A, "name": "For Loops", "kind": "function",
             "file": "demo/loops.py", "line": 1,
             "summary": "Loop over rows in order."},
            {"concept_id": NODE_B, "name": "Accumulators", "kind": "function",
             "file": "demo/loops.py", "line": 20,
             "summary": "Sum a running total inside the loop.",
             "needs": ["For Loops"]},
        ]
        con.execute(
            "INSERT INTO modules(id, repo, task_summary, created_at, lessons)"
            " VALUES(?, ?, ?, ?, ?)",
            (MODULE_ID, "demo/lessondeps", "Dependency links module", now,
             json.dumps(lessons)))
        for cid, les in ((CID_A, lessons[0]), (CID_B, lessons[1])):
            con.execute(
                "INSERT INTO concepts(id, module_id, name, kind, file,"
                " line, mastery) VALUES(?, ?, ?, ?, ?, ?, ?)",
                (cid, MODULE_ID, les["name"], les["kind"], les["file"],
                 les["line"], 0.0))
        con.commit()
        return {"seeded": True, "mid": MODULE_ID}
    finally:
        con.close()
