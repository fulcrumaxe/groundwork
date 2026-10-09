"""Improvement demo: explain-it-differently order toggle (I-102).

Full behavior: ?order=examples renders the same lesson blocks
example-first (Worked example jumps ahead of How it works) while the
default keeps legacy definition-first bytes; the toggle preserves
the level and both orders carry identical content. seed_db plants a
worked add() lesson; the module beats film both orders live.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone

MODULE_ID = "demo-b18-flip"

LESSON = {"concept_id": "add", "name": "add", "kind": "function",
          "file": "calc.py", "line": 1,
          "summary": "Adds two numbers together.",
          "docstring": "Return the sum of a and b.",
          "callers": [], "callees": [], "key_lines": "",
          "source": "def add(a, b):\n    return a + b\n",
          "how": ["take a", "take b", "return total"],
          "worked": {"call": "add(2, 3)", "output": "5",
                     "trace": {"var": "total", "steps": [2, 5]}},
          "dualcode": {"steps": [], "states": []}}

SCENARIO = {
    "id": "explainflip",
    "kind": "improvement",
    "batch": 18,
    "item": "I-102",
    "title": "Explain it differently",
    "blurb": "Flip any lesson example-first or definition-first -- same content, the order that clicks.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 18 - Improvement I-102",
         "title": "Explain it differently",
         "subtitle": "One lesson, two orders -- definition-first or example-first, same content."},
        {"type": "terminal", "duration": 7,
         "caption": "The reorder in one call: example blocks front, order kept, recall probe pinned.",
         "commands": [
             ["python3", "-c",
              "from groundwork import explainflip as m; "
              "d = [{'h': 'What it does', 'b': 'x'}, {'h': 'Worked example', 'b': 'y'}]; "
              "print('default:', [b['h'] for b in m.reorder_blocks(d, 'definition')]); "
              "print('flipped:', [b['h'] for b in m.reorder_blocks(d, 'examples')]); "
              "print('unknown order falls back:', m.normalize_order('sideways'))"],
         ]},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b18-explainflip",
         "caption": "Status carries a live both-orders demo of the same two blocks.",
         "assert_js": "() => !!document.querySelector('#status-b18-explainflip')",
         "assert_want": "True"},
        {"type": "chrome", "duration": 8,
         "url_path": "/modules/{seed_module_id}?level=2",
         "focus": "#lesson-add h4",
         "caption": "Default order on the live lesson: definition first, the example after the steps.",
         "assert_js": "() => { const hs = Array.from(document.querySelectorAll('h5'))"
                      ".map(h => h.textContent); "
                      "return hs.indexOf('How it works') > -1 && "
                      "hs.indexOf('Worked example') > hs.indexOf('How it works'); }",
         "assert_want": "True"},
        {"type": "chrome", "duration": 9,
         "url_path": "/modules/{seed_module_id}?level=2&order=examples",
         "focus": "#lesson-add h4",
         "caption": "Flipped: the same blocks, the example now ahead of the steps.",
         "assert_js": "() => { const hs = Array.from(document.querySelectorAll('h5'))"
                      ".map(h => h.textContent); "
                      "return hs.indexOf('How it works') > -1 && "
                      "hs.indexOf('Worked example') < hs.indexOf('How it works'); }",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 18",
         "title": "The order that clicks.",
         "subtitle": "explainflip.py reorders at render time -- no second copy, level preserved."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Plant a one-lesson module with summary, how-steps, and a worked run."""
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
            (MODULE_ID, "demo/b18-flip", "Order-toggle module", now,
             json.dumps([LESSON])))
        con.execute(
            "INSERT INTO concepts(id, module_id, name, kind, file,"
            " line, mastery) VALUES(?, ?, ?, ?, ?, ?, ?)",
            (cid, MODULE_ID, "add", "function", "calc.py", 1, 0.0))
        con.commit()
        return {"seeded": True, "module_id": MODULE_ID}
    finally:
        con.close()
