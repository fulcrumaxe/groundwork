"""Improvement demo: reading walkthroughs aloud (I-138).

Full behavior: every replay block on the lesson path gains a Listen
button that reads the current step via speechSynthesis — guarded so
browsers without speech (or without JS) render byte-identical, a
second click stops. seed_db plants a traced lesson for a live block.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone

MODULE_ID = "demo-readout-138"
NODE = "demo/speak.py:add"
CID = f"{MODULE_ID}:{NODE}"

SCENARIO = {
    "id": "readout",
    "kind": "improvement",
    "batch": 22,
    "item": "I-138",
    "title": "Reading aloud",
    "blurb": "Walkthrough steps grow a Listen button — the trace, spoken.",
    "beats": [
        {"type": "title", "duration": 4,
         "kicker": "Batch 22 - Improvement I-138",
         "title": "Reading aloud",
         "subtitle": "Replay blocks that speak -- guarded, so silence stays silent."},
        {"type": "chrome", "duration": 9,
         "url_path": "/modules/{seed_mid}",
         "focus": "#replay",
         "caption": "The traced lesson renders a replay block with the speech wire.",
         "assert_js": "() => !!document.querySelector('script[data-readaloud]') && !!document.querySelector('.replay')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 8,
         "caption": "The exact injected button, and the guard that keeps no-speech pages clean.",
         "commands": [
             ["python3", "-c",
              "from groundwork import readout as m; "
              "print('button:', m.sample_button_html()); "
              "js = m.script_js(); "
              "print('guards speech:', 'speechSynthesis' in js); "
              "print('toggles stop:', js.count('cancel()')); "
              "print('targets replay:', chr(39) + '.replay' + chr(39) in js)"],
         ]},
        {"type": "chrome", "duration": 7,
         "url_path": "/status",
         "focus": "#status-b22-readout",
         "caption": "Status shows the injected button exactly as it looks.",
         "assert_js": "() => !!document.querySelector('#status-b22-readout') && !!document.querySelector('button.readaloud')",
         "assert_want": "True"},
        {"type": "title", "duration": 4,
         "kicker": "Groundwork - Batch 22",
         "title": "Listen to this step.",
         "subtitle": "readout.py injects one guarded script -- click toggles stop."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Plant a module with a measured-trace lesson (live replay block)."""
    con = sqlite3.connect(db_path)
    try:
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        con.execute("DELETE FROM concepts WHERE module_id=?", (MODULE_ID,))
        con.execute("DELETE FROM modules WHERE id=?", (MODULE_ID,))
        lessons = [
            {"concept_id": NODE, "name": "Add Aloud",
             "kind": "function", "file": "demo/speak.py", "line": 1,
             "summary": "Add two numbers, narrated.",
             "worked": {"call": "add(2, 3)", "output": "5",
                        "trace": {"var": "total",
                                  "steps": ["1", "3", "5"]}},
             "how": ["Sets total.", "Adds.", "Hands back."],
             "dualcode": {"steps": [], "states": []}},
        ]
        con.execute(
            "INSERT INTO modules(id, repo, task_summary, created_at, lessons)"
            " VALUES(?, ?, ?, ?, ?)",
            (MODULE_ID, "demo/readout", "Read-aloud module", now,
             json.dumps(lessons)))
        con.execute(
            "INSERT INTO concepts(id, module_id, name, kind, file,"
            " line, mastery) VALUES(?, ?, ?, ?, ?, ?, ?)",
            (CID, MODULE_ID, "Add Aloud", "function",
             "demo/speak.py", 1, 0.0))
        con.commit()
        return {"seeded": True, "mid": MODULE_ID}
    finally:
        con.close()
