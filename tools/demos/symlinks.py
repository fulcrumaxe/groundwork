"""Improvement demo: symbol-mention lesson links (I-104).

Full behavior: every symbol a lesson names links to its own lesson
section -- or carries its file line when it has none -- as a
post-pass over finished HTML; unknown names stay plain text.
seed_db plants a two-lesson module whose summaries name each
other; the module beat counts the live symlink anchors.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone

MODULE_ID = "demo-b19-symlinks"
NODES = ["demo/sym.py:add", "demo/sym.py:total"]

SCENARIO = {
    "id": "symlinks",
    "kind": "improvement",
    "batch": 19,
    "item": "I-104",
    "title": "Symbol-mention lesson links",
    "blurb": "Every symbol a lesson names links to its lesson -- or its file line when it has none.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 19 - Improvement I-104",
         "title": "Symbol-mention lesson links",
         "subtitle": "Named symbols link to their lesson -- unknown names stay plain."},
        {"type": "terminal", "duration": 8,
         "caption": "Known mentions link with file-line titles; unknown names pass through untouched.",
         "commands": [
             ["python3", "-c",
              "from groundwork import symlinks as m; "
              "idx = m.build_index([{'name': 'grade', 'module_id': 'm1', 'file': 'calc.py', 'line': 12}], 'm1'); "
              "print(m.link_symbols('grade totals via render_levels', idx, 'm1')); "
              "print('unknown untouched:', m.link_symbols('frobnicate it', idx, 'm1')); "
              "print('empty index legacy:', m.link_symbols('grade it', {}, 'm1'))"],
         ]},
        {"type": "chrome", "duration": 7,
         "url_path": "/status",
         "focus": "#status-b19-symlinks",
         "caption": "Status carries a live sample: two mentions linked, the rule stated.",
         "assert_js": "() => !!document.querySelector('#status-b19-symlinks') && "
                      "document.querySelectorAll('a.symlink').length >= 2",
         "assert_want": "True"},
        {"type": "chrome", "duration": 10,
         "url_path": "/modules/{seed_module_id}?level=2",
         "focus": "#lesson-{seed_add_slug}",
         "caption": "The live lesson: add names total, and total links back to its section.",
         "assert_js": "() => document.querySelectorAll('a.symlink').length >= 1 && "
                      "document.querySelector('a.symlink').title.includes('demo/sym.py')",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 19",
         "title": "Names become doors.",
         "subtitle": "symlinks.py post-passes lesson HTML -- longest names first, capped."},
    ],
}


def _slug(text: str) -> str:
    out = "".join(ch.lower() if ch.isalnum() else "-" for ch in text)
    return "-".join(filter(None, out.split("-"))) or "lesson"


def seed_db(db_path: str) -> dict:
    """Plant two lessons whose summaries name each other's symbol."""
    con = sqlite3.connect(db_path)
    try:
        cids = [f"{MODULE_ID}:{n}" for n in NODES]
        for cid in cids:
            con.execute("DELETE FROM cards WHERE concept_id=?", (cid,))
            con.execute("DELETE FROM concepts WHERE id=?", (cid,))
        con.execute("DELETE FROM modules WHERE id=?", (MODULE_ID,))
        lessons = [
            {"concept_id": NODES[0], "name": "add", "kind": "function",
             "file": "demo/sym.py", "line": 1,
             "summary": "add() totals two numbers for total, the checkout accumulator.",
             "docstring": "Add a and b.", "callers": [], "callees": [],
             "key_lines": "", "source": "def add(a, b):\n    return a + b\n",
             "complexity": 1, "how": [], "worked": None},
            {"concept_id": NODES[1], "name": "total", "kind": "function",
             "file": "demo/sym.py", "line": 5,
             "summary": "total accumulates checkout sums produced by add.",
             "docstring": "Accumulate the total.", "callers": [], "callees": [],
             "key_lines": "", "source": "def total(xs):\n    return sum(xs)\n",
             "complexity": 1, "how": [], "worked": None},
        ]
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        con.execute(
            "INSERT INTO modules(id, repo, task_summary, created_at, lessons)"
            " VALUES(?, ?, ?, ?, ?)",
            (MODULE_ID, "demo/b19-sym", "Symbol links module", now,
             json.dumps(lessons)))
        for node, cid in zip(NODES, cids):
            name = node.rsplit(":", 1)[1]
            con.execute(
                "INSERT INTO concepts(id, module_id, name, kind, file,"
                " line, mastery) VALUES(?, ?, ?, ?, ?, ?, ?)",
                (cid, MODULE_ID, name, "function", "demo/sym.py", 1, 0.0))
        con.commit()
        return {"seeded": True, "module_id": MODULE_ID,
                "add_slug": _slug(NODES[0])}
    finally:
        con.close()
