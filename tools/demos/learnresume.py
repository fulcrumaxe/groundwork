"""Feature demo: learning resume (F-109).

Full behavior: History lists verified Bloom skills per repo — only
owned concepts verify, and passes at 21+ days stability flag
delayed-proof. Portable plain tables, no scripts. seed_db plants an
owned concept whose modify pass came at mature stability.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone

MODULE_ID = "demo-resume-109"
NODE = "demo/resume.py:refactor"
CID = f"{MODULE_ID}:{NODE}"
CARD_ID = "demo-resume-card"

SCENARIO = {
    "id": "learnresume",
    "kind": "feature",
    "batch": 22,
    "item": "F-109",
    "title": "Learning resume",
    "blurb": "Verified skills per repo — references written by your own proof.",
    "beats": [
        {"type": "title", "duration": 4,
         "kicker": "Batch 22 - Feature F-109",
         "title": "Learning resume",
         "subtitle": "Only owned concepts verify -- attempts alone never appear."},
        {"type": "chrome", "duration": 10,
         "url_path": "/reviews",
         "focus": "#learning-resume",
         "caption": "The modify skill verifies with delayed proof from a mature pass.",
         "assert_js": "() => document.body.textContent.includes('delayed-proof') && document.body.textContent.includes('modify')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 8,
         "caption": "Per-repo skills with proof concepts, hold-up flags, and since-dates.",
         "commands": [
             ["python3", "-c",
              "import json, os; from groundwork import learnresume as m; "
              "print('mature bar:', m.MATURE_DAYS, 'days'); "
              "print(json.dumps(m.skills(os.environ.get('DEMO_DB', 'groundwork.db')), indent=1))"],
         ]},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b22-learnresume",
         "caption": "Status documents the verify-only-owned rule.",
         "assert_js": "() => !!document.querySelector('#status-b22-learnresume')",
         "assert_want": "True"},
        {"type": "title", "duration": 4,
         "kicker": "Groundwork - Batch 22",
         "title": "References, self-written.",
         "subtitle": "learnresume.py tables verified skills -- printable, portable."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Plant an owned concept with a mature-stability modify pass."""
    con = sqlite3.connect(db_path)
    try:
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        con.execute("DELETE FROM reviews WHERE card_id=?", (CARD_ID,))
        con.execute("DELETE FROM cards WHERE id=?", (CARD_ID,))
        con.execute("DELETE FROM concepts WHERE module_id=?", (MODULE_ID,))
        con.execute("DELETE FROM modules WHERE id=?", (MODULE_ID,))
        lessons = [
            {"concept_id": NODE, "name": "Refactor",
             "kind": "function", "file": "demo/resume.py", "line": 1,
             "summary": "A refactor held up over delay."},
        ]
        con.execute(
            "INSERT INTO modules(id, repo, task_summary, created_at, lessons)"
            " VALUES(?, ?, ?, ?, ?)",
            (MODULE_ID, "demo/resume", "Learning-resume module", now,
             json.dumps(lessons)))
        con.execute(
            "INSERT INTO concepts(id, module_id, name, kind, file,"
            " line, mastery) VALUES(?, ?, ?, ?, ?, ?, ?)",
            (CID, MODULE_ID, "Refactor", "function",
             "demo/resume.py", 1, 0.0))
        con.execute(
            "INSERT INTO cards(id, concept_id, exercise_type, front, back, due)"
            " VALUES(?, ?, '19', ?, ?, ?)",
            (CARD_ID, CID, "Refactor this?", "Done.",
             "2001-01-01T12:00:00Z"))
        # Two passing modify reviews (owned) — the second at mature
        # stability, so the skill verifies as delayed-proof.
        con.execute(
            "INSERT INTO reviews(card_id, grade, confidence, reviewed_at,"
            " prev_stability, submission) VALUES(?, 5, 4, ?, 0, ?)",
            (CARD_ID, "2026-03-01T09:00:00Z", "learnresume seed"))
        con.execute(
            "INSERT INTO reviews(card_id, grade, confidence, reviewed_at,"
            " prev_stability, submission) VALUES(?, 5, 4, ?, 25, ?)",
            (CARD_ID, "2026-09-20T09:00:00Z", "learnresume seed"))
        con.commit()
        return {"seeded": True, "card_id": CARD_ID}
    finally:
        con.close()
