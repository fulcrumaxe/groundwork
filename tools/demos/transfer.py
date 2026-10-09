"""Feature demo: transfer test (F-70, type 74).

Full behavior: the same concept restated in unfamiliar renamed code
with no lesson links on the front -- predict the output and the
sandbox grades behavior, not recall. seed_db plants the generated
transfer card as the sole due card; the /due beat answers the
measured output and polls the transfer-holds verdict.
"""
from __future__ import annotations

import json
import sqlite3

CARD_ID = "demo-b18-transfer"
NOVEL = "zuna_0 = 2 + 3\nprint(zuna_0)"
REFERENCE = "total = 2 + 3\nprint(total)"
FRONT = ("You know `add` \u2014 now prove it somewhere new. This snippet restates the same idea "
         "in code you have not seen (names changed, idea kept). There are no links back to the lesson.\n"
         "What does it print/return?\n```python\n" + NOVEL + "\n```")
BACK = "5"
PAYLOAD = {"novel": NOVEL, "expected": "5", "reference": REFERENCE,
           "check": {"expected": "5"}, "grounded": True}
ANSWER = "5"

SCENARIO = {
    "id": "transfer",
    "kind": "feature",
    "batch": 18,
    "item": "F-70",
    "title": "Transfer test",
    "blurb": "Same idea in code you have never seen -- no lesson links on the front; the sandbox checks the behavior.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 18 - Feature F-70",
         "title": "Transfer test",
         "subtitle": "Known idea, unfamiliar code -- the sandbox grades what it does."},
        {"type": "terminal", "duration": 7,
         "caption": "The rename in one call: identifiers novel, structure kept, output measured.",
         "commands": [
             ["python3", "-c",
              "from types import SimpleNamespace as NS; "
              "from groundwork import transfer as m; "
              "c = NS(name='add', file='calc.py', line=1, node_id='m:add'); "
              "ex = m.generate('x', c, [], {'runnable': 'total = 2 + 3\\nprint(total)', 'expected_output': '5'}); "
              "print('novel:', repr(ex['payload']['novel'])); "
              "print('no lesson anchor:', 'calc.py' not in ex['front'] and ':1' not in ex['front']); "
              "print(m.grade(ex, '')['feedback'])"],
         ]},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b18-transfer",
         "caption": "Status homes the type: renamed snippet, sandbox-measured grading.",
         "assert_js": "() => !!document.querySelector('#status-b18-transfer')",
         "assert_want": "True"},
        {"type": "chrome", "duration": 8,
         "url_path": "/due",
         "focus": "#card-{seed_card_id} h3",
         "caption": "The transfer card: renamed code, no lesson links, predict the output.",
         "assert_js": "() => { const f = document.querySelector("
                      "\"form[action='/cards/{seed_card_id}/review']\"); "
                      "return !!f && document.body.innerText.includes('prove it somewhere new'); }",
         "assert_want": "True"},
        {"type": "chrome", "duration": 13,
         "url_path": "/due",
         "caption": "The measured output -- same idea recognized in unfamiliar code.",
         "js": ["() => { const f = document.querySelector(\"form[action='/cards/{seed_card_id}/review']\"); "
                "if (!f) return 'seed-form-missing'; "
                "f.querySelectorAll(\"input[name='answer']\").forEach(i => i.value = {seed_answer_js}); "
                "const conf = f.querySelector(\"input[name='confidence'][value='4']\"); "
                "if (conf) conf.checked = true; "
                "f.submit(); return 'submitted'; }"],
         "poll_js": "() => document.body.innerText.slice(0, 12000)",
         "poll_want": "Transfer holds",
         "poll_required": True,
         "poll_timeout": 25,
         "assert_js": "() => !!document.querySelector('.verdict-stamp') && "
                      "document.body.innerText.includes('same idea, new code')",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 18",
         "title": "Behavior, not recall.",
         "subtitle": "transfer.py renames and measures -- lesson text cannot pass."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Plant the generated type-74 card (pipeline shape) as the sole due card."""
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
            " VALUES(?, ?, '74', ?, ?, ?, '2000-01-01T00:00:00Z')",
            (CARD_ID, row[0], FRONT, BACK, json.dumps(PAYLOAD)))
        con.commit()
        return {"seeded": True, "card_id": CARD_ID,
                "answer_js": json.dumps(json.dumps(ANSWER))[1:-1]}
    finally:
        con.close()
