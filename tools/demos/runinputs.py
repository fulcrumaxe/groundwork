"""Improvement demo: run-your-own-inputs (I-106).

Full behavior: every worked example grows editable inputs -- change
the arguments, see your call rebuilt in-page, try neighbor
variants in your own REPL. seed_db plants a worked lesson; the
module beat edits an argument and watches the call rebuild.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone

MODULE_ID = "demo-b19-runinputs"
NODE = "demo/own.py:add"

SCENARIO = {
    "id": "runinputs",
    "kind": "improvement",
    "batch": 19,
    "item": "I-106",
    "title": "Run-your-own-inputs",
    "blurb": "Change the worked example's arguments -- your call rebuilds in-page.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 19 - Improvement I-106",
         "title": "Run-your-own-inputs",
         "subtitle": "Editable arguments, a rebuilt call, neighbor variants to try."},
        {"type": "terminal", "duration": 8,
         "caption": "The stored call parses to a function plus args; neighbor variants suggest themselves.",
         "commands": [
             ["python3", "-c",
              "from groundwork import runinputs as m; "
              "print(m.parse_call('add(2, 3)')); "
              "print(m.suggest_variants('add', ['2', '3'])); "
              "print('unusable call renders:', repr(m.runinputs_html({})))"],
         ]},
        {"type": "chrome", "duration": 7,
         "url_path": "/status",
         "focus": "#status-b19-runinputs",
         "caption": "Status carries a live sample: measured call, editable fields, variants.",
         "assert_js": "() => !!document.querySelector('#status-b19-runinputs') && "
                      "!!document.querySelector('#runinputs')",
         "assert_want": "True"},
        {"type": "chrome", "duration": 10,
         "url_path": "/modules/{seed_module_id}",
         "focus": "#runinputs",
         "caption": "Editing the first argument rebuilds the call in-page -- try it in your REPL.",
         "js": ["() => { const d = document.querySelector('#runinputs'); "
               "if (!d) return 'missing'; "
               "const f = d.querySelector('.ri-field'); "
               "f.value = '9'; f.dispatchEvent(new Event('input', {bubbles: true})); "
               "return 'set'; }"],
         "assert_js": "() => document.querySelector('.ri-out').textContent.includes('add(9, 3)')",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 19",
         "title": "Your inputs, your call.",
         "subtitle": "runinputs.py parses the stored call -- edits persist per call."},
    ],
}


def _slug(text: str) -> str:
    out = "".join(ch.lower() if ch.isalnum() else "-" for ch in text)
    return "-".join(filter(None, out.split("-"))) or "lesson"


def seed_db(db_path: str) -> dict:
    """Plant one lesson with a usable worked call."""
    con = sqlite3.connect(db_path)
    try:
        cid = f"{MODULE_ID}:{NODE}"
        con.execute("DELETE FROM cards WHERE concept_id=?", (cid,))
        con.execute("DELETE FROM concepts WHERE id=?", (cid,))
        con.execute("DELETE FROM modules WHERE id=?", (MODULE_ID,))
        lessons = [
            {"concept_id": NODE, "name": "add", "kind": "function",
             "file": "demo/own.py", "line": 1,
             "summary": "add() totals two numbers via its defaults.",
             "docstring": "Add a and b.", "callers": [], "callees": [],
             "key_lines": "",
             "source": "def add(a=2, b=3):\n    total = a + b\n    return total\n",
             "complexity": 1, "how": ["Read the two defaults.",
                                      "Add them into total.",
                                      "Return total to the caller."],
             "worked": {"call": "add(2, 3)", "output": "5"}},
        ]
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        con.execute(
            "INSERT INTO modules(id, repo, task_summary, created_at, lessons)"
            " VALUES(?, ?, ?, ?, ?)",
            (MODULE_ID, "demo/b19-own", "Own-inputs module", now,
             json.dumps(lessons)))
        con.execute(
            "INSERT INTO concepts(id, module_id, name, kind, file,"
            " line, mastery) VALUES(?, ?, ?, ?, ?, ?, ?)",
            (cid, MODULE_ID, "add", "function", "demo/own.py", 1, 0.0))
        con.commit()
        return {"seeded": True, "module_id": MODULE_ID,
                "lesson_slug": _slug(NODE)}
    finally:
        con.close()
