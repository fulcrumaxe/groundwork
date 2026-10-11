"""Improvement demo: before/after diff (I-107).

Full behavior: each lesson shows what the agent changed --
added/removed counts with the capped unified diff one click away;
lessons without the pair render exactly as before. seed_db plants
a lesson carrying before/after; the module beat reads the counts.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone

MODULE_ID = "demo-b19-beforafter"
NODE = "demo/ba.py:limit"

SCENARIO = {
    "id": "beforafter",
    "kind": "improvement",
    "batch": 19,
    "item": "I-107",
    "title": "Before/after diff",
    "blurb": "Each lesson shows what the agent changed -- counts plus the diff one click away.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 19 - Improvement I-107",
         "title": "Before/after diff",
         "subtitle": "Added/removed counts -- the capped diff one click away."},
        {"type": "terminal", "duration": 8,
         "caption": "One line changed counts one added, one removed; a pairless lesson renders nothing.",
         "commands": [
             ["python3", "-c",
              "from groundwork import beforafter as m; "
              "print(m.diff_stats('x = 1\\n', 'x = 2\\n')); "
              "print(m.unified_diff('x = 1\\n', 'x = 2\\n')); "
              "print('no pair renders:', repr(m.lesson_block({})))"],
         ]},
        {"type": "chrome", "duration": 7,
         "url_path": "/status",
         "focus": "#status-b19-beforafter",
         "caption": "Status carries a live sample: one added, one removed, diff disclosed.",
         "assert_js": "() => !!document.querySelector('#status-b19-beforafter') && "
                      "document.body.innerText.includes('1 added, 1 removed')",
         "assert_want": "True"},
        {"type": "chrome", "duration": 10,
         "url_path": "/modules/{seed_module_id}",
         "focus": "#beforafter",
         "caption": "The live lesson names its change: one added, one removed by the agent.",
         "assert_js": "() => !!document.querySelector('#beforafter') && "
                      "document.body.innerText.includes('Show what changed')",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 19",
         "title": "See what changed.",
         "subtitle": "beforafter.py reads before/after -- after falls back to source."},
    ],
}


def _slug(text: str) -> str:
    out = "".join(ch.lower() if ch.isalnum() else "-" for ch in text)
    return "-".join(filter(None, out.split("-"))) or "lesson"


def seed_db(db_path: str) -> dict:
    """Plant one lesson carrying a before/after pair."""
    con = sqlite3.connect(db_path)
    try:
        cid = f"{MODULE_ID}:{NODE}"
        con.execute("DELETE FROM cards WHERE concept_id=?", (cid,))
        con.execute("DELETE FROM concepts WHERE id=?", (cid,))
        con.execute("DELETE FROM modules WHERE id=?", (MODULE_ID,))
        lessons = [
            {"concept_id": NODE, "name": "limit", "kind": "function",
             "file": "demo/ba.py", "line": 1,
             "summary": "limit() caps the queue length at two.",
             "docstring": "Cap the queue.", "callers": [], "callees": [],
             "key_lines": "",
             "source": "def limit(xs):\n    return xs[:2]\n",
             "before": "def limit(xs):\n    return xs[:1]\n",
             "after": "def limit(xs):\n    return xs[:2]\n",
             "complexity": 1, "how": [], "worked": None},
        ]
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        con.execute(
            "INSERT INTO modules(id, repo, task_summary, created_at, lessons)"
            " VALUES(?, ?, ?, ?, ?)",
            (MODULE_ID, "demo/b19-ba", "Before-after module", now,
             json.dumps(lessons)))
        con.execute(
            "INSERT INTO concepts(id, module_id, name, kind, file,"
            " line, mastery) VALUES(?, ?, ?, ?, ?, ?, ?)",
            (cid, MODULE_ID, "limit", "function", "demo/ba.py", 1, 0.0))
        con.commit()
        return {"seeded": True, "module_id": MODULE_ID,
                "lesson_slug": _slug(NODE)}
    finally:
        con.close()
