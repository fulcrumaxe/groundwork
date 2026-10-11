"""Improvement demo: gentle still-with-us reading nudge (I-144).

Full behavior: after ten idle minutes a hidden banner asks
"still with us?" with a Keep-reading button that re-hides it;
the timer resets on any activity and dismissal never blocks.
seed_db plants a one-lesson module; the beat reveals the banner
exactly as the timer would.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone

MODULE_ID = "demo-readnudge-144"
NODE = "demo/read.py:long_lesson"
CID = f"{MODULE_ID}:{NODE}"

SCENARIO = {
    "id": "readnudge",
    "kind": "improvement",
    "batch": 23,
    "item": "I-144",
    "title": "Still-with-us nudge",
    "blurb": "Ten idle minutes raise a gentle keep-reading nudge.",
    "beats": [
        {"type": "title", "duration": 4,
         "kicker": "Batch 23 - Improvement I-144",
         "title": "Still-with-us nudge",
         "subtitle": "Long reads check in -- gently, and never blocking."},
        {"type": "chrome", "duration": 10,
         "url_path": "/modules/{seed_mid}",
         "focus": "#readnudge",
         "caption": "After ten idle minutes the hidden banner asks -- Still with us?",
         "js": ["() => { const b = document.getElementById('readnudge'); "
                "if (!b) return 'banner-missing'; b.hidden = false; "
                "return 'shown'; }"],
         "assert_js": "() => document.body.innerText.includes('Still with us?') "
                      "&& document.body.innerText.includes('Keep reading')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 8,
         "caption": "The rule in one line: idle past the limit nudges, activity resets it.",
         "commands": [
             ["python3", "-c",
              "from groundwork import readnudge as m; "
              "print('idle 600s:', m.should_nudge(0, 600)); "
              "print('idle 599s:', m.should_nudge(0, 599)); "
              "print('hostile:', m.should_nudge('x', None)); "
              "print('limit:', m.IDLE_SECS, 'seconds')"],
         ]},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b23-readnudge",
         "caption": "Status states the guarantee: without JS the page never changes.",
         "assert_js": "() => !!document.querySelector('#status-b23-readnudge')",
         "assert_want": "True"},
        {"type": "title", "duration": 4,
         "kicker": "Groundwork - Batch 23",
         "title": "Keep reading?",
         "subtitle": "readnudge.py arms one timer -- activity resets it, dismissal is free."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Plant a one-lesson module carrying the nudge banner."""
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
            {"concept_id": NODE, "name": "long_lesson",
             "kind": "function", "file": "demo/read.py", "line": 1,
             "summary": "long_lesson is a slow read that deserves a check-in.",
             "docstring": "Ten idle minutes raise the banner.",
             "callers": [], "callees": [], "key_lines": "",
             "source": "def long_lesson():\n    return read()\n",
             "complexity": 1,
             "how": ["Settle in.", "Read slowly."]},
        ]
        con.execute(
            "INSERT INTO modules(id, repo, task_summary, created_at, lessons)"
            " VALUES(?, ?, ?, ?, ?)",
            (MODULE_ID, "", "Reading-nudge module", now,
             json.dumps(lessons)))
        con.execute(
            "INSERT INTO concepts(id, module_id, name, kind, file,"
            " line, mastery) VALUES(?, ?, ?, ?, ?, ?, ?)",
            (CID, MODULE_ID, "long_lesson", "function",
             "demo/read.py", 1, 0.0))
        con.commit()
        return {"seeded": True, "mid": MODULE_ID}
    finally:
        con.close()
