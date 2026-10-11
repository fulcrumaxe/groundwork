"""Feature demo: boredom rung-ups (F-97).

Full behavior: a concept with a 3-pass streak is bored, so its queued cards
lead hardest-first in the due queue -- a rung up instead of more same-level
drills. seed_db plants a bored concept (recall + apply cards, three passes)
beside a more-overdue calm card; the MCP beat shows the reorder.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone

MODULE_ID = "demo-boredom-97"
BORED_NODE = "demo/rungs.py:loops"
CALM_NODE = "demo/rungs.py:total"
BORED_CID = f"{MODULE_ID}:{BORED_NODE}"
CALM_CID = f"{MODULE_ID}:{CALM_NODE}"
RECALL_ID = "demo-bored-recall"
APPLY_ID = "demo-bored-apply"
CALM_ID = "demo-bored-calm"

SCENARIO = {
    "id": "boredom",
    "kind": "feature",
    "batch": 21,
    "item": "F-97",
    "title": "Boredom rung-ups",
    "blurb": "Acing reviews in a row jumps one Bloom rung up instead of more drills.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 21 - Feature F-97",
         "title": "Boredom rung-ups",
         "subtitle": "Three passes in a row? Up a rung -- not more of the same."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b21-boredom",
         "caption": "Status documents the pass-streak rule with a live sample.",
         "assert_js": "() => !!document.querySelector('#status-b21-boredom')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 9,
         "caption": "The rule in one line: a 3-pass streak promotes the hardest card first.",
         "commands": [
             ["python3", "-c",
              "from groundwork import boredom as m; "
              "print('bored:', m.is_bored([3, 4, 5, 4]), '| calm:', m.is_bored([5, 2, 5])); "
              "print('recall ->', m.suggest_rung('recall', [4, 5, 4])); "
              "cards = [{'id': 'r', 'concept_id': 'c', 'exercise_type': '1'}, "
              "{'id': 'a', 'concept_id': 'c', 'exercise_type': '8'}, "
              "{'id': 'k', 'concept_id': 'k', 'exercise_type': '1'}]; "
              "print('order:', [c['id'] for c in m.promote(cards, {'c': [4, 5, 4]})])"],
         ]},
        {"type": "terminal", "duration": 10,
         "caption": "The live queue: the bored concept's apply card jumps the overdue line.",
         "commands": [
             ["python3", "-c",
              "import os; from groundwork import mcp as mcpmod; "
              "db = os.environ.get('DEMO_DB', 'groundwork.db'); "
              "out = mcpmod.MCPServer(db).tool_list_due_reviews({'limit': 2000}); "
              "ids = [c['id'] for c in out['due']]; "
              "print('queue head:', ids[:3]); "
              "print('apply leads recall:', ids.index('{seed_apply_id}') < ids.index('{seed_recall_id}')); "
              "print('bored jumps calm:', ids.index('{seed_apply_id}') < ids.index('{seed_calm_id}'))"],
         ]},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 21",
         "title": "Bored? Climb.",
         "subtitle": "boredom.py promotes rung-ups -- calm queues keep today's order."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Plant a bored concept (recall+apply, 3 passes) + overdue calm card."""
    con = sqlite3.connect(db_path)
    try:
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        for cid in (RECALL_ID, APPLY_ID, CALM_ID):
            con.execute("DELETE FROM reviews WHERE card_id=?", (cid,))
            con.execute("DELETE FROM cards WHERE id=?", (cid,))
        con.execute("DELETE FROM concepts WHERE module_id=?", (MODULE_ID,))
        con.execute("DELETE FROM modules WHERE id=?", (MODULE_ID,))
        lessons = [
            {"concept_id": BORED_NODE, "name": "loops", "kind": "function",
             "file": "demo/rungs.py", "line": 1, "summary": "Loop drills."},
            {"concept_id": CALM_NODE, "name": "total", "kind": "function",
             "file": "demo/rungs.py", "line": 10, "summary": "Total drills."},
        ]
        con.execute(
            "INSERT INTO modules(id, repo, task_summary, created_at, lessons)"
            " VALUES(?, ?, ?, ?, ?)",
            (MODULE_ID, "demo/boredom", "Boredom rung-ups module", now,
             json.dumps(lessons)))
        con.execute(
            "INSERT INTO concepts(id, module_id, name, kind, file,"
            " line, mastery) VALUES(?, ?, ?, ?, ?, ?, ?)",
            (BORED_CID, MODULE_ID, "loops", "function",
             "demo/rungs.py", 1, 0.0))
        con.execute(
            "INSERT INTO concepts(id, module_id, name, kind, file,"
            " line, mastery) VALUES(?, ?, ?, ?, ?, ?, ?)",
            (CALM_CID, MODULE_ID, "total", "function",
             "demo/rungs.py", 10, 0.0))
        con.execute(
            "INSERT INTO cards(id, concept_id, exercise_type, front, back, due)"
            " VALUES(?, ?, '1', ?, ?, ?)",
            (RECALL_ID, BORED_CID, "What opens a loop?", "for.",
             "2001-01-01T00:00:00Z"))
        con.execute(
            "INSERT INTO cards(id, concept_id, exercise_type, front, back, due)"
            " VALUES(?, ?, '8', ?, ?, ?)",
            (APPLY_ID, BORED_CID, "What prints?", "3.",
             "2001-01-01T00:00:00Z"))
        con.execute(
            "INSERT INTO cards(id, concept_id, exercise_type, front, back, due)"
            " VALUES(?, ?, '1', ?, ?, ?)",
            (CALM_ID, CALM_CID, "What seeds it?", "0.",
             "2000-01-01T00:00:00Z"))
        for grade in (4, 5, 4):
            con.execute(
                "INSERT INTO reviews(card_id, grade, confidence, submission)"
                " VALUES(?, ?, 4, 'boredom seed')", (RECALL_ID, grade))
        con.commit()
        return {"seeded": True, "recall_id": RECALL_ID,
                "apply_id": APPLY_ID, "calm_id": CALM_ID}
    finally:
        con.close()
