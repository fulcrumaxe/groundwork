"""Feature demo: probe lifecycle -- listed, answered, stamped (F-51 integration).

Full behavior: an owned, stable card whose last review sits 8 days
back rides Due as a flagged probe extra; answering it stamps
cards.last_probe, and the card re-lists as plain due -- never
probe-flagged twice. seed_db plants one owned stable type-24 card
and parks every other card out of the queue.
"""
from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone

MODULE_ID = "demo-probelife-51"
CONCEPT_ID = "demo-probelife-51:demo/probelife.py:recall"
CARD_ID = "demo-probelife-51"
FRONT = "Probe lifecycle: answer this 8-day-old owned card."
BACK = "Answering stamps last_probe; the card re-lists as plain due."
WRONG_ANSWER = "xylophone zebra quasar xyzzy"

SCENARIO = {
    "id": "probelife",
    "kind": "feature",
    "batch": 15,
    "item": "F-51",
    "title": "Probes live once",
    "blurb": "Owned cards resurface flagged -- answered once, stamped, never flagged twice.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 15 - Feature F-51",
         "title": "Probes live once",
         "subtitle": "Owned cards resurface flagged -- answered once, stamped."},
        {"type": "terminal", "duration": 7,
         "caption": "The queue in one call: the owned card rides along flagged probe=7.",
         "commands": [
             ["python3", "-c",
              "import os; from groundwork.mcp import MCPServer; "
              "due = MCPServer(os.environ['DEMO_DB']).tool_list_due_reviews({'limit': 20})['due']; "
              "hit = [c for c in due if c['id'] == '" + CARD_ID + "']; "
              "print('queue:', len(due), '| probe hits:', len(hit), "
              "'| flag:', hit[0].get('probe') if hit else None)"],
         ]},
        {"type": "chrome", "duration": 9,
         "url_path": "/due",
         "focus": "#card-" + CARD_ID,
         "caption": "Due shows the flagged extra alone -- the probe 7d chip, front and center.",
         "assert_js": "() => document.body.innerText.includes('probe 7d') && "
                      "document.body.innerText.includes('8-day-old owned card')",
         "assert_want": "True"},
        {"type": "chrome", "duration": 13,
         "url_path": "/due",
         "caption": "Answer the probe -- bonus-graded with no bank, and the stamp covers this review.",
         "js": ["() => { const f = document.querySelector(\"form[action='/cards/" + CARD_ID + "/review']\"); "
                "if (!f) return 'seed-form-missing'; "
                "const ta = f.querySelector('textarea[name=answer]'); "
                "if (!ta) return 'no-textarea'; ta.value = '" + WRONG_ANSWER + "'; "
                "const conf = f.querySelector(\"input[name='confidence'][value='3']\"); "
                "if (conf) conf.checked = true; "
                "f.submit(); return 'submitted'; }"],
         "poll_js": "() => document.body.innerText.slice(0, 12000)",
         "poll_want": "Next review:",
         "poll_required": True,
         "poll_timeout": 25,
         "assert_js": "() => document.body.innerText.includes('Next review:')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "Proof in the fixture DB: last_probe stamped, re-listed plain -- never flagged twice.",
         "commands": [
             ["python3", "-c",
              "import os, sqlite3; con = sqlite3.connect(os.environ.get('DEMO_DB', 'groundwork.db')); "
              "print('last_probe:', con.execute(\"SELECT last_probe FROM cards WHERE id='" + CARD_ID + "'\").fetchone()[0]); "
              "con.execute(\"UPDATE cards SET due = strftime('%Y-%m-%dT%H:%M:%SZ','now','-1 days') WHERE id='" + CARD_ID + "'\"); "
              "con.commit(); "
              "from groundwork.mcp import MCPServer; "
              "due = MCPServer(os.environ['DEMO_DB']).tool_list_due_reviews({'limit': 20})['due']; "
              "hit = [c for c in due if c['id'] == '" + CARD_ID + "']; "
              "print('re-listed:', len(hit) == 1, '| probe flag:', hit[0].get('probe') if hit else 'missing')"],
         ]},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 15",
         "title": "One probe per cycle.",
         "subtitle": "last_probe covers the answered review -- the queue moves on."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Plant one owned stable card, last reviewed 8 days ago.

    Two passing reviews on an ownership type (24) own the concept;
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
            (MODULE_ID, "demo/probelife", "Probe lifecycle module", created))
        con.execute(
            "INSERT INTO concepts(id, module_id, name, kind)"
            " VALUES(?, ?, ?, ?)",
            (CONCEPT_ID, MODULE_ID, "recall", "function"))
        con.execute(
            "INSERT INTO cards(id, concept_id, exercise_type, front, back,"
            " payload, stability, due, stale, last_probe)"
            " VALUES(?, ?, '24', ?, ?, '{}', 10.0,"
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
