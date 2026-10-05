"""Feature demo: feature-flag removal exercise (F-43, type 66).

Full behavior: the learner cuts a stale flag branch -- the flag name
must vanish everywhere (a grep gate catches comments and strings
where tests stay green) AND the hidden tests must stay green on the
pruned code. seed_db plants the generated card as the sole due card;
the terminal beat grades the reference through the sandbox.
"""
from __future__ import annotations

import json
import sqlite3

CARD_ID = 'demo-flagcut-66'
FRONT = 'Cut the stale flag `NEW_UI` in `handle`: remove every reference to the flag name and resolve both branches so only live behavior remains. The hidden tests must stay green.\n```python\nNEW_UI = False\n\ndef handle(x):\n    if NEW_UI:\n        out = x * 2\n    else:\n        out = x + 100\n    return out\n```'
BACK = 'def handle(x):\n    out = x + 100\n    return out\n'
PAYLOAD = {'flag': 'NEW_UI', 'func': 'handle', 'original': 'NEW_UI = False\n\ndef handle(x):\n    if NEW_UI:\n        out = x * 2\n    else:\n        out = x + 100\n    return out\n', 'reference': 'def handle(x):\n    out = x + 100\n    return out\n', 'tests': "assert handle(3) == 103\nassert handle(103) == 203\nprint('OK')", 'seeded': False, 'grounded': True}
ANSWER = 'def handle(x):\n    out = x + 100\n    return out\n'

SCENARIO = {
    "id": "flagcut",
    "kind": "feature",
    "batch": 11,
    "item": "F-43",
    "title": "Cut the stale flag",
    "blurb": "Remove the dead branch -- grep gate plus green hidden tests.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 11 - Feature F-43",
         "title": "Cut the stale flag",
         "subtitle": "The flag dies everywhere -- tests stay green."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b11-flagcut",
         "caption": "Status homes the type: grep gate plus reference run, no partials.",
         "assert_js": "() => !!document.querySelector('#status-b11-flagcut')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 8,
         "caption": "The rule in one line: pruned code passes, a lingering flag fails.",
         "commands": [
             ["python3", "-c",
              "import sys; sys.path.insert(0, 'tools'); "
              "from demos.flagcut import PAYLOAD, ANSWER; "
              "from groundwork import flagcut as m; "
              "from groundwork.sandbox import SandboxRunner; "
              "ex = {'payload': PAYLOAD}; r = SandboxRunner(); "
              "ok = m.grade(ex, ANSWER, r); "
              "bad = m.grade(ex, ANSWER + '# NEW_UI lives\\n', r); "
              "print('good:', ok['pass'], '-', ok['feedback']); "
              "print('bad:', bad['pass'], '-', bad['feedback'])"],
         ]},
        {"type": "chrome", "duration": 8,
         "url_path": "/due",
         "focus": "#card-{seed_card_id}",
         "caption": "The flag-cut card: stale branch on top, cleanup below.",
         "assert_js": "() => { const f = document.querySelector("
                      "\"form[action='/cards/{seed_card_id}/review']\"); "
                      "return !!f && !!f.querySelector(\"[name='answer']\") && "
                      "document.body.innerText.includes('NEW_UI'); }",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 11",
         "title": "Gone means gone.",
         "subtitle": "flagcut.py greps the corpse -- comments count too."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Plant one type-66 card (generated shape) as the sole due card."""
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
            " VALUES(?, ?, '66', ?, ?, ?, '2000-01-01T00:00:00Z')",
            (CARD_ID, row[0], FRONT, BACK, json.dumps(PAYLOAD)))
        con.commit()
        return {"seeded": True, "card_id": CARD_ID}
    finally:
        con.close()
