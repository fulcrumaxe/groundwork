"""Improvement demo: weekly lesson digest (I-149).

Full behavior: lessons studied in the last seven days whose
before/after version pair differs get one digest row each on
History — module, lesson, changed-line counts, grouped by module
and capped at 25. Quiet weeks render nothing. seed_db plants a
studied lesson with a two-line change.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone

MODULE_ID = "demo-weekdigest-149"
NODE = "demo/digest.py:total"
CID = f"{MODULE_ID}:{NODE}"
CARD_ID = f"{MODULE_ID}:ex001"
BEFORE = "def total(rows):\n    return sum(rows)\n"
AFTER = "def total(rows):\n    return sum(r for r in rows if r)\n"

SCENARIO = {
    "id": "weekdigest",
    "kind": "improvement",
    "batch": 23,
    "item": "I-149",
    "title": "Weekly lesson digest",
    "blurb": "What changed in code you studied this week.",
    "beats": [
        {"type": "title", "duration": 4,
         "kicker": "Batch 23 - Improvement I-149",
         "title": "Weekly lesson digest",
         "subtitle": "Studied it this week and it changed? One row tells you."},
        {"type": "chrome", "duration": 9,
         "url_path": "/reviews",
         "focus": ".weekdigest",
         "caption": "History digests studied lessons whose code changed -- module, lesson, lines.",
         "assert_js": "() => document.body.innerText.includes('2 changed lines')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 8,
         "caption": "Only differing pairs count; identical versions stay out of the digest.",
         "commands": [
             ["python3", "-c",
              "from groundwork import weekdigest as m; "
              "lessons = [{'concept': 'total', 'before': 'a\\nb\\n', "
              "'after': 'a\\nc\\n'}, {'concept': 'same', 'before': 'x', "
              "'after': 'x'}]; "
              "print(m.changed_for(lessons))"],
         ]},
        {"type": "chrome", "duration": 7,
         "url_path": "/status",
         "focus": "#status-b23-weekdigest",
         "caption": "Status documents the window: seven days, grouped by module, capped at 25.",
         "assert_js": "() => !!document.querySelector('#status-b23-weekdigest')",
         "assert_want": "True"},
        {"type": "title", "duration": 4,
         "kicker": "Groundwork - Batch 23",
         "title": "Your code moved.",
         "subtitle": "weekdigest.py reads existing tables -- no schema, quiet weeks silent."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Plant a studied lesson with a two-line before/after change."""
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
            {"concept_id": NODE, "name": "total",
             "kind": "function", "file": "demo/digest.py", "line": 1,
             "summary": "total sums rows, now skipping falsy ones.",
             "docstring": "A two-line change.",
             "callers": [], "callees": [], "key_lines": "",
             "source": AFTER,
             "complexity": 1,
             "before": BEFORE, "after": AFTER,
             "how": ["Sum the rows.", "Skip the falsy ones."]},
        ]
        con.execute(
            "INSERT INTO modules(id, repo, task_summary, created_at, lessons)"
            " VALUES(?, ?, ?, ?, ?)",
            (MODULE_ID, "", "Weekdigest module", now,
             json.dumps(lessons)))
        con.execute(
            "INSERT INTO concepts(id, module_id, name, kind, file,"
            " line, mastery) VALUES(?, ?, ?, ?, ?, ?, ?)",
            (CID, MODULE_ID, "total", "function",
             "demo/digest.py", 1, 0.0))
        con.execute(
            "INSERT INTO cards(id, concept_id, exercise_type, due)"
            " VALUES(?, ?, '1', ?)", (CARD_ID, CID, now))
        con.execute(
            "INSERT INTO reviews(card_id, grade, confidence, reviewed_at,"
            " submission) VALUES(?, 4, 3, ?, 'weekdigest seed')",
            (CARD_ID, now))
        con.commit()
        return {"seeded": True, "mid": MODULE_ID}
    finally:
        con.close()
