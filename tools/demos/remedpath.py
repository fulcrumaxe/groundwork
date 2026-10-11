"""Feature demo: remediation paths (F-100).

Full behavior: a failed concept pulls its unmastered prerequisites ahead of
the retry in the due queue, so the learner revisits foundations first.
seed_db plants a failed advanced card whose lesson needs Total Base, plus a
more-overdue calm card; the MCP beat shows the prereq lifted to the head
with its remedial flag.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone

MODULE_ID = "demo-remedpath-100"
HARD_NODE = "demo/path.py:advanced"
BASE_NODE = "demo/path.py:base"
CALM_NODE = "demo/path.py:calm"
HARD_CID = f"{MODULE_ID}:{HARD_NODE}"
BASE_CID = f"{MODULE_ID}:{BASE_NODE}"
CALM_CID = f"{MODULE_ID}:{CALM_NODE}"
HARD_ID = "demo-remed-hard"
PRE_ID = "demo-remed-pre"
CALM_ID = "demo-remed-calm"

SCENARIO = {
    "id": "remedpath",
    "kind": "feature",
    "batch": 21,
    "item": "F-100",
    "title": "Remediation paths",
    "blurb": "Fail a concept and its unmastered prerequisites jump ahead of the retry.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 21 - Feature F-100",
         "title": "Remediation paths",
         "subtitle": "Fail forward -- foundations first, retry second."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b21-remedpath",
         "caption": "Status documents the path rule with a live sample.",
         "assert_js": "() => !!document.querySelector('#status-b21-remedpath')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 9,
         "caption": "The rule in one line: unmastered prereqs first, failed concept last.",
         "commands": [
             ["python3", "-c",
              "from groundwork import remedpath as m; "
              "pmap = {'Advanced Sums': ['Total Base', 'Loop Order']}; "
              "mastery = {'Loop Order': 5.0}; "
              "path = m.remediation_path('Advanced Sums', pmap, mastery); "
              "print('path:', path); "
              "print(m.describe_path(path, 'Advanced Sums')); "
              "print('calm:', m.remediation_path('Unknown', pmap, mastery))"],
         ]},
        {"type": "terminal", "duration": 11,
         "caption": "The live queue: the prereq lifts past a more-overdue calm card.",
         "commands": [
             ["python3", "-c",
              "import os; from groundwork import mcp as mcpmod; "
              "db = os.environ.get('DEMO_DB', 'groundwork.db'); "
              "out = mcpmod.MCPServer(db).tool_list_due_reviews({'limit': 2000}); "
              "due = out['due']; ids = [c['id'] for c in due]; "
              "pre = due[ids.index('{seed_pre_id}')]; "
              "print('queue head:', ids[:3]); "
              "print('prereq leads:', ids.index('{seed_pre_id}') == 0); "
              "print('remedial:', pre.get('remedial'), '| for:', pre.get('remediation_for'))"],
         ]},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 21",
         "title": "Foundations first.",
         "subtitle": "remedpath.py scaffolds retries -- calm queues stay put."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Plant a failed advanced card, its prereq, and an overdue calm card."""
    con = sqlite3.connect(db_path)
    try:
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        for cid in (HARD_ID, PRE_ID, CALM_ID):
            con.execute("DELETE FROM reviews WHERE card_id=?", (cid,))
            con.execute("DELETE FROM cards WHERE id=?", (cid,))
        con.execute("DELETE FROM concepts WHERE module_id=?", (MODULE_ID,))
        con.execute("DELETE FROM modules WHERE id=?", (MODULE_ID,))
        lessons = [
            {"concept_id": HARD_NODE, "name": "Advanced Sums",
             "kind": "function", "file": "demo/path.py", "line": 10,
             "summary": "Advanced running sums.",
             "needs": ["Total Base"]},
            {"concept_id": BASE_NODE, "name": "Total Base",
             "kind": "function", "file": "demo/path.py", "line": 1,
             "summary": "Seed and add."},
            {"concept_id": CALM_NODE, "name": "Calm Drills",
             "kind": "function", "file": "demo/path.py", "line": 20,
             "summary": "Unrelated calm drills."},
        ]
        con.execute(
            "INSERT INTO modules(id, repo, task_summary, created_at, lessons)"
            " VALUES(?, ?, ?, ?, ?)",
            (MODULE_ID, "demo/remedpath", "Remediation paths module", now,
             json.dumps(lessons)))
        con.execute(
            "INSERT INTO concepts(id, module_id, name, kind, file,"
            " line, mastery) VALUES(?, ?, ?, ?, ?, ?, ?)",
            (HARD_CID, MODULE_ID, "Advanced Sums", "function",
             "demo/path.py", 10, 0.0))
        con.execute(
            "INSERT INTO concepts(id, module_id, name, kind, file,"
            " line, mastery) VALUES(?, ?, ?, ?, ?, ?, ?)",
            (BASE_CID, MODULE_ID, "Total Base", "function",
             "demo/path.py", 1, 0.0))
        con.execute(
            "INSERT INTO concepts(id, module_id, name, kind, file,"
            " line, mastery) VALUES(?, ?, ?, ?, ?, ?, ?)",
            (CALM_CID, MODULE_ID, "Calm Drills", "function",
             "demo/path.py", 20, 0.0))
        con.execute(
            "INSERT INTO cards(id, concept_id, exercise_type, front, back, due)"
            " VALUES(?, ?, '1', ?, ?, ?)",
            (HARD_ID, HARD_CID, "Sum with a twist?", "42.",
             "2001-01-01T12:00:00Z"))
        con.execute(
            "INSERT INTO cards(id, concept_id, exercise_type, front, back, due)"
            " VALUES(?, ?, '1', ?, ?, ?)",
            (PRE_ID, BASE_CID, "What seeds it?", "0.",
             "2000-06-01T12:00:00Z"))
        con.execute(
            "INSERT INTO cards(id, concept_id, exercise_type, front, back, due)"
            " VALUES(?, ?, '1', ?, ?, ?)",
            (CALM_ID, CALM_CID, "What adds?", "Rows.",
             "1999-01-01T12:00:00Z"))
        con.execute(
            "INSERT INTO reviews(card_id, grade, confidence, submission)"
            " VALUES(?, 1, 2, 'remedpath seed')", (HARD_ID,))
        con.commit()
        return {"seeded": True, "hard_id": HARD_ID, "pre_id": PRE_ID,
                "calm_id": CALM_ID}
    finally:
        con.close()
