"""Feature demo: explain-it party trick from the owned list (F-111).

Full behavior: the Due page deals one mastered concept per visit
as a sixty-second explain-it prompt with a study link back to its
lesson; nothing owned yet renders the locked note. seed_db prunes
the library to one owned concept so the pick is deterministic.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone

MODULE_ID = "demo-partytrick-111"
NODE = "demo/trick.py:explain_me"
CID = f"{MODULE_ID}:{NODE}"
CARD_ID = f"{MODULE_ID}:ex001"

SCENARIO = {
    "id": "partytrick",
    "kind": "feature",
    "batch": 23,
    "item": "F-111",
    "title": "Explain-it party trick",
    "blurb": "Quiz yourself from your owned list -- explain one mastered concept aloud.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 23 - Feature F-111",
         "title": "Explain-it party trick",
         "subtitle": "Sixty seconds, one mastered concept, out loud."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b23-partytrick",
         "caption": "Status documents the deal: one owned concept per Due visit.",
         "assert_js": "() => !!document.querySelector('#status-b23-partytrick')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "The pick is a seeded draw over owned concepts -- deterministic under test.",
         "commands": [
             ["python3", "-c",
              "import os; from groundwork import partytrick as m; "
              "c = m.pick(os.environ['DEMO_DB'], seed=7); "
              "print('pick:', c['concept']); "
              "print(m.prompt_for(c['concept'])[:70] + '...')"],
         ]},
        {"type": "chrome", "duration": 11,
         "url_path": "/due",
         "focus": "#partytrick",
         "caption": "The Due page deals the mastered concept with a link back to its lesson.",
         "assert_js": "() => document.body.innerText.includes('Explain it to me:')",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 23",
         "title": "Teach it aloud.",
         "subtitle": "partytrick.py never touches the scheduler -- a pure reorder."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Prune to one owned concept (modify pass plus two attempts)."""
    con = sqlite3.connect(db_path)
    try:
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        for table in ("reviews", "cards", "diffvote_votes",
                      "clarity_ratings", "confusing_flags", "known_skips",
                      "concepts", "modules"):
            con.execute(f"DELETE FROM {table}")
        lessons = [
            {"concept_id": NODE, "name": "explain_me",
             "kind": "function", "file": "demo/trick.py", "line": 1,
             "summary": "explain_me is mastered and ready to perform.",
             "docstring": "Sixty seconds, out loud.",
             "callers": [], "callees": [], "key_lines": "",
             "source": "def explain_me():\n    return teach()\n",
             "complexity": 1,
             "how": ["Own it.", "Explain it aloud."]},
        ]
        con.execute(
            "INSERT INTO modules(id, repo, task_summary, created_at, lessons)"
            " VALUES(?, ?, ?, ?, ?)",
            (MODULE_ID, "", "Party-trick module", now,
             json.dumps(lessons)))
        con.execute(
            "INSERT INTO concepts(id, module_id, name, kind, file,"
            " line, mastery) VALUES(?, ?, ?, ?, ?, ?, ?)",
            (CID, MODULE_ID, "explain_me", "function",
             "demo/trick.py", 1, 0.9))
        con.execute(
            "INSERT INTO cards(id, concept_id, exercise_type, due)"
            " VALUES(?, ?, '27', ?)", (CARD_ID, CID, now))
        for _ in range(2):
            con.execute(
                "INSERT INTO reviews(card_id, grade, confidence, reviewed_at,"
                " submission) VALUES(?, 5, 4, ?, 'partytrick seed')",
                (CARD_ID, now))
        con.commit()
        return {"seeded": True, "mid": MODULE_ID, "cid": CID}
    finally:
        con.close()
