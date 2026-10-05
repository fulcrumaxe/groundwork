"""Feature demo: rate-limit design exercise (F-48, type 71).

Full behavior: the learner judges tradeoffs for a traffic profile
under an abuse scenario and submits five key=value lines (scope,
window, burst, retry, why). The rubric grader scores five independent
points with partial credit -- pass at half or more. Static,
deterministic.
"""
from __future__ import annotations

import json
import sqlite3

CARD_ID = 'demo-ratelimit-71'
FRONT = 'Design rate limits for `ingest` (webhooks): legit peak bursty 1000 events/min; abuse: a retry storm replays 10000 deliveries/min after an outage, overloading parsers. Submit five `key=value` lines: `scope=` (per-key AND global limits), `window=` (concrete window), `burst=` (burst handling), `retry=` (429 behavior), `why=` (one-line reason).'
BACK = 'scope=10/min per IP plus 1000/min global | window=60s fixed | burst=token bucket 5 | retry=429 with Retry-After: 60 | why=per-IP stops one abuser while the global cap guards total capacity; Retry-After forces backoff'
PAYLOAD = {'service': 'ingest', 'profile': 'webhooks', 'baseline': 'bursty 1000 events/min', 'abuse': 'a retry storm replays 10000 deliveries/min after an outage, overloading parsers', 'grounded': True}
ANSWER = 'scope=10/min per IP plus 1000/min global\nwindow=60s fixed\nburst=token bucket 5\nretry=429 with Retry-After: 60\nwhy=per-IP stops one abuser while global cap guards capacity'

SCENARIO = {
    "id": "ratelimit",
    "kind": "feature",
    "batch": 11,
    "item": "F-48",
    "title": "Rate-limit it",
    "blurb": "Design limits for a retry storm -- five points, half passes.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 11 - Feature F-48",
         "title": "Rate-limit it",
         "subtitle": "Scope, window, burst, retry, why -- five lines."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b11-ratelimit",
         "caption": "Status homes the type: traffic profile, abuse storm, rubric gate.",
         "assert_js": "() => !!document.querySelector('#status-b11-ratelimit')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 8,
         "caption": "The rule in one line: five-for-five passes, a bare scope fails.",
         "commands": [
             ["python3", "-c",
              "import sys; sys.path.insert(0, 'tools'); "
              "from demos.ratelimit import PAYLOAD, ANSWER; "
              "from groundwork import ratelimit as m; "
              "ex = {'payload': PAYLOAD}; "
              "ok = m.grade(ex, ANSWER); bad = m.grade(ex, 'scope=nothing'); "
              "print('good:', ok['pass'], '-', ok['feedback']); "
              "print('bad:', bad['pass'], '-', bad['feedback'])"],
         ]},
        {"type": "chrome", "duration": 8,
         "url_path": "/due",
         "focus": "#card-{seed_card_id}",
         "caption": "The rate-limit card: storm profile on top, five lines below.",
         "assert_js": "() => { const f = document.querySelector("
                      "\"form[action='/cards/{seed_card_id}/review']\"); "
                      "return !!f && !!f.querySelector(\"[name='answer']\") && "
                      "document.body.innerText.includes('key=value'); }",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 11",
         "title": "Survive the storm.",
         "subtitle": "ratelimit.py rubrics the plan -- per-key plus global."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Plant one type-71 card (generated shape) as the sole due card."""
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
            " VALUES(?, ?, '71', ?, ?, ?, '2000-01-01T00:00:00Z')",
            (CARD_ID, row[0], FRONT, BACK, json.dumps(PAYLOAD)))
        con.commit()
        return {"seeded": True, "card_id": CARD_ID}
    finally:
        con.close()
