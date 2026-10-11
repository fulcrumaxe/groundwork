"""Improvement demo: per-lesson why (I-109).

Full behavior: lessons open with the agent's one-line concept note
-- verbatim, escaped, no invention; noteless lessons render
exactly as before. seed_db plants a lesson carrying a why note;
the module beat reads the Why this matters aside.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone

MODULE_ID = "demo-b19-whyit"
NODE = "demo/why.py:add"
NOTE = "Checkout totals flow through add."

SCENARIO = {
    "id": "whyit",
    "kind": "improvement",
    "batch": 19,
    "item": "I-109",
    "title": "Per-lesson why",
    "blurb": "Lessons open with the agent's one-line note -- verbatim, never invented.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 19 - Improvement I-109",
         "title": "Per-lesson why",
         "subtitle": "The agent's one line, verbatim -- or nothing at all."},
        {"type": "terminal", "duration": 8,
         "caption": "Explicit note wins, stored why_note backs it up, missing renders empty.",
         "commands": [
             ["python3", "-c",
              "from groundwork import whyit as m; "
              "les = {'name': 'add', 'why_note': 'Checkout totals flow through add.'}; "
              "print(repr(m.why_for_lesson(les, 'Filed note wins.'))); "
              "print(repr(m.why_for_lesson(les))); "
              "print('missing renders:', repr(m.lesson_why_html({}))); "
              "print('first carries id:', 'id=' in m.lesson_why_html(les, first=True))"],
         ]},
        {"type": "chrome", "duration": 7,
         "url_path": "/status",
         "focus": "#status-b19-whyit",
         "caption": "Status carries a live sample: checkout totals flow through add.",
         "assert_js": "() => !!document.querySelector('#status-b19-whyit') && "
                      "document.body.innerText.includes('Why this matters')",
         "assert_want": "True"},
        {"type": "chrome", "duration": 10,
         "url_path": "/modules/{seed_module_id}",
         "focus": "#whyit",
         "caption": "The live lesson opens with its why -- the agent's line, quoted.",
         "assert_js": "() => !!document.querySelector('#whyit') && "
                      "document.body.innerText.includes('Checkout totals flow through add')",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 19",
         "title": "Why before what.",
         "subtitle": "whyit.py quotes the note -- no note, no aside."},
    ],
}


def _slug(text: str) -> str:
    out = "".join(ch.lower() if ch.isalnum() else "-" for ch in text)
    return "-".join(filter(None, out.split("-"))) or "lesson"


def seed_db(db_path: str) -> dict:
    """Plant one lesson carrying a why note."""
    con = sqlite3.connect(db_path)
    try:
        cid = f"{MODULE_ID}:{NODE}"
        con.execute("DELETE FROM cards WHERE concept_id=?", (cid,))
        con.execute("DELETE FROM concepts WHERE id=?", (cid,))
        con.execute("DELETE FROM modules WHERE id=?", (MODULE_ID,))
        lessons = [
            {"concept_id": NODE, "name": "add", "kind": "function",
             "file": "demo/why.py", "line": 1,
             "summary": "add() totals two numbers via its defaults.",
             "docstring": "Add a and b.", "callers": [], "callees": [],
             "key_lines": "",
             "source": "def add(a=2, b=3):\n    total = a + b\n    return total\n",
             "complexity": 1, "how": [], "worked": None,
             "why_note": NOTE},
        ]
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        con.execute(
            "INSERT INTO modules(id, repo, task_summary, created_at, lessons)"
            " VALUES(?, ?, ?, ?, ?)",
            (MODULE_ID, "demo/b19-why", "Why module", now,
             json.dumps(lessons)))
        con.execute(
            "INSERT INTO concepts(id, module_id, name, kind, file,"
            " line, mastery) VALUES(?, ?, ?, ?, ?, ?, ?)",
            (cid, MODULE_ID, "add", "function", "demo/why.py", 1, 0.0))
        con.commit()
        return {"seeded": True, "module_id": MODULE_ID,
                "lesson_slug": _slug(NODE)}
    finally:
        con.close()
