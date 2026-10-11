"""Feature demo: concepts-owned headline (F-102).

Full behavior: History opens with how many concepts the learner can
prove they own (a spaced modify/create pass plus a return visit) —
streaks never appear. seed_db plants one owned concept and one fresh
one so the headline reads "1 concept owned".
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone

MODULE_ID = "demo-own-102"
NODE_OWNED = "demo/own.py:total"
NODE_FRESH = "demo/own.py:sketch"
CID_OWNED = f"{MODULE_ID}:{NODE_OWNED}"
CID_FRESH = f"{MODULE_ID}:{NODE_FRESH}"
CARD_ID = "demo-own-card"

SCENARIO = {
    "id": "ownhead",
    "kind": "feature",
    "batch": 22,
    "item": "F-102",
    "title": "Concepts owned, up top",
    "blurb": "History opens with the concepts you can prove — streaks never counted.",
    "beats": [
        {"type": "title", "duration": 4,
         "kicker": "Batch 22 - Feature F-102",
         "title": "Concepts owned, up top",
         "subtitle": "Owned proof first -- attempt volume can wait below."},
        {"type": "chrome", "duration": 9,
         "url_path": "/reviews",
         "focus": "#owned-headline",
         "caption": "The first thing History says: concepts owned, out of concepts there.",
         "assert_js": "() => document.getElementById('owned-headline').textContent",
         "assert_want": "1 concept owned"},
        {"type": "terminal", "duration": 8,
         "caption": "The owned rule: a modify/create pass plus a return visit.",
         "commands": [
             ["python3", "-c",
              "import os; from groundwork import ownhead as m, ownership as o; "
              "print('modify/create types:', len(o.ownership_types())); "
              "print('counts:', m.counts(os.environ.get('DEMO_DB', 'groundwork.db')))"],
         ]},
        {"type": "chrome", "duration": 7,
         "url_path": "/status",
         "focus": "#status-b22-ownhead",
         "caption": "Status documents the rule; the empty-library sample says 0 with a next step.",
         "assert_js": "() => !!document.querySelector('#status-b22-ownhead')",
         "assert_want": "True"},
        {"type": "title", "duration": 4,
         "kicker": "Groundwork - Batch 22",
         "title": "Proof, not streaks.",
         "subtitle": "ownhead.py counts owned concepts -- History leads with it."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Plant one owned concept (modify pass + revisit) and one fresh."""
    con = sqlite3.connect(db_path)
    try:
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        con.execute("DELETE FROM reviews WHERE card_id=?", (CARD_ID,))
        con.execute("DELETE FROM cards WHERE id=?", (CARD_ID,))
        con.execute("DELETE FROM concepts WHERE module_id=?", (MODULE_ID,))
        con.execute("DELETE FROM modules WHERE id=?", (MODULE_ID,))
        lessons = [
            {"concept_id": NODE_OWNED, "name": "Total",
             "kind": "function", "file": "demo/own.py", "line": 1,
             "summary": "Own this running total."},
            {"concept_id": NODE_FRESH, "name": "Sketch",
             "kind": "function", "file": "demo/own.py", "line": 9,
             "summary": "Not yet attempted."},
        ]
        con.execute(
            "INSERT INTO modules(id, repo, task_summary, created_at, lessons)"
            " VALUES(?, ?, ?, ?, ?)",
            (MODULE_ID, "demo/ownhead", "Owned-headline module", now,
             json.dumps(lessons)))
        for cid, name, line in ((CID_OWNED, "Total", 1),
                                (CID_FRESH, "Sketch", 9)):
            con.execute(
                "INSERT INTO concepts(id, module_id, name, kind, file,"
                " line, mastery) VALUES(?, ?, ?, ?, ?, ?, ?)",
                (cid, MODULE_ID, name, "function", "demo/own.py",
                 line, 0.0))
        con.execute(
            "INSERT INTO cards(id, concept_id, exercise_type, front, back, due)"
            " VALUES(?, ?, '19', ?, ?, ?)",
            (CARD_ID, CID_OWNED, "Refactor this total?", "Done.",
             "2001-01-01T12:00:00Z"))
        for when in ("2026-09-01T09:00:00Z", "2026-09-08T09:00:00Z"):
            con.execute(
                "INSERT INTO reviews(card_id, grade, confidence, reviewed_at,"
                " submission) VALUES(?, 5, 4, ?, 'ownhead seed')",
                (CARD_ID, when))
        con.commit()
        return {"seeded": True, "card_id": CARD_ID, "mid": MODULE_ID}
    finally:
        con.close()
