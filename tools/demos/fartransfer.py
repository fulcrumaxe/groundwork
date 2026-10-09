"""Feature demo: far-transfer challenge (F-71, type 75).

Full behavior: re-express a source pattern in the other language
(Python <-> TS/JS) with every behavior intact -- a static all-check
gate with no partial credit. seed_db plants the generated port card
as the sole due card; the /due beat submits the full port and polls
the all-behaviors verdict.
"""
from __future__ import annotations

import json
import sqlite3

CARD_ID = "demo-b18-fartransfer"
SOURCE = "const nums = raw.filter(x => x.trim()).map(x => parseInt(x));"
REFERENCE = "nums = [int(x) for x in raw if x.strip()]"
FRONT = ("Far transfer: this `typescript` pattern comes from `add`. Re-express it in `python` "
         "preserving every behavior (filtering, defaults, types):\n```\n" + SOURCE + "\n```")
PAYLOAD = {"pattern": "map-default", "direction": "typescript->python",
           "source": SOURCE, "reference": REFERENCE,
           "check": ["for", "if", "int("], "grounded": True}
ANSWER = REFERENCE

SCENARIO = {
    "id": "fartransfer",
    "kind": "feature",
    "batch": 18,
    "item": "F-71",
    "title": "Far-transfer challenge",
    "blurb": "Port a pattern to the other language -- Python to JS/TS or back -- with every behavior intact.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 18 - Feature F-71",
         "title": "Far-transfer challenge",
         "subtitle": "Port the pattern across languages -- drop one behavior, drop the port."},
        {"type": "terminal", "duration": 7,
         "caption": "The gate in one call: all checks hold or the missing behavior is named.",
         "commands": [
             ["python3", "-c",
              "from groundwork import fartransfer as m; "
              "ex = {'payload': {'reference': 'r', 'check': ['for', 'if', 'int(']}}; "
              "print(m.grade(ex, 'nums = [int(x) for x in raw if x.strip()]')['feedback']); "
              "print(m.grade(ex, 'nums = [x for x in raw if x.strip()]')['feedback'])"],
         ]},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b18-fartransfer",
         "caption": "Status homes the type: fixed pattern catalog, no partial credit.",
         "assert_js": "() => !!document.querySelector('#status-b18-fartransfer')",
         "assert_want": "True"},
        {"type": "chrome", "duration": 8,
         "url_path": "/due",
         "focus": "#card-{seed_card_id} h3",
         "caption": "The port card: typescript in, python out, every behavior kept.",
         "assert_js": "() => { const f = document.querySelector("
                      "\"form[action='/cards/{seed_card_id}/review']\"); "
                      "return !!f && document.body.innerText.includes('Re-express it'); }",
         "assert_want": "True"},
        {"type": "chrome", "duration": 13,
         "url_path": "/due",
         "caption": "The full port -- filter, guard, and conversion all survive.",
         "js": ["() => { const f = document.querySelector(\"form[action='/cards/{seed_card_id}/review']\"); "
                "if (!f) return 'seed-form-missing'; "
                "f.querySelectorAll(\"input[name='answer']\").forEach(i => i.value = {seed_answer_js}); "
                "const conf = f.querySelector(\"input[name='confidence'][value='4']\"); "
                "if (conf) conf.checked = true; "
                "f.submit(); return 'submitted'; }"],
         "poll_js": "() => document.body.innerText.slice(0, 12000)",
         "poll_want": "All 3 behaviors ported",
         "poll_required": True,
         "poll_timeout": 25,
         "assert_js": "() => !!document.querySelector('.verdict-stamp') && "
                      "document.body.innerText.includes('All 3 behaviors ported')",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 18",
         "title": "Every behavior survives.",
         "subtitle": "fartransfer.py gates the port statically -- all checks, no credit split."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Plant the generated type-75 card (pipeline shape) as the sole due card."""
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
            " VALUES(?, ?, '75', ?, ?, ?, '2000-01-01T00:00:00Z')",
            (CARD_ID, row[0], FRONT, REFERENCE, json.dumps(PAYLOAD)))
        con.commit()
        return {"seeded": True, "card_id": CARD_ID,
                "answer_js": json.dumps(json.dumps(ANSWER))[1:-1]}
    finally:
        con.close()
