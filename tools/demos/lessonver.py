"""Improvement demo: lesson version banner (I-115).

Full behavior: lessons carry an updated-for-commit banner -- the
lesson commit, or the module range's last hash -- plus a moved-on
comparison when HEAD differs; same commits render nothing.
seed_db plants a ranged module; the module beat reads the banner.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone

MODULE_ID = "demo-b19-lessonver"
NODE = "demo/ver.py:add"
COMMIT = "abc1234"

SCENARIO = {
    "id": "lessonver",
    "kind": "improvement",
    "batch": 19,
    "item": "I-115",
    "title": "Lesson version banner",
    "blurb": "Lessons say which commit they were updated for -- and when code moved on.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 19 - Improvement I-115",
         "title": "Lesson version banner",
         "subtitle": "Updated for commit X -- and whether code has moved on since."},
        {"type": "terminal", "duration": 8,
         "caption": "Unknown HEAD states the commit; a newer HEAD adds moved-on; same HEAD stays silent.",
         "commands": [
             ["python3", "-c",
              "from groundwork import lessonver as m; "
              "print(m.banner_html('abc1234', '')); "
              "print(m.banner_html('abc1234', 'def5678')); "
              "print('same renders:', repr(m.banner_html('abc1234', 'abc1234'))); "
              "print('range last wins:', m.lesson_commit_of({}, 'aaa1111,abc1234'))"],
         ]},
        {"type": "chrome", "duration": 7,
         "url_path": "/status",
         "focus": "#status-b19-lessonver",
         "caption": "Status states the rule: lesson commit first, range hash next, moved-on noted.",
         "assert_js": "() => !!document.querySelector('#status-b19-lessonver')",
         "assert_want": "True"},
        {"type": "chrome", "duration": 10,
         "url_path": "/modules/{seed_module_id}",
         "focus": ".lessonver",
         "caption": "The live lesson is stamped: updated for commit abc1234.",
         "assert_js": "() => !!document.querySelector('.lessonver') && "
                      "document.body.innerText.includes('Updated for commit') && "
                      "document.body.innerText.includes('abc1234')",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 19",
         "title": "Stamped with proof.",
         "subtitle": "lessonver.py normalizes hashes -- same commit renders legacy."},
    ],
}


def _slug(text: str) -> str:
    out = "".join(ch.lower() if ch.isalnum() else "-" for ch in text)
    return "-".join(filter(None, out.split("-"))) or "lesson"


def seed_db(db_path: str) -> dict:
    """Plant a ranged module with one unstamped lesson."""
    con = sqlite3.connect(db_path)
    try:
        cid = f"{MODULE_ID}:{NODE}"
        con.execute("DELETE FROM cards WHERE concept_id=?", (cid,))
        con.execute("DELETE FROM concepts WHERE id=?", (cid,))
        con.execute("DELETE FROM modules WHERE id=?", (MODULE_ID,))
        lessons = [
            {"concept_id": NODE, "name": "add", "kind": "function",
             "file": "demo/ver.py", "line": 1,
             "summary": "add() totals two numbers via its defaults.",
             "docstring": "Add a and b.", "callers": [], "callees": [],
             "key_lines": "",
             "source": "def add(a=2, b=3):\n    total = a + b\n    return total\n",
             "complexity": 1, "how": [], "worked": None},
        ]
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        con.execute(
            "INSERT INTO modules(id, repo, task_summary, created_at, lessons,"
            " commit_range) VALUES(?, ?, ?, ?, ?, ?)",
            (MODULE_ID, "demo/b19-ver", "Version module", now,
             json.dumps(lessons), COMMIT))
        con.execute(
            "INSERT INTO concepts(id, module_id, name, kind, file,"
            " line, mastery) VALUES(?, ?, ?, ?, ?, ?, ?)",
            (cid, MODULE_ID, "add", "function", "demo/ver.py", 1, 0.0))
        con.commit()
        return {"seeded": True, "module_id": MODULE_ID,
                "lesson_slug": _slug(NODE)}
    finally:
        con.close()
