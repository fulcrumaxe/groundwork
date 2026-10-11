"""Improvement demo: regeneration status, transparently (I-135).

Full behavior: every confusing-flagged section shows its regen queue
position plus flagged age beside the queue banner on the module page
— a flag is awaiting rewrite with its age, or gone. seed_db plants a
module with two backdated flags.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta, timezone

MODULE_ID = "demo-regen-135"
NODE = "demo/regen.py:rewrite"
CID = f"{MODULE_ID}:{NODE}"

SCENARIO = {
    "id": "regenstat",
    "kind": "improvement",
    "batch": 22,
    "item": "I-135",
    "title": "Regeneration status",
    "blurb": "Flagged sections show queue position and age — nothing waits silently.",
    "beats": [
        {"type": "title", "duration": 4,
         "kicker": "Batch 22 - Improvement I-135",
         "title": "Regeneration status",
         "subtitle": "Flagged means queued -- visibly, with its age."},
        {"type": "chrome", "duration": 9,
         "url_path": "/modules/{seed_mid}",
         "focus": "#regen-status",
         "caption": "Each flagged section names its queue position and flagged age.",
         "assert_js": "() => { const el = document.getElementById('regen-status'); return !!el && el.textContent.includes('#1 in queue') && el.textContent.includes('#2 in queue'); }",
         "assert_want": "True"},
        {"type": "terminal", "duration": 8,
         "caption": "No new storage: positions come from the existing flags table.",
         "commands": [
             ["python3", "-c",
              "import os; from groundwork import regenstat as m; "
              "db = os.environ.get('DEMO_DB', 'groundwork.db'); "
              "rows = m.flag_statuses(db, '{seed_mid}'); "
              "print('flags:', len(rows)); "
              "[print(r['position'], r['section'], r['flagged_at']) for r in rows]; "
              "print('quiet module:', m.flag_statuses(db, 'nope'))"],
         ]},
        {"type": "chrome", "duration": 7,
         "url_path": "/status",
         "focus": "#status-b22-regenstat",
         "caption": "Status documents the rule with a live sample.",
         "assert_js": "() => !!document.querySelector('#status-b22-regenstat')",
         "assert_want": "True"},
        {"type": "title", "duration": 4,
         "kicker": "Groundwork - Batch 22",
         "title": "Awaiting rewrite, aged.",
         "subtitle": "regenstat.py lists the queue -- position plus age, no fake states."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Plant a module with two backdated confusing flags."""
    con = sqlite3.connect(db_path)
    try:
        now = datetime.now(timezone.utc)
        stamped = now.strftime("%Y-%m-%dT%H:%M:%SZ")
        con.execute("DELETE FROM concepts WHERE module_id=?", (MODULE_ID,))
        con.execute("DELETE FROM modules WHERE id=?", (MODULE_ID,))
        con.execute(
            "CREATE TABLE IF NOT EXISTS confusing_flags ("
            " section_id TEXT PRIMARY KEY,"
            " flagged_at TEXT NOT NULL DEFAULT"
            " (strftime('%Y-%m-%dT%H:%M:%SZ','now')))")
        con.execute("DELETE FROM confusing_flags WHERE section_id LIKE ?",
                    (f"{MODULE_ID}:%",))
        lessons = [
            {"concept_id": NODE, "name": "Rewrite Me",
             "kind": "function", "file": "demo/regen.py", "line": 1,
             "summary": "A section awaiting rewrite."},
        ]
        con.execute(
            "INSERT INTO modules(id, repo, task_summary, created_at, lessons)"
            " VALUES(?, ?, ?, ?, ?)",
            (MODULE_ID, "demo/regenstat", "Regen-status module", stamped,
             json.dumps(lessons)))
        con.execute(
            "INSERT INTO concepts(id, module_id, name, kind, file,"
            " line, mastery) VALUES(?, ?, ?, ?, ?, ?, ?)",
            (CID, MODULE_ID, "Rewrite Me", "function",
             "demo/regen.py", 1, 0.0))
        old = (now - timedelta(days=2)).strftime("%Y-%m-%dT%H:%M:%SZ")
        fresh = (now - timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
        con.execute(
            "INSERT INTO confusing_flags(section_id, flagged_at)"
            " VALUES(?, ?)", (f"{MODULE_ID}:what-it-does", old))
        con.execute(
            "INSERT INTO confusing_flags(section_id, flagged_at)"
            " VALUES(?, ?)", (f"{MODULE_ID}:contracts", fresh))
        con.commit()
        return {"seeded": True, "mid": MODULE_ID, "old": old,
                "fresh": fresh}
    finally:
        con.close()
