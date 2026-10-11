"""Improvement demo: calm walkthrough reveals (I-140).

Full behavior: every stepped replay ships a hidden full-steps twin
on the lesson path, and one page script swaps the stepper for the
whole trace when reduced-motion is set — without the preference (or
JS) the stepper stands alone exactly as before.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone

MODULE_ID = "demo-calm-140"
NODE = "demo/calm.py:add"
CID = f"{MODULE_ID}:{NODE}"

SCENARIO = {
    "id": "calmreplay",
    "kind": "improvement",
    "batch": 22,
    "item": "I-140",
    "title": "Calm walkthrough reveals",
    "blurb": "Reduced-motion learners get the whole trace at once — no stepping.",
    "beats": [
        {"type": "title", "duration": 4,
         "kicker": "Batch 22 - Improvement I-140",
         "title": "Calm walkthrough reveals",
         "subtitle": "Stepping is motion too -- the full trace ships beside it."},
        {"type": "chrome", "duration": 9,
         "url_path": "/modules/{seed_mid}",
         "focus": "#replay",
         "caption": "The stepper stands alone; its hidden full-trace twin ships with it.",
         "assert_js": "() => !!document.querySelector('.replay') && !!document.querySelector('#replay-full[hidden]') && !!document.querySelector('script[data-calm-replay]')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 8,
         "caption": "The twin reuses the stepper's own steps, so they never disagree.",
         "commands": [
             ["python3", "-c",
              "from groundwork import calmreplay as m, replay as r; "
              "les = {'worked': {'trace': {'steps': ['1', '3', '5']}}, 'how': ['Sets total.', 'Adds.', 'Hands back.']}; "
              "print('stepper rows:', len(r.replay_steps(les))); "
              "twin = m.instant_html(les); "
              "print('twin hidden:', 'hidden' in twin, '| steps:', twin.count('<tr><td>')); "
              "print('traceless:', repr(m.instant_html({}))); "
              "print('media guard:', 'prefers-reduced-motion' in m.script_js())"],
         ]},
        {"type": "chrome", "duration": 7,
         "url_path": "/status",
         "js": ["() => { const o = document.getElementById('owned-headline'); if (o) o.remove(); return 'trimmed'; }"],
         "focus": "#status-b22-calmreplay",
         "caption": "Status documents the swap; the twin itself ships hidden.",
         "assert_js": "() => !!document.querySelector('#status-b22-calmreplay')",
         "assert_want": "True"},
        {"type": "title", "duration": 4,
         "kicker": "Groundwork - Batch 22",
         "title": "The trace, simply there.",
         "subtitle": "calmreplay.py twins every stepper -- reduced motion skips the clicks."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Plant a module with a measured-trace lesson (stepper + twin)."""
    con = sqlite3.connect(db_path)
    try:
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        con.execute("DELETE FROM concepts WHERE module_id=?", (MODULE_ID,))
        con.execute("DELETE FROM modules WHERE id=?", (MODULE_ID,))
        lessons = [
            {"concept_id": NODE, "name": "Add Calmly",
             "kind": "function", "file": "demo/calm.py", "line": 1,
             "summary": "Add two numbers, all steps visible.",
             "worked": {"call": "add(2, 3)", "output": "5",
                        "trace": {"var": "total",
                                  "steps": ["1", "3", "5"]}},
             "how": ["Sets total.", "Adds.", "Hands back."],
             "dualcode": {"steps": [], "states": []}},
        ]
        con.execute(
            "INSERT INTO modules(id, repo, task_summary, created_at, lessons)"
            " VALUES(?, ?, ?, ?, ?)",
            (MODULE_ID, "demo/calmreplay", "Calm-reveal module", now,
             json.dumps(lessons)))
        con.execute(
            "INSERT INTO concepts(id, module_id, name, kind, file,"
            " line, mastery) VALUES(?, ?, ?, ?, ?, ?, ?)",
            (CID, MODULE_ID, "Add Calmly", "function",
             "demo/calm.py", 1, 0.0))
        con.commit()
        return {"seeded": True, "mid": MODULE_ID}
    finally:
        con.close()
