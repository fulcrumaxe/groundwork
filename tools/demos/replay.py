"""Improvement demo: worked-example replay (I-105).

Full behavior: long measured traces replay one step at a time --
prev/next links, a step counter, the measured state at each step;
traceless lessons keep the legacy full pack. seed_db plants a
three-step traced lesson; the module beats walk steps one and two.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone

MODULE_ID = "demo-b19-replay"
NODE = "demo/replay.py:add"
HOW = ["Sets total to the first input.", "Adds the second input.",
       "Hands the sum back to the caller."]
STEPS = ["total = 2", "total = 5", "return 5"]

SCENARIO = {
    "id": "replay",
    "kind": "improvement",
    "batch": 19,
    "item": "I-105",
    "title": "Worked-example replay",
    "blurb": "Step through the measured trace one step at a time -- prev/next with state.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 19 - Improvement I-105",
         "title": "Worked-example replay",
         "subtitle": "One step at a time -- the measured state at each step."},
        {"type": "terminal", "duration": 7,
         "caption": "Three measured steps slice cleanly; a traceless lesson keeps the full pack.",
         "commands": [
             ["python3", "-c",
              "from groundwork import replay as m; "
              "les = {'worked': {'trace': {'steps': ['total = 2', 'total = 5', 'return 5']}}, "
              "'how': ['Sets it.', 'Adds.', 'Hands back.']}; "
              "print(len(m.replay_steps(les)), 'steps; clamp 9 ->', m.clamp_step(les, 9)); "
              "print('no trace, no replay:', repr(m.replay_html({}, 1, '')))"],
         ]},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b19-replay",
         "caption": "Status carries a live sample: step two of three, state shown.",
         "assert_js": "() => !!document.querySelector('#status-b19-replay') && "
                      "document.body.innerText.includes('Step 2 of 3')",
         "assert_want": "True"},
        {"type": "chrome", "duration": 9,
         "url_path": "/modules/{seed_module_id}",
         "focus": "#replay",
         "caption": "Step one of three on the live lesson -- state, counter, next link.",
         "assert_js": "() => !!document.querySelector('#replay') && "
                      "document.body.innerText.includes('Step 1 of 3')",
         "assert_want": "True"},
        {"type": "chrome", "duration": 8,
         "url_path": "/modules/{seed_module_id}?replay=2",
         "focus": "#replay",
         "caption": "Step two: prev appears, the state advances, one step still ahead.",
         "assert_js": "() => document.body.innerText.includes('Step 2 of 3') && "
                      "document.body.innerText.includes('total = 5')",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 19",
         "title": "Traces, stepped.",
         "subtitle": "replay.py slices the stored trace -- measured, never invented."},
    ],
}


def _slug(text: str) -> str:
    out = "".join(ch.lower() if ch.isalnum() else "-" for ch in text)
    return "-".join(filter(None, out.split("-"))) or "lesson"


def seed_db(db_path: str) -> dict:
    """Plant one lesson with a three-step measured trace."""
    con = sqlite3.connect(db_path)
    try:
        cid = f"{MODULE_ID}:{NODE}"
        con.execute("DELETE FROM cards WHERE concept_id=?", (cid,))
        con.execute("DELETE FROM concepts WHERE id=?", (cid,))
        con.execute("DELETE FROM modules WHERE id=?", (MODULE_ID,))
        lessons = [
            {"concept_id": NODE, "name": "add", "kind": "function",
             "file": "demo/replay.py", "line": 1,
             "summary": "add() totals two numbers via its defaults.",
             "docstring": "Add a and b.", "callers": [], "callees": [],
             "key_lines": "",
             "source": "def add(a=2, b=3):\n    total = a + b\n    return total\n",
             "complexity": 1, "how": list(HOW),
             "worked": {"call": "add(2, 3)", "output": "5",
                        "trace": {"var": "total", "steps": list(STEPS)}},
             "dualcode": {"steps": list(HOW), "states": []}},
        ]
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        con.execute(
            "INSERT INTO modules(id, repo, task_summary, created_at, lessons)"
            " VALUES(?, ?, ?, ?, ?)",
            (MODULE_ID, "demo/b19-replay", "Replay module", now,
             json.dumps(lessons)))
        con.execute(
            "INSERT INTO concepts(id, module_id, name, kind, file,"
            " line, mastery) VALUES(?, ?, ?, ?, ?, ?, ?)",
            (cid, MODULE_ID, "add", "function", "demo/replay.py", 1, 0.0))
        con.commit()
        return {"seeded": True, "module_id": MODULE_ID,
                "lesson_slug": _slug(NODE)}
    finally:
        con.close()
