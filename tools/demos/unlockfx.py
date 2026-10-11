"""Improvement demo: newly-unlocked lesson animation (I-148).

Full behavior: a lesson whose prerequisites are all owned but
which is itself unowned pops with a calm badge reusing the shared
240ms reveal (static under reduced-motion). Freshness derives
purely from current edges + mastery, never history. seed_db plants
a two-lesson chain with the base owned and the next fresh.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone

MODULE_ID = "demo-unlockfx-148"
BASE_NODE = "demo/graph.py:base"
NEXT_NODE = "demo/graph.py:next"
BASE_CID = f"{MODULE_ID}:{BASE_NODE}"
NEXT_CID = f"{MODULE_ID}:{NEXT_NODE}"


def _slug(text: str) -> str:
    out = "".join(ch.lower() if ch.isalnum() else "-" for ch in text)
    return "-".join(filter(None, out.split("-"))) or "lesson"


SCENARIO = {
    "id": "unlockfx",
    "kind": "improvement",
    "batch": 23,
    "item": "I-148",
    "title": "Unlock animation",
    "blurb": "Newly unlocked lessons pop with a calm badge -- still when reduced-motion is set.",
    "beats": [
        {"type": "title", "duration": 4,
         "kicker": "Batch 23 - Improvement I-148",
         "title": "Unlock animation",
         "subtitle": "Fresh lessons pop -- prereqs owned, lesson itself still new."},
        {"type": "chrome", "duration": 9,
         "url_path": "/modules/{seed_mid}",
         "focus": "#lesson-{seed_slug} h2",
         "caption": "The next lesson's prereq is owned, so its heading pops Unlocked.",
         "assert_js": "() => document.body.innerText.includes('Unlocked \\u2014 new')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 8,
         "caption": "Freshness is pure state: prereqs owned plus target unowned.",
         "commands": [
             ["python3", "-c",
              "from groundwork import unlockfx as m; "
              "edges = {'next': ['base'], 'base': []}; "
              "print('fresh:', m.is_fresh('next', edges, {'base'})); "
              "print('owned target:', m.is_fresh('next', edges, {'base', 'next'})); "
              "print('no prereq:', m.is_fresh('base', edges, set()))"],
         ]},
        {"type": "chrome", "duration": 7,
         "url_path": "/status",
         "focus": "#status-b23-unlockfx",
         "caption": "Status documents the reveal: shared 240ms keyframe, still when reduced-motion.",
         "assert_js": "() => !!document.querySelector('#status-b23-unlockfx')",
         "assert_want": "True"},
        {"type": "title", "duration": 4,
         "kicker": "Groundwork - Batch 23",
         "title": "Newly unlocked? It pops.",
         "subtitle": "unlockfx.py derives freshness from edges plus mastery -- never history."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Plant a two-lesson chain: base owned, next fresh."""
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
            {"concept_id": BASE_NODE, "name": "base",
             "kind": "function", "file": "demo/graph.py", "line": 1,
             "summary": "base is the owned prerequisite everything builds on.",
             "docstring": "Owned ground.",
             "callers": [], "callees": [], "key_lines": "",
             "source": "def base():\n    return foundation()\n",
             "complexity": 1,
             "how": ["Own this first."]},
            {"concept_id": NEXT_NODE, "name": "next",
             "kind": "function", "file": "demo/graph.py", "line": 9,
             "summary": "next builds on base and just became available.",
             "docstring": "Freshly unlocked.",
             "callers": [], "callees": [BASE_NODE], "key_lines": "",
             "source": "def next():\n    return base() + 1\n",
             "complexity": 1,
             "how": ["Lean on base.", "Take the next step."]},
        ]
        con.execute(
            "INSERT INTO modules(id, repo, task_summary, created_at, lessons)"
            " VALUES(?, ?, ?, ?, ?)",
            (MODULE_ID, "", "Unlock-fx module", now,
             json.dumps(lessons)))
        con.execute(
            "INSERT INTO concepts(id, module_id, name, kind, file,"
            " line, mastery) VALUES(?, ?, ?, ?, ?, ?, ?)",
            (BASE_CID, MODULE_ID, "base", "function",
             "demo/graph.py", 1, 0.9))
        con.execute(
            "INSERT INTO concepts(id, module_id, name, kind, file,"
            " line, mastery) VALUES(?, ?, ?, ?, ?, ?, ?)",
            (NEXT_CID, MODULE_ID, "next", "function",
             "demo/graph.py", 9, 0.0))
        con.commit()
        return {"seeded": True, "mid": MODULE_ID, "slug": _slug(NEXT_NODE)}
    finally:
        con.close()
