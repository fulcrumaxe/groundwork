"""Feature demo: pre-mortem (F-74, type 78).

Full behavior: assume the code already failed in production and list
how -- graded against a statically derived checklist with per-item
partial credit where half or more passes. seed_db plants the
generated pre-mortem card as the sole due card; the /due beat names
all four modes and polls the full-marks verdict.
"""
from __future__ import annotations

import json
import sqlite3

CARD_ID = "demo-b18-premortem"
CODE = ("def fetch(path):\n    f = open(path)\n    data = f.read()\n"
        "    first = data[0]\n    return requests.get(first)")
FRONT = ("Pre-mortem `add`: assume it failed in production. List how (4 failure modes, one per line).\n"
         "```python\n" + CODE + "\n```")
ITEMS = ["Unhandled error: exception path escapes with no try/except",
         "No retry/timeout around a fallible call (network, subprocess, IO)",
         "Resource leak: open()/lock acquired with no close/release path",
         "Boundary slip: off-by-one, empty input, or unguarded index/slice"]
KEYS = [["unhandled", "exception", "try", "except"],
        ["retry", "timeout", "backoff"],
        ["leak", "close", "release", "open("],
        ["boundary", "off-by-one", "empty", "index"]]
BACK = "\n".join(f"{i + 1}. {s}" for i, s in enumerate(ITEMS))
PAYLOAD = {"items": ITEMS, "keys": KEYS, "solution": ITEMS,
           "surface": ["unhandled-error", "no-retry", "resource-leak",
                       "boundary"],
           "check": "pre-mortem", "grounded": True}
ANSWER = "unhandled error, no retry, resource leak, boundary index"

SCENARIO = {
    "id": "premortem",
    "kind": "feature",
    "batch": 18,
    "item": "F-74",
    "title": "Pre-mortem",
    "blurb": "List how this code could fail before it does -- errors, retries, races, leaks.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 18 - Feature F-74",
         "title": "Pre-mortem",
         "subtitle": "It already failed -- list how, against a static checklist."},
        {"type": "terminal", "duration": 7,
         "caption": "The checklist in one call: full marks, then a half-credit pass naming its miss.",
         "commands": [
             ["python3", "-c",
              "from groundwork import premortem as m; "
              "ex = {'payload': {'items': ['Unhandled error', 'No retry'], 'keys': [['unhandled'], ['retry']]}}; "
              "print(m.grade(ex, 'unhandled error, no retry')['feedback']); "
              "print(m.grade(ex, 'unhandled error')['feedback'])"],
         ]},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b18-premortem",
         "caption": "Status homes the type: static detectors, no sandbox, half to pass.",
         "assert_js": "() => !!document.querySelector('#status-b18-premortem')",
         "assert_want": "True"},
        {"type": "chrome", "duration": 8,
         "url_path": "/due",
         "focus": "#card-{seed_card_id} h3",
         "caption": "The pre-mortem card: four failure modes hiding in plain code.",
         "assert_js": "() => { const f = document.querySelector("
                      "\"form[action='/cards/{seed_card_id}/review']\"); "
                      "return !!f && document.body.innerText.includes('assume it failed'); }",
         "assert_want": "True"},
        {"type": "chrome", "duration": 13,
         "url_path": "/due",
         "caption": "All four modes named -- errors, retries, leaks, boundaries.",
         "js": ["() => { const f = document.querySelector(\"form[action='/cards/{seed_card_id}/review']\"); "
                "if (!f) return 'seed-form-missing'; "
                "f.querySelectorAll(\"input[name='answer']\").forEach(i => i.value = {seed_answer_js}); "
                "const conf = f.querySelector(\"input[name='confidence'][value='4']\"); "
                "if (conf) conf.checked = true; "
                "f.submit(); return 'submitted'; }"],
         "poll_js": "() => document.body.innerText.slice(0, 12000)",
         "poll_want": "Full pre-mortem",
         "poll_required": True,
         "poll_timeout": 25,
         "assert_js": "() => !!document.querySelector('.verdict-stamp') && "
                      "document.body.innerText.includes('Full pre-mortem (4/4 modes)')",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 18",
         "title": "Fail it first.",
         "subtitle": "premortem.py derives the checklist statically -- name half to pass."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Plant the generated type-78 card (pipeline shape) as the sole due card."""
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
            " VALUES(?, ?, '78', ?, ?, ?, '2000-01-01T00:00:00Z')",
            (CARD_ID, row[0], FRONT, BACK, json.dumps(PAYLOAD)))
        con.commit()
        return {"seeded": True, "card_id": CARD_ID,
                "answer_js": json.dumps(json.dumps(ANSWER))[1:-1]}
    finally:
        con.close()
