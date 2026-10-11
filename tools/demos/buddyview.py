"""Improvement demo: study-with-a-friend twin panes (I-143).

Full behavior: two distinct ?buddy= names on a module page render
one lesson in two labelled panes with per-friend position markers
— local only, no sync, no network. Solo visits render exactly as
before. seed_db plants a one-lesson module.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone

MODULE_ID = "demo-buddyview-143"
NODE = "demo/pair.py:read_together"
CID = f"{MODULE_ID}:{NODE}"

SCENARIO = {
    "id": "buddyview",
    "kind": "improvement",
    "batch": 23,
    "item": "I-143",
    "title": "Study with a friend",
    "blurb": "Same lesson side by side -- two panes, local only.",
    "beats": [
        {"type": "title", "duration": 4,
         "kicker": "Batch 23 - Improvement I-143",
         "title": "Study with a friend",
         "subtitle": "One lesson, two panes -- read together on one machine."},
        {"type": "chrome", "duration": 10,
         "url_path": "/modules/{seed_mid}?buddy=Ada&buddy=Grace",
         "focus": ".buddy-view",
         "caption": "Two names in ?buddy= render two labelled panes for one lesson.",
         "assert_js": "() => document.body.innerText.includes(\"Ada's pane\") "
                      "&& document.body.innerText.includes(\"Grace's pane\")",
         "assert_want": "True"},
        {"type": "terminal", "duration": 8,
         "caption": "Two distinct friends open the view; solo visits stay byte-identical.",
         "commands": [
             ["python3", "-c",
              "from groundwork import buddyview as m; "
              "print('pair:', bool(m.buddy_html('Loops', ['Ada', 'Grace']))); "
              "print('solo:', repr(m.buddy_html('Loops', ['Ada']))); "
              "print('markers:', m.buddy_markers([['Ada', 20], ['Grace', 55]]))"],
         ]},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b23-buddyview",
         "caption": "Status states the scope: local panes, no sync, no network.",
         "assert_js": "() => !!document.querySelector('#status-b23-buddyview')",
         "assert_want": "True"},
        {"type": "title", "duration": 4,
         "kicker": "Groundwork - Batch 23",
         "title": "Read it together.",
         "subtitle": "buddyview.py renders twin panes -- solo pages never change."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Plant a one-lesson module for the twin-pane view."""
    con = sqlite3.connect(db_path)
    try:
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        con.execute("DELETE FROM reviews WHERE card_id LIKE ?",
                    (MODULE_ID + ":%",))
        con.execute("DELETE FROM cards WHERE concept_id LIKE ?",
                    (MODULE_ID + ":%",))
        con.execute("DELETE FROM concepts WHERE module_id=?", (MODULE_ID,))
        con.execute("DELETE FROM modules WHERE id=?", (MODULE_ID,))
        lessons = [
            {"concept_id": NODE, "name": "read_together",
             "kind": "function", "file": "demo/pair.py", "line": 1,
             "summary": "read_together renders one lesson twice, once per friend.",
             "docstring": "Twin panes, local only.",
             "callers": [], "callees": [], "key_lines": "",
             "source": "def read_together(lesson, friends):\n    return panes\n",
             "complexity": 1,
             "how": ["Name two friends.", "Each gets a labelled pane."]},
        ]
        con.execute(
            "INSERT INTO modules(id, repo, task_summary, created_at, lessons)"
            " VALUES(?, ?, ?, ?, ?)",
            (MODULE_ID, "", "Buddy-view module", now,
             json.dumps(lessons)))
        con.execute(
            "INSERT INTO concepts(id, module_id, name, kind, file,"
            " line, mastery) VALUES(?, ?, ?, ?, ?, ?, ?)",
            (CID, MODULE_ID, "read_together", "function",
             "demo/pair.py", 1, 0.0))
        con.commit()
        return {"seeded": True, "mid": MODULE_ID}
    finally:
        con.close()
