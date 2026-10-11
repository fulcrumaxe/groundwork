"""Improvement demo: try-it-yourself micro-prompts (I-112).

Full behavior: study paragraphs pause for a rotating nudge --
restate, exemplify, predict -- one per eligible prose block,
never after the last, never graded. seed_db plants a three-block
lesson; the module beat counts the two live nudges.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone

MODULE_ID = "demo-b19-tryprompts"
NODE = "demo/try.py:add"

SCENARIO = {
    "id": "tryprompts",
    "kind": "improvement",
    "batch": 19,
    "item": "I-112",
    "title": "Try-it-yourself micro-prompts",
    "blurb": "Study paragraphs pause for a nudge -- restate, exemplify, predict.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 19 - Improvement I-112",
         "title": "Try-it-yourself micro-prompts",
         "subtitle": "One rotating nudge per paragraph -- never graded, never last."},
        {"type": "terminal", "duration": 8,
         "caption": "Three blocks take two prompts; code, recall heads, and the last block take none.",
         "commands": [
             ["python3", "-c",
              "from groundwork import tryprompts as m; "
              "bs = [{'h': 'What it does', 'b': 'Adds.'}, "
              "{'h': 'How it works', 'b': 'Steps.'}, "
              "{'h': 'Recall first', 'b': 'Quiz.'}]; "
              "print(len(m.prompts_for(bs)), 'prompts for 3 blocks; first:', m.prompt_for(0)[:40]); "
              "print('code takes none:', repr(m.block_prompt_html(0, {'h': 'Code', 'b': 'x', 'pre': True})))"],
         ]},
        {"type": "chrome", "duration": 7,
         "url_path": "/status",
         "focus": "#status-b19-tryprompts",
         "caption": "Status carries a live sample: the restate nudge, disclosed.",
         "assert_js": "() => !!document.querySelector('#status-b19-tryprompts') && "
                      "document.body.innerText.includes('Try it yourself')",
         "assert_want": "True"},
        {"type": "chrome", "duration": 10,
         "url_path": "/modules/{seed_module_id}?level=2",
         "focus": "#lesson-{seed_lesson_slug}",
         "caption": "Study blocks pause for rotating nudges -- the last block reads on.",
         "assert_js": "() => document.querySelectorAll('details.tryprompt').length >= 2 && "
                      "document.body.innerText.includes('Try it yourself')",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 19",
         "title": "Pause and try.",
         "subtitle": "tryprompts.py rotates restate, exemplify, predict."},
    ],
}


def _slug(text: str) -> str:
    out = "".join(ch.lower() if ch.isalnum() else "-" for ch in text)
    return "-".join(filter(None, out.split("-"))) or "lesson"


def seed_db(db_path: str) -> dict:
    """Plant one lesson with three prose blocks (summary, docstring, how)."""
    con = sqlite3.connect(db_path)
    try:
        cid = f"{MODULE_ID}:{NODE}"
        con.execute("DELETE FROM cards WHERE concept_id=?", (cid,))
        con.execute("DELETE FROM concepts WHERE id=?", (cid,))
        con.execute("DELETE FROM modules WHERE id=?", (MODULE_ID,))
        lessons = [
            {"concept_id": NODE, "name": "add", "kind": "function",
             "file": "demo/try.py", "line": 1,
             "summary": "add() totals two numbers via its defaults.",
             "docstring": "Add a and b.", "callers": [], "callees": [],
             "key_lines": "",
             "source": "def add(a=2, b=3):\n    total = a + b\n    return total\n",
             "complexity": 1,
             "how": ["Read the two defaults.", "Add them into total.",
                     "Return total to the caller."],
             "worked": None},
        ]
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        con.execute(
            "INSERT INTO modules(id, repo, task_summary, created_at, lessons)"
            " VALUES(?, ?, ?, ?, ?)",
            (MODULE_ID, "demo/b19-try", "Try-prompts module", now,
             json.dumps(lessons)))
        con.execute(
            "INSERT INTO concepts(id, module_id, name, kind, file,"
            " line, mastery) VALUES(?, ?, ?, ?, ?, ?, ?)",
            (cid, MODULE_ID, "add", "function", "demo/try.py", 1, 0.0))
        con.commit()
        return {"seeded": True, "module_id": MODULE_ID,
                "lesson_slug": _slug(NODE)}
    finally:
        con.close()
