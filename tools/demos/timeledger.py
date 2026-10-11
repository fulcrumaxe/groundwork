"""Feature demo: time ledger (F-105).

Full behavior: History totals capped daily active spans (last review
minus first review per day, 6h cap) and divides by owned concepts
for a minutes-per-concept ROI. seed_db plants two practice days with
real spans plus the owned concept that prices them.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone

MODULE_ID = "demo-ledger-105"
NODE = "demo/ledger.py:shift"
CID = f"{MODULE_ID}:{NODE}"
CARD_ID = "demo-ledger-card"
# Day 1: 45 minutes; day 2: 120 minutes; total 165 -> "2h 45m".
SPANS = (("2026-03-02T09:00:00Z", "2026-03-02T09:45:00Z"),
         ("2026-03-03T10:00:00Z", "2026-03-03T12:00:00Z"))

SCENARIO = {
    "id": "timeledger",
    "kind": "feature",
    "batch": 22,
    "item": "F-105",
    "title": "Time ledger",
    "blurb": "Invested hours against concepts owned — the honest ROI of practice.",
    "beats": [
        {"type": "title", "duration": 4,
         "kicker": "Batch 22 - Feature F-105",
         "title": "Time ledger",
         "subtitle": "Hours in, owned concepts out -- capped daily, honestly divided."},
        {"type": "chrome", "duration": 9,
         "url_path": "/reviews",
         "focus": "#time-ledger",
         "caption": "2h 45m of practice prices one owned concept, ROI included.",
         "assert_js": "() => document.body.textContent.includes('2h 45m')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 8,
         "caption": "Per-day spans, capped so an open tab never invents a marathon.",
         "commands": [
             ["python3", "-c",
              "import os; from groundwork import timeledger as m; "
              "db = os.environ.get('DEMO_DB', 'groundwork.db'); "
              "print('cap/day:', m.DAY_CAP_MINUTES, 'min'); "
              "print('ledger:', m.ledger(db)); "
              "print('seeded days:', [(d, round(x, 1)) for d, x in m.daily_spans(db) if d.startswith('2026-03')])"],
         ]},
        {"type": "chrome", "duration": 7,
         "url_path": "/status",
         "focus": "#status-b22-timeledger",
         "caption": "Status documents the ledger rule: spans in, ROI out.",
         "assert_js": "() => !!document.querySelector('#status-b22-timeledger')",
         "assert_want": "True"},
        {"type": "title", "duration": 4,
         "kicker": "Groundwork - Batch 22",
         "title": "Books that balance.",
         "subtitle": "timeledger.py prices proof in minutes -- quiet weeks stay quiet."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Plant two spanned days of passing modify reviews (one owned)."""
    con = sqlite3.connect(db_path)
    try:
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        con.execute("DELETE FROM reviews WHERE card_id=?", (CARD_ID,))
        con.execute("DELETE FROM cards WHERE id=?", (CARD_ID,))
        con.execute("DELETE FROM concepts WHERE module_id=?", (MODULE_ID,))
        con.execute("DELETE FROM modules WHERE id=?", (MODULE_ID,))
        lessons = [
            {"concept_id": NODE, "name": "Shift",
             "kind": "function", "file": "demo/ledger.py", "line": 1,
             "summary": "Two shifts of honest practice."},
        ]
        con.execute(
            "INSERT INTO modules(id, repo, task_summary, created_at, lessons)"
            " VALUES(?, ?, ?, ?, ?)",
            (MODULE_ID, "demo/timeledger", "Time-ledger module", now,
             json.dumps(lessons)))
        con.execute(
            "INSERT INTO concepts(id, module_id, name, kind, file,"
            " line, mastery) VALUES(?, ?, ?, ?, ?, ?, ?)",
            (CID, MODULE_ID, "Shift", "function",
             "demo/ledger.py", 1, 0.0))
        con.execute(
            "INSERT INTO cards(id, concept_id, exercise_type, front, back, due)"
            " VALUES(?, ?, '19', ?, ?, ?)",
            (CARD_ID, CID, "Refactor this shift?", "Done.",
             "2001-01-01T12:00:00Z"))
        for lo, hi in SPANS:
            for when in (lo, hi):
                con.execute(
                    "INSERT INTO reviews(card_id, grade, confidence,"
                    " reviewed_at, submission) VALUES(?, 5, 4, ?, ?)",
                    (CARD_ID, when, "timeledger seed"))
        con.commit()
        return {"seeded": True, "card_id": CARD_ID, "minutes": 165.0}
    finally:
        con.close()
