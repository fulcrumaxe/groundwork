"""Feature demo: frustration relief (F-96).

Full behavior: three fast fails in a row on one card raise a relief banner
on the verdict page -- a breather note plus a link to an easier same-concept
card. seed_db plants a type-1 card with two prior fails and an easier
sibling; the /due beat submits a third fail and films the banner.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone

MODULE_ID = "demo-frust-96"
NODE = "demo/relief.py:total"
CONCEPT_ID = f"{MODULE_ID}:{NODE}"
CARD_ID = "demo-frust-hard"
EASY_ID = "demo-frust-easy"

SCENARIO = {
    "id": "frustcatch",
    "kind": "feature",
    "batch": 21,
    "item": "F-96",
    "title": "Frustration relief",
    "blurb": "Three fast fails earn a breather note and an easier card on the same idea.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 21 - Feature F-96",
         "title": "Frustration relief",
         "subtitle": "Three fast fails -- a signal, not a verdict. Take the smaller step."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b21-frustcatch",
         "caption": "Status documents the relief: streak rule plus easier-card routing.",
         "assert_js": "() => !!document.querySelector('#status-b21-frustcatch')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 8,
         "caption": "The rule in one line: a tail of 3 fast fails plans relief.",
         "commands": [
             ["python3", "-c",
              "from groundwork import frustcatch as m; "
              "pool = [{'id': 'easy', 'difficulty': 0.1}]; "
              "plan = m.relief_plan([5, 1, 2, 1], pool, 'hard'); "
              "print('frustrated:', plan['frustrated'], '| streak:', plan['streak']); "
              "print('easier:', plan['easier']['id']); "
              "print('calm:', m.relief_plan([5, 4, 5], pool, 'hard')['frustrated'])"],
         ]},
        {"type": "chrome", "duration": 16,
         "url_path": "/due",
         "focus": "p.relief",
         "caption": "Fail the struggling card again -- the verdict offers the easier step.",
         "js": ["() => { const f = document.querySelector(\"form[action='/cards/{seed_card_id}/review']\"); "
                "if (!f) return 'seed-form-missing'; "
                "const sel = f.querySelector(\"select[name='answer']\"); "
                "if (!sel) return 'no-select'; sel.value = '1'; "
                "const conf = f.querySelector(\"input[name='confidence'][value='2']\"); "
                "if (conf) conf.checked = true; "
                "f.submit(); return 'submitted'; }"],
         "poll_js": "() => document.body.innerText.slice(0, 12000)",
         "poll_want": "misses in a row",
         "poll_required": True,
         "poll_timeout": 25,
         "assert_js": "() => !!document.querySelector('p.relief') && "
                      "document.body.innerText.includes('Try an easier card instead')",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 21",
         "title": "Rebuild, then retry.",
         "subtitle": "frustcatch.py routes strugglers -- calm cards grade as before."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Plant a failing type-1 card with two prior fails + easier sibling."""
    con = sqlite3.connect(db_path)
    try:
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        for cid in (CARD_ID, EASY_ID):
            con.execute("DELETE FROM reviews WHERE card_id=?", (cid,))
            con.execute("DELETE FROM cards WHERE id=?", (cid,))
        con.execute("DELETE FROM concepts WHERE id=?", (CONCEPT_ID,))
        con.execute("DELETE FROM modules WHERE id=?", (MODULE_ID,))
        lesson = {"concept_id": NODE, "name": "total", "kind": "function",
                  "file": "demo/relief.py", "line": 1,
                  "summary": "Sum rows into a running total."}
        con.execute(
            "INSERT INTO modules(id, repo, task_summary, created_at, lessons)"
            " VALUES(?, ?, ?, ?, ?)",
            (MODULE_ID, "demo/frustcatch", "Frustration relief module", now,
             json.dumps([lesson])))
        con.execute(
            "INSERT INTO concepts(id, module_id, name, kind, file,"
            " line, mastery) VALUES(?, ?, ?, ?, ?, ?, ?)",
            (CONCEPT_ID, MODULE_ID, "total", "function",
             "demo/relief.py", 1, 0.0))
        con.execute(
            "INSERT INTO cards(id, concept_id, exercise_type, front, back,"
            " difficulty, due) VALUES(?, ?, '1', ?, ?, 0.5, ?)",
            (CARD_ID, CONCEPT_ID, "What does total() return with no rows?",
             "0: the seed value.", "2000-01-01T00:00:00Z"))
        con.execute(
            "INSERT INTO cards(id, concept_id, exercise_type, front, back,"
            " difficulty, due) VALUES(?, ?, '1', ?, ?, 0.1, ?)",
            (EASY_ID, CONCEPT_ID, "What value seeds the total?",
             "Zero.", "2000-01-01T00:00:00Z"))
        for grade in (1, 2):
            con.execute(
                "INSERT INTO reviews(card_id, grade, confidence, submission)"
                " VALUES(?, ?, 2, 'frustcatch seed')", (CARD_ID, grade))
        con.commit()
        return {"seeded": True, "card_id": CARD_ID, "easy_id": EASY_ID}
    finally:
        con.close()
