"""Feature demo: idempotency double-run exercise (F-47, type 70).

Full behavior: the learner rewrites a non-idempotent handler into a
re-runnable one -- handle(store, event, emit) must apply its effect
exactly once per key. The grader runs the handler twice on the same
store (same end state AND zero new side effects), then checks liveness
on fresh stores. All-or-nothing: a retry that double-charges fails.
"""
from __future__ import annotations

import json
import sqlite3

CARD_ID = 'demo-idempot-70'
FRONT = 'Make `handle(store, event, emit)` re-runnable: applying event key `evt-0b5a94ae` twice must leave the same end state with no duplicate side effects, and a fresh key must still apply.\n```python\ndef handle(store, event, emit):\n    store.setdefault("log", []).append(event["item"])\n    emit("charged")\n```'
BACK = 'def handle(store, event, emit):\n    seen = store.setdefault("seen", set())\n    if event["key"] in seen:\n        return\n    seen.add(event["key"])\n    store.setdefault("log", []).append(event["item"])\n    emit("charged")\n'
PAYLOAD = {'key': 'evt-0b5a94ae', 'handler': 'handle', 'starter': 'def handle(store, event, emit):\n    store.setdefault("log", []).append(event["item"])\n    emit("charged")\n', 'grounded': True}
ANSWER = 'def handle(store, event, emit):\n    seen = store.setdefault("seen", set())\n    if event["key"] in seen:\n        return\n    seen.add(event["key"])\n    store.setdefault("log", []).append(event["item"])\n    emit("charged")\n'

SCENARIO = {
    "id": "idempot",
    "kind": "feature",
    "batch": 11,
    "item": "F-47",
    "title": "Idempotency double-run",
    "blurb": "Retry-safe handlers -- twice applied, once effected.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 11 - Feature F-47",
         "title": "Idempotency double-run",
         "subtitle": "Apply twice, effect once -- or fail."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b11-idempot",
         "caption": "Status homes the type: double run, same state, fresh keys alive.",
         "assert_js": "() => !!document.querySelector('#status-b11-idempot')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 8,
         "caption": "The rule in one line: the guarded handler passes, the starter double-charges.",
         "commands": [
             ["python3", "-c",
              "import sys; sys.path.insert(0, 'tools'); "
              "from demos.idempot import PAYLOAD, ANSWER; "
              "from groundwork import idempot as m; "
              "ex = {'payload': PAYLOAD}; "
              "ok = m.grade(ex, ANSWER); "
              "bad = m.grade(ex, PAYLOAD['starter']); "
              "print('good:', ok['pass'], '-', ok['feedback']); "
              "print('bad:', bad['pass'], '-', bad['feedback'])"],
         ]},
        {"type": "chrome", "duration": 8,
         "url_path": "/due",
         "focus": "#card-{seed_card_id}",
         "caption": "The idempotency card: charging handler on top, rewrite below.",
         "assert_js": "() => { const f = document.querySelector("
                      "\"form[action='/cards/{seed_card_id}/review']\"); "
                      "return !!f && !!f.querySelector(\"[name='answer']\") && "
                      "document.body.innerText.includes('re-runnable'); }",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 11",
         "title": "Safe to retry.",
         "subtitle": "idempot.py runs it twice -- duplicates are failure."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Plant one type-70 card (generated shape) as the sole due card."""
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
            " VALUES(?, ?, '70', ?, ?, ?, '2000-01-01T00:00:00Z')",
            (CARD_ID, row[0], FRONT, BACK, json.dumps(PAYLOAD)))
        con.commit()
        return {"seeded": True, "card_id": CARD_ID}
    finally:
        con.close()
