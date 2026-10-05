"""Feature demo: delayed-retest engine (F-51).

Full behavior: an owned, stable card whose last review sits 8 days
back resurfaces on Due as a flagged probe extra -- the queue never
counts same-day fluency. Terminal beat re-runs the pure engine on
synthetic dicts with a fixed clock.
"""
from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone

MODULE_ID = "demo-retest-51"
CONCEPT_ID = "demo-retest-51:demo/retest.py:recall"
CARD_ID = "demo-retest-51"
FRONT = "Retest probe: state the 7/30-day rule in one line."
BACK = "Owned stable cards resurface once their last review is 7 or 30 days past."

SCENARIO = {
    "id": "retest",
    "kind": "feature",
    "batch": 12,
    "item": "F-51",
    "title": "Delayed retest",
    "blurb": "Owned concepts resurface at 7 and 30 days -- probes, not reviews.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 12 - Feature F-51",
         "title": "Delayed retest",
         "subtitle": "Owned concepts resurface at 7 and 30 days."},
        {"type": "chrome", "duration": 7,
         "url_path": "/status",
         "focus": "#status-b12-retest",
         "caption": "Status homes the engine: owned, stable, past a window, no probe yet.",
         "assert_js": "() => { const el = document.querySelector("
                      "\"#status-b12-retest\"); return !!el && "
                      "document.body.innerText.includes('probes_due'); }",
         "assert_want": "True"},
        {"type": "terminal", "duration": 9,
         "caption": "The rule in one line: ten days owned probes, yesterday does not.",
         "commands": [
             ["python3", "-c",
              "from groundwork import retest as m; "
              "now = '2026-10-05T00:00:00Z'; "
              "old = {'card_id': 'a', 'owned': True, 'stability': 10.0, "
              "'last_review': '2026-09-25T00:00:00Z'}; "
              "fresh = {'card_id': 'b', 'owned': True, 'stability': 10.0, "
              "'last_review': '2026-10-04T00:00:00Z'}; "
              "print('due:', m.probes_due([old, fresh], now)); "
              "print('front:', m.probe_card({\"concept\": \"recall\", "
              "\"window\": 7})['front'])"],
         ]},
        {"type": "chrome", "duration": 10,
         "url_path": "/due",
         "focus": "#card-{seed_card_id}",
         "caption": "The probe rides Due as a flagged extra -- sole card in the queue.",
         "assert_js": "() => document.body.innerText.includes('probe 7d') && "
                      "document.body.innerText.includes('7/30-day rule')",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 12",
         "title": "Fluency never counts.",
         "subtitle": "retest.py probes owned cards -- the queue flags them."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Plant one owned stable card, last reviewed 8 days ago.

    Two passing reviews on an ownership type (12) own the concept;
    every other card is pushed out of the queue so the probe extra
    stands alone on Due.
    """
    con = sqlite3.connect(db_path)
    try:
        now = datetime.now(timezone.utc)
        old = (now - timedelta(days=10)).strftime("%Y-%m-%dT%H:%M:%SZ")
        last = (now - timedelta(days=8)).strftime("%Y-%m-%dT%H:%M:%SZ")
        created = now.strftime("%Y-%m-%dT%H:%M:%SZ")
        con.execute("UPDATE cards SET due='2030-01-01T00:00:00Z'")
        con.execute("DELETE FROM reviews WHERE card_id=?", (CARD_ID,))
        con.execute("DELETE FROM cards WHERE id=?", (CARD_ID,))
        con.execute("DELETE FROM concepts WHERE id=?", (CONCEPT_ID,))
        con.execute("DELETE FROM modules WHERE id=?", (MODULE_ID,))
        con.execute(
            "INSERT INTO modules(id, repo, task_summary, created_at)"
            " VALUES(?, ?, ?, ?)",
            (MODULE_ID, "demo/retest", "Retest probe module", created))
        con.execute(
            "INSERT INTO concepts(id, module_id, name, kind)"
            " VALUES(?, ?, ?, ?)",
            (CONCEPT_ID, MODULE_ID, "recall", "function"))
        con.execute(
            "INSERT INTO cards(id, concept_id, exercise_type, front, back,"
            " payload, stability, due, stale, last_probe)"
            " VALUES(?, ?, '12', ?, ?, '{}', 10.0,"
            " '2030-01-01T00:00:00Z', 0, NULL)",
            (CARD_ID, CONCEPT_ID, FRONT, BACK))
        con.execute(
            "INSERT INTO reviews(card_id, grade, confidence, reviewed_at)"
            " VALUES(?, 5, 5, ?)", (CARD_ID, old))
        con.execute(
            "INSERT INTO reviews(card_id, grade, confidence, reviewed_at)"
            " VALUES(?, 4, 4, ?)", (CARD_ID, last))
        con.commit()
        return {"seeded": True, "card_id": CARD_ID}
    finally:
        con.close()
