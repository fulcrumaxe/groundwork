"""Feature demo: teaching certificates per module pack (F-112).

Full behavior: a certificate issues per module at full owned
coverage, dated by the last concept owned, with a delayed-verified
seal once three weeks pass since issue; partial packs show
progress ("3/5 — 2 to go"). seed_db prunes to one fully-owned
pack with month-old passes so the seal shows.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta, timezone

MODULE_ID = "demo-teachcert-112"
NODE = "demo/cert.py:teachable"
CID = f"{MODULE_ID}:{NODE}"
CARD_ID = f"{MODULE_ID}:ex001"

SCENARIO = {
    "id": "teachcert",
    "kind": "feature",
    "batch": 23,
    "item": "F-112",
    "title": "Teaching certificates",
    "blurb": "Own a whole pack -- proof you could teach it.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 23 - Feature F-112",
         "title": "Teaching certificates",
         "subtitle": "Own the pack, earn the certificate -- sealed after three weeks."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b23-teachcert",
         "caption": "Status documents the rule: full coverage issues, three weeks seal.",
         "assert_js": "() => !!document.querySelector('#status-b23-teachcert')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "One pack, full coverage, month-old passes -- eligible and sealed.",
         "commands": [
             ["python3", "-c",
              "import os; from groundwork import teachcert as m; "
              "db = os.environ['DEMO_DB']; "
              "print('eligible:', [c['pack'] for c in m.eligible(db)]); "
              "c = m.certificates(db)[0]; "
              "print('coverage:', c['owned'], '/', c['total'], "
              "'delayed:', c['delayed'])"],
         ]},
        {"type": "chrome", "duration": 11,
         "url_path": "/reviews",
         "focus": "#teaching-certificates",
         "caption": "History issues the certificate with its delayed-verified seal.",
         "assert_js": "() => document.body.innerText.includes("
                      "'Teaching certificate:') "
                      "&& document.body.innerText.includes('delayed-verified')",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 23",
         "title": "You could teach this.",
         "subtitle": "teachcert.py reads existing tables -- retention proved, not crammed."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Prune to one fully-owned pack with month-old passing reviews."""
    con = sqlite3.connect(db_path)
    try:
        now = datetime.now(timezone.utc)
        old = (now - timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%SZ")
        stamp = now.strftime("%Y-%m-%dT%H:%M:%SZ")
        for table in ("reviews", "cards", "diffvote_votes",
                      "clarity_ratings", "confusing_flags", "known_skips",
                      "concepts", "modules"):
            con.execute(f"DELETE FROM {table}")
        lessons = [
            {"concept_id": NODE, "name": "teachable",
             "kind": "function", "file": "demo/cert.py", "line": 1,
             "summary": "teachable is fully owned and a month proven.",
             "docstring": "Certificate material.",
             "callers": [], "callees": [], "key_lines": "",
             "source": "def teachable():\n    return teach()\n",
             "complexity": 1,
             "how": ["Own every concept.", "Wait three weeks."]},
        ]
        con.execute(
            "INSERT INTO modules(id, repo, task_summary, created_at, lessons)"
            " VALUES(?, ?, ?, ?, ?)",
            (MODULE_ID, "", "Teach-cert module", stamp,
             json.dumps(lessons)))
        con.execute(
            "INSERT INTO concepts(id, module_id, name, kind, file,"
            " line, mastery) VALUES(?, ?, ?, ?, ?, ?, ?)",
            (CID, MODULE_ID, "teachable", "function",
             "demo/cert.py", 1, 0.9))
        con.execute(
            "INSERT INTO cards(id, concept_id, exercise_type, due)"
            " VALUES(?, ?, '27', ?)", (CARD_ID, CID, stamp))
        for _ in range(2):
            con.execute(
                "INSERT INTO reviews(card_id, grade, confidence, reviewed_at,"
                " submission) VALUES(?, 5, 4, ?, 'teachcert seed')",
                (CARD_ID, old))
        con.commit()
        return {"seeded": True, "mid": MODULE_ID}
    finally:
        con.close()
