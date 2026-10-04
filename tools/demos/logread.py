"""Feature demo: log reading (F-35, type 58).

Full behavior: read a short synthetic log describing exactly ONE
root cause from a fixed taxonomy and name that exact cause --
two WARN red herrings share incident vocabulary but explain
nothing and never pass. seed_db plants a static database-connection-
refused card (grounded, generate() bytes) as the sole due card;
/due names the cause and polls the exact-phrase verdict.
"""
from __future__ import annotations

import json
import sqlite3

CARD_ID = "demo-logread-58"

SCENARIO = {
    "id": "logread",
    "kind": "feature",
    "batch": 10,
    "item": "F-35",
    "title": "Log reading",
    "blurb": "Diagnose an outage from logs alone -- name the exact root cause, not a red herring.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 10 - Feature F-35",
         "title": "Log reading",
         "subtitle": "Follow the ERROR chain -- the WARN lines are noise."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b10-logread",
         "caption": "Status homes the type: one taxonomy cause, WARN herrings, exact phrase.",
         "assert_js": "() => !!document.querySelector('#status-b10-logread')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "The rule in one line: the FATAL cause passes, a WARN herring never does.",
         "commands": [
             ["python3", "-c",
              "from groundwork import logread as m; "
              "ex = {'payload': {'cause': 'database connection refused'}}; "
              "print(m.grade(ex, 'Database Connection Refused')['feedback']); "
              "print(m.grade(ex, 'slow query 512ms')['feedback'])"],
         ]},
        {"type": "chrome", "duration": 8,
         "url_path": "/due",
         "focus": "#card-{seed_card_id}",
         "caption": "The log card: INFO, WARN noise, then the ERROR/FATAL chain.",
         "assert_js": "() => { const f = document.querySelector("
                      "\"form[action='/cards/{seed_card_id}/review']\"); "
                      "return !!f && !!f.querySelector(\"input[name='answer']\") && "
                      "document.body.innerText.includes('ROOT CAUSE'); }",
         "assert_want": "True"},
        {"type": "chrome", "duration": 13,
         "url_path": "/due",
         "caption": "Name the cause -- the verdict follows the FATAL line.",
         "js": ["() => { const f = document.querySelector(\"form[action='/cards/{seed_card_id}/review']\"); "
                "if (!f) return 'seed-form-missing'; "
                "const inp = f.querySelector(\"input[name='answer']\"); "
                "if (!inp) return 'no-input'; inp.value = {seed_answer_js}; "
                "const conf = f.querySelector(\"input[name='confidence'][value='4']\"); "
                "if (conf) conf.checked = true; "
                "f.submit(); return 'submitted'; }"],
         "poll_js": "() => document.body.innerText.slice(0, 12000)",
         "poll_want": "Correct: database connection refused",
         "poll_required": True,
         "poll_timeout": 25,
         "assert_js": "() => !!document.querySelector('.verdict-stamp') && "
                      "document.body.innerText.includes('Correct: database connection refused')",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 10",
         "title": "Cause, not noise.",
         "subtitle": "logread.py grades the phrase -- herrings and dumps fail."},
    ],
}

FRONT = 'Read ONLY this log and name the exact ROOT CAUSE (one phrase from the list). WARN lines that explain nothing are red herrings.\nChoices: database connection refused; out of memory; disk full; auth token expired; upstream timeout; tls certificate expired\n```log\n10:00:32 INFO api: listening on :8080\n10:00:34 INFO worker: pool ready (4 workers)\n10:00:41 WARN cache: miss rate 41% above baseline on products:*\n10:00:46 WARN worker: slow query 512ms on orders_by_user (threshold 500ms)\n10:00:53 ERROR db: connect postgres://db:5432/app failed: connection refused\n10:00:54 ERROR api: request GET /orders failed: upstream db unreachable\n10:00:55 FATAL worker: no healthy database backend, shutting down\n```'
BACK = 'Root cause: `database connection refused` (see the FATAL line).'
PAYLOAD = {'log': '10:00:32 INFO api: listening on :8080\n10:00:34 INFO worker: pool ready (4 workers)\n10:00:41 WARN cache: miss rate 41% above baseline on products:*\n10:00:46 WARN worker: slow query 512ms on orders_by_user (threshold 500ms)\n10:00:53 ERROR db: connect postgres://db:5432/app failed: connection refused\n10:00:54 ERROR api: request GET /orders failed: upstream db unreachable\n10:00:55 FATAL worker: no healthy database backend, shutting down', 'cause': 'database connection refused', 'choices': ['database connection refused', 'out of memory', 'disk full', 'auth token expired', 'upstream timeout', 'tls certificate expired'], 'herrings': ['cache: miss rate 41% above baseline on products:*', 'worker: slow query 512ms on orders_by_user (threshold 500ms)'], 'mode': 'grounded', 'grounded': True}
ANSWER = "database connection refused"


def seed_db(db_path: str) -> dict:
    """Plant one type-58 card (generate() bytes) as the sole due card."""
    con = sqlite3.connect(db_path)
    try:
        row = con.execute(
            "SELECT id FROM concepts ORDER BY rowid LIMIT 1").fetchone()
        if not row:
            return {"seeded": False, "reason": "no concepts"}
        con.execute("UPDATE cards SET due='2030-01-01T00:00:00Z'")
        con.execute("DELETE FROM reviews WHERE card_id=?", (CARD_ID,))
        con.execute(
            "INSERT OR REPLACE INTO cards(id, concept_id, exercise_type,"
            " front, back, payload, due)"
            " VALUES(?, ?, '58', ?, ?, ?, '2000-01-01T00:00:00Z')",
            (CARD_ID, row[0], FRONT, BACK, json.dumps(PAYLOAD)))
        con.commit()
        return {"seeded": True, "card_id": CARD_ID,
                "answer_js": json.dumps(json.dumps(ANSWER))[1:-1]}
    finally:
        con.close()
