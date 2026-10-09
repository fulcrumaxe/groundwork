"""Feature demo: pressure drill (F-72, type 76).

Full behavior: diagnose a production-style log against a 90s drill
budget -- follow the victim request id past WARN noise and a decoy
failing request, then name the exact root cause. seed_db plants the
generated drill card as the sole due card; the /due beat names the
cause and polls the inside-budget verdict.
"""
from __future__ import annotations

import json
import sqlite3

CARD_ID = "demo-b18-pressure"
LOG = ("14:00:58.790 INFO  edge-gw: listening on :8080 (req-c810 warmup)\n"
       "14:00:59.443 INFO  order-worker: pool ready (8 workers)\n"
       "14:01:02.798 WARN  order-worker: auth-svc: clock skew 120ms vs ntp (tolerance 500ms)\n"
       "14:01:04.624 INFO  edge-gw: req-6eca GET /stats 200 4ms\n"
       "14:01:05.308 WARN  edge-gw: search-api: deprecated v1 endpoint /old-search called 12 times\n"
       "14:01:07.178 INFO  edge-gw: req-c810 POST /orders accepted\n"
       "14:01:09.691 ERROR checkout-api: metrics-agent: push to stats-sink failed: dial tcp: i/o timeout (non-blocking) [req-6eca]\n"
       "14:01:11.977 ERROR order-worker: search-api: GET /search exceeded 3000ms deadline (search-svc) [req-c810]\n"
       "14:01:13.833 ERROR edge-gw: edge-gw: upstream search-svc timed out after 3 attempts [req-c810]\n"
       "14:01:15.736 FATAL checkout-api: edge-gw: 504 Gateway Timeout on /search, circuit open [req-c810]")
FRONT = ("DRILL \u2014 90s budget. Read ONLY this production log and name the exact ROOT CAUSE "
         "(one phrase from the list). Follow the failing request id; every other request is noise.\n"
         "Choices: database connection refused; upstream timeout; auth token expired; disk full\n"
         "```log\n" + LOG + "\n```")
BACK = "Root cause: `upstream timeout` (victim req-c810)."
PAYLOAD = {"log": LOG, "cause": "upstream timeout",
           "answer": "upstream timeout",
           "aliases": ["timeout", "timed out", "gateway timeout", "504"],
           "choices": ["database connection refused", "upstream timeout",
                       "auth token expired", "disk full"],
           "victim": "req-c810", "decoy": "req-6eca", "budget_s": 90,
           "mode": "synthesized", "grounded": True}
ANSWER = "upstream timeout"

SCENARIO = {
    "id": "pressure",
    "kind": "feature",
    "batch": 18,
    "item": "F-72",
    "title": "Pressure drill",
    "blurb": "Diagnose a production-style log against a 90s clock -- follow the victim request, not the noise.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 18 - Feature F-72",
         "title": "Pressure drill",
         "subtitle": "One victim request id in a noisy log -- name the exact cause in 90 seconds."},
        {"type": "terminal", "duration": 7,
         "caption": "The match in one call: the cause phrase passes, a herring never does.",
         "commands": [
             ["python3", "-c",
              "from groundwork import pressure as m; "
              "ex = {'payload': {'cause': 'upstream timeout'}}; "
              "print(m.grade(ex, 'upstream timeout')['feedback']); "
              "print(m.grade(ex, 'disk full')['feedback']); "
              "print(m.grade(ex, 'log line 1\\nlog line 2')['feedback'])"],
         ]},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b18-pressure",
         "caption": "Status homes the type: advisory budget, deterministic exact-phrase grading.",
         "assert_js": "() => !!document.querySelector('#status-b18-pressure')",
         "assert_want": "True"},
        {"type": "chrome", "duration": 8,
         "url_path": "/due",
         "focus": "#card-{seed_card_id} h3",
         "caption": "The drill card: one victim request id in a noisy production log.",
         "assert_js": "() => { const f = document.querySelector("
                      "\"form[action='/cards/{seed_card_id}/review']\"); "
                      "return !!f && document.body.innerText.includes('ROOT CAUSE'); }",
         "assert_want": "True"},
        {"type": "chrome", "duration": 13,
         "url_path": "/due",
         "caption": "Victim req-c810 followed past the noise -- the exact phrase wins.",
         "js": ["() => { const f = document.querySelector(\"form[action='/cards/{seed_card_id}/review']\"); "
                "if (!f) return 'seed-form-missing'; "
                "f.querySelectorAll(\"input[name='answer']\").forEach(i => i.value = {seed_answer_js}); "
                "const conf = f.querySelector(\"input[name='confidence'][value='4']\"); "
                "if (conf) conf.checked = true; "
                "f.submit(); return 'submitted'; }"],
         "poll_js": "() => document.body.innerText.slice(0, 12000)",
         "poll_want": "Correct: upstream timeout",
         "poll_required": True,
         "poll_timeout": 25,
         "assert_js": "() => !!document.querySelector('.verdict-stamp') && "
                      "document.body.innerText.includes('inside the 90s drill budget')",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 18",
         "title": "Follow the victim.",
         "subtitle": "pressure.py builds the log, seeds the herrings -- exact phrase decides."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Plant the generated type-76 card (pipeline shape) as the sole due card.

    The commander track gates diagnose (76) behind replay (77): two
    passing reviews on a not-due helper replay card clear the first
    stage so the drill card reaches the queue.
    """
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
            " VALUES(?, ?, '76', ?, ?, ?, '2000-01-01T00:00:00Z')",
            (CARD_ID, row[0], FRONT, BACK, json.dumps(PAYLOAD)))
        helper = "demo-b18-pressure-replay"
        con.execute("DELETE FROM reviews WHERE card_id=?", (helper,))
        con.execute(
            "INSERT OR REPLACE INTO cards(id, concept_id, exercise_type,"
            " front, back, payload, due)"
            " VALUES(?, ?, '77', ?, ?, ?, '2030-01-01T00:00:00Z')",
            (helper, row[0], "Replay helper (not due)", "helper",
             json.dumps({"shown": [], "order": [0, 1, 2, 3]})))
        for _ in range(2):
            con.execute(
                "INSERT INTO reviews(card_id, grade, confidence, submission)"
                " VALUES(?, 5, 4, 'replay proof')", (helper,))
        con.commit()
        return {"seeded": True, "card_id": CARD_ID,
                "answer_js": json.dumps(json.dumps(ANSWER))[1:-1]}
    finally:
        con.close()
