"""Improvement demo: lesson version diff (I-116).

Full behavior: a lesson carrying a before/after code pair shows a
capped line-by-line diff table (removed/added rows with old/new line
numbers, +added/-removed counts) banner-adjacent atop the explainer
via lessons.render_levels; lessons without the pair (or with an
identical pair) render byte-identical legacy output. seed_db plants a
module whose lesson carries before with after falling back to source;
the module beat reads the live diff table.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone

MODULE_ID = "demo-b20-lessondiff"
NODE = "demo/ld.py:add"

SCENARIO = {
    "id": "lessondiff",
    "kind": "improvement",
    "batch": 20,
    "item": "I-116",
    "title": "Lesson version diff",
    "blurb": "Lessons with a before/after pair show what changed, line by line.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 20 - Improvement I-116",
         "title": "Lesson version diff",
         "subtitle": "Old versus new code, line by line, atop the lesson."},
        {"type": "terminal", "duration": 8,
         "caption": "One changed line counts one added, one removed; pairless lessons render nothing.",
         "commands": [
             ["python3", "-c",
              "from groundwork import lessondiff as m; "
              "b = 'def add(a, b):\\n    return a - b\\n'; "
              "a = 'def add(a, b):\\n    return a + b\\n'; "
              "print(m.summary_counts(m.diff_ops(b, a))); "
              "print('match renders:', repr(m.diff_html(a, a))); "
              "print('no pair renders:', repr(m.lesson_block({})))"],
         ]},
        {"type": "chrome", "duration": 7,
         "url_path": "/status",
         "focus": "#status-b20-lessondiff",
         "caption": "Status documents the rule with a live before/after sample.",
         "assert_js": "() => !!document.querySelector('#status-b20-lessondiff') && "
                      "document.body.innerText.includes('Changed lines')",
         "assert_want": "True"},
        {"type": "chrome", "duration": 10,
         "url_path": "/modules/{seed_module_id}",
         "focus": "table.lessondiff",
         "caption": "The live lesson shows the version diff: the old line out, the new line in.",
         "assert_js": "() => !!document.querySelector('table.lessondiff') && "
                      "document.body.innerText.includes('Changed lines') && "
                      "document.body.innerText.includes('return a - b') && "
                      "document.body.innerText.includes('return a + b')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 5,
         "caption": "Proof in the fixture DB: the lesson carries before; source is the new side.",
         "commands": [
             ["python3", "-c",
              "import json, os, sqlite3; "
              "con = sqlite3.connect(os.environ.get('DEMO_DB', 'groundwork.db')); "
              "row = con.execute(\"SELECT lessons FROM modules WHERE id='\" + \"demo-b20-lessondiff\" + \"'\").fetchone(); "
              "les = json.loads(row[0])[0]; "
              "print('before:', repr(les.get('before')[-16:])); "
              "print('source:', repr(les.get('source')[-16:]))"],
         ]},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 20",
         "title": "What changed, at a glance.",
         "subtitle": "lessondiff.py renders the pair -- legacy lessons stay byte-identical."},
    ],
}


def _slug(text: str) -> str:
    out = "".join(ch.lower() if ch.isalnum() else "-" for ch in text)
    return "-".join(filter(None, out.split("-"))) or "lesson"


def seed_db(db_path: str) -> dict:
    """Plant one lesson carrying before; after falls back to source."""
    con = sqlite3.connect(db_path)
    try:
        cid = f"{MODULE_ID}:{NODE}"
        con.execute("DELETE FROM cards WHERE concept_id=?", (cid,))
        con.execute("DELETE FROM concepts WHERE id=?", (cid,))
        con.execute("DELETE FROM modules WHERE id=?", (MODULE_ID,))
        lessons = [
            {"concept_id": NODE, "name": "add", "kind": "function",
             "file": "demo/ld.py", "line": 1,
             "summary": "add() totals two numbers via its defaults.",
             "docstring": "Add a and b.", "callers": [], "callees": [],
             "key_lines": "",
             "source": "def add(a, b):\n    return a + b\n",
             "before": "def add(a, b):\n    return a - b\n",
             "complexity": 1, "how": [], "worked": None},
        ]
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        con.execute(
            "INSERT INTO modules(id, repo, task_summary, created_at, lessons)"
            " VALUES(?, ?, ?, ?, ?)",
            (MODULE_ID, "demo/b20-ld", "Version-diff module", now,
             json.dumps(lessons)))
        con.execute(
            "INSERT INTO concepts(id, module_id, name, kind, file,"
            " line, mastery) VALUES(?, ?, ?, ?, ?, ?, ?)",
            (cid, MODULE_ID, "add", "function", "demo/ld.py", 1, 0.0))
        con.commit()
        return {"seeded": True, "module_id": MODULE_ID,
                "lesson_slug": _slug(NODE)}
    finally:
        con.close()
