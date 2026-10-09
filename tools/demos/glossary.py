"""Improvement demo: inline glossary tooltips (I-103).

Full behavior: known jargon in leveled explainers wraps in
<dfn class='gloss'> tooltips on the lesson rendering path (at most
12 per fragment); unknown words pass through untouched and the
markup degrades to plain text without CSS. seed_db plants a
jargon-rich add() lesson; the module beat films live tooltips.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone

MODULE_ID = "demo-b18-gloss"

LESSON = {"concept_id": "add", "name": "add", "kind": "function",
          "file": "calc.py", "line": 1,
          "summary": "A function that takes an argument, runs a loop, and returns the total to the caller.",
          "docstring": "Add every value the caller passes in.",
          "callers": [], "callees": [], "key_lines": "",
          "source": "def add(a, b):\n    return a + b\n",
          "how": ["take the first argument", "store it in a variable",
                  "return the sum to the caller"],
          "worked": {"call": "add(2, 3)", "output": "5",
                     "trace": {"var": "total", "steps": [2, 5]}},
          "dualcode": {"steps": [], "states": []}}

SCENARIO = {
    "id": "glossary",
    "kind": "improvement",
    "batch": 18,
    "item": "I-103",
    "title": "Inline glossary tooltips",
    "blurb": "Jargon in leveled explainers defines itself on hover -- no lookup, no lost place.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 18 - Improvement I-103",
         "title": "Inline glossary tooltips",
         "subtitle": "Jargon defines itself in place -- hover a term, keep your place."},
        {"type": "terminal", "duration": 8,
         "caption": "The wrap in one call: known terms gain tooltips, unknown words pass through.",
         "commands": [
             ["python3", "-c",
              "from groundwork import glossary as m; "
              "print(m.term_def('function')); "
              "print(m.term_def('frobnicate')); "
              "print(m.gloss_html('The function takes an argument.'))"],
         ]},
        {"type": "terminal", "duration": 6,
         "caption": "Budgeted and safe: at most 12 tooltips, hostile input never raises.",
         "commands": [
             ["python3", "-c",
              "from groundwork import glossary as m; "
              "many = ' '.join(['function'] * 20); "
              "print('capped at:', m.gloss_html(many).count(\"class='gloss'\"), '/', m.MAX_TOOLTIPS); "
              "print('hostile:', repr(m.gloss_html(None)), repr(m.annotate_html(42)))"],
         ]},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b18-glossary",
         "caption": "Status renders a live sample: recursion, function, call, arguments annotated.",
         "assert_js": "() => !!document.querySelector('#status-b18-glossary')",
         "assert_want": "True"},
        {"type": "chrome", "duration": 10,
         "url_path": "/modules/{seed_module_id}?level=2",
         "focus": "#lesson-add h4",
         "caption": "The live lesson: jargon wrapped in tooltips on the rendering path.",
         "assert_js": "() => { const els = document.querySelectorAll('dfn.gloss'); "
                      "return els.length >= 3 && "
                      "document.body.innerHTML.includes('tabindex'); }",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 18",
         "title": "No lookup, no lost place.",
         "subtitle": "glossary.py annotates the lesson path -- plain text when styles are off."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Plant a one-lesson module whose summary and steps are jargon-rich."""
    con = sqlite3.connect(db_path)
    try:
        cid = f"{MODULE_ID}:add"
        con.execute("DELETE FROM cards WHERE concept_id=?", (cid,))
        con.execute("DELETE FROM concepts WHERE id=?", (cid,))
        con.execute("DELETE FROM modules WHERE id=?", (MODULE_ID,))
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        con.execute(
            "INSERT INTO modules(id, repo, task_summary, created_at, lessons)"
            " VALUES(?, ?, ?, ?, ?)",
            (MODULE_ID, "demo/b18-gloss", "Glossary module", now,
             json.dumps([LESSON])))
        con.execute(
            "INSERT INTO concepts(id, module_id, name, kind, file,"
            " line, mastery) VALUES(?, ?, ?, ?, ?, ?, ?)",
            (cid, MODULE_ID, "add", "function", "calc.py", 1, 0.0))
        con.commit()
        return {"seeded": True, "module_id": MODULE_ID}
    finally:
        con.close()
