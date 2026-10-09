"""Feature demo: incident replay (F-73, type 77).

Full behavior: replay a past outage from four shuffled timeline
events -- submit signal/detect/mitigate/prevent/order key=value
lines for rubric partial credit where half or more passes. seed_db
plants the generated replay card as the sole due card; the /due
beat posts all five lines and polls the 5/5 verdict.
"""
from __future__ import annotations

import json
import sqlite3

CARD_ID = "demo-b18-incident"
SHOWN = ["deploy freeze plus canary gate lands in the postmortem",
         "rollback to the previous release restores service",
         "error-rate alert fires after the deploy",
         "on-call diffs the release and finds the breaking change"]
FRONT = ("Replay this past outage on `calc` (bad-deploy: bad deploy pages at 02:00). "
         "These four timeline events are shuffled:\n"
         "A. deploy freeze plus canary gate lands in the postmortem\n"
         "B. rollback to the previous release restores service\n"
         "C. error-rate alert fires after the deploy\n"
         "D. on-call diffs the release and finds the breaking change\n"
         "Submit five `key=value` lines: `signal=` (what alerted), `detect=` (how on-call found "
         "the cause), `mitigate=` (what restored service), `prevent=` (what stops recurrence), "
         "`order=` (the true chronological letter sequence, e.g. `order=C A B D`).")
BACK = ("signal=error-rate alert fires after the deploy\n"
        "detect=on-call diffs the release and finds the breaking change\n"
        "mitigate=rollback to the previous release restores service\n"
        "prevent=deploy freeze plus canary gate lands in the postmortem\n"
        "order=C D B A")
PAYLOAD = {"service": "calc", "scenario": "bad-deploy", "shown": SHOWN,
           "order": [3, 2, 0, 1],
           "signal_kw": ["error", "alert", "5xx", "deploy"],
           "detect_kw": ["diff", "bisect", "log", "release"],
           "mitigate_kw": ["rollback", "revert", "previous release"],
           "prevent_kw": ["canary", "freeze", "gate", "postmortem"],
           "check": BACK, "grounded": True}
ANSWER = BACK

SCENARIO = {
    "id": "incident",
    "kind": "feature",
    "batch": 18,
    "item": "F-73",
    "title": "Incident replay",
    "blurb": "Replay a past outage -- signal, detection, mitigation, prevention, and timeline order, rubric-graded.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 18 - Feature F-73",
         "title": "Incident replay",
         "subtitle": "Five keyed lines against a shuffled outage -- half or more passes."},
        {"type": "terminal", "duration": 8,
         "caption": "The rubric in one call: five points, partial credit, the order must match.",
         "commands": [
             ["python3", "-c",
              "from groundwork import incident as m; "
              "import json; ex = {'payload': json.loads('{\"signal_kw\": [\"error\", \"alert\"], \"detect_kw\": [\"diff\"], \"mitigate_kw\": [\"rollback\"], \"prevent_kw\": [\"canary\"], \"order\": [3, 2, 0, 1], \"shown\": [1, 2, 3, 4]}')}; "
              "print(m.grade(ex, 'signal=error alert\\ndetect=diff\\nmitigate=rollback\\nprevent=canary\\norder=C D B A')['feedback']); "
              "print(m.grade(ex, 'signal=error alert\\norder=C D B A')['feedback'])"],
         ]},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b18-incident",
         "caption": "Status homes the type: signal to prevention plus the true order.",
         "assert_js": "() => !!document.querySelector('#status-b18-incident')",
         "assert_want": "True"},
        {"type": "chrome", "duration": 8,
         "url_path": "/due",
         "focus": "#card-{seed_card_id} h3",
         "caption": "The replay card: four shuffled events, five keyed lines to write.",
         "assert_js": "() => { const f = document.querySelector("
                      "\"form[action='/cards/{seed_card_id}/review']\"); "
                      "return !!f && document.body.innerText.includes('key=value'); }",
         "assert_want": "True"},
        {"type": "chrome", "duration": 14,
         "url_path": "/due",
         "caption": "All five lines posted -- signal through order, every point hit.",
         "js": ["() => { const f = document.querySelector(\"form[action='/cards/{seed_card_id}/review']\"); "
                "if (!f) return 'seed-form-missing'; "
                "const nf = document.createElement('form'); nf.method = 'post'; nf.action = f.action; "
                "const ta = document.createElement('textarea'); ta.name = 'answer'; ta.value = {seed_answer_js}; "
                "const cf = document.createElement('input'); cf.type = 'hidden'; cf.name = 'confidence'; cf.value = '4'; "
                "const og = document.createElement('input'); og.type = 'hidden'; og.name = 'origin'; og.value = '/due'; "
                "nf.appendChild(ta); nf.appendChild(cf); nf.appendChild(og); "
                "document.body.appendChild(nf); nf.submit(); return 'submitted'; }"],
         "poll_js": "() => document.body.innerText.slice(0, 12000)",
         "poll_want": "Incident replay 5/5",
         "poll_required": True,
         "poll_timeout": 25,
         "assert_js": "() => !!document.querySelector('.verdict-stamp') && "
                      "document.body.innerText.includes('Incident replay 5/5')",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 18",
         "title": "Signal to prevention.",
         "subtitle": "incident.py shuffles the timeline -- the rubric scores all five points."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Plant the generated type-77 card (pipeline shape) as the sole due card."""
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
            " VALUES(?, ?, '77', ?, ?, ?, '2000-01-01T00:00:00Z')",
            (CARD_ID, row[0], FRONT, BACK, json.dumps(PAYLOAD)))
        con.commit()
        return {"seeded": True, "card_id": CARD_ID,
                "answer_js": json.dumps(json.dumps(ANSWER))[1:-1]}
    finally:
        con.close()
