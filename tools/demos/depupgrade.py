"""Feature demo: dependency upgrade (F-39, type 62).

Full behavior: read a pin bump plus a breaking-change note and
rewrite the caller from the old API shape to the new one --
graded statically (new shape in, old shape out), no network, no
packages. seed_db plants a static renamed-kwarg card (generate()
bytes) as the sole due card; /due submits the migrated caller
and polls the migration verdict.
"""
from __future__ import annotations

import json
import sqlite3

CARD_ID = "demo-depupgrade-62"

SCENARIO = {
    "id": "depupgrade",
    "kind": "feature",
    "batch": 10,
    "item": "F-39",
    "title": "Dependency upgrade",
    "blurb": "Migrate a caller across a breaking pin bump -- new-API shape in, old shape out.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 10 - Feature F-39",
         "title": "Dependency upgrade",
         "subtitle": "The pin bumped -- move the call, never copy it."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b10-depupgrade",
         "caption": "Status homes the type: new-API shape in, old-API shape out.",
         "assert_js": "() => !!document.querySelector('#status-b10-depupgrade')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "The rule in one line: migrated caller passes, the old shape names its debt.",
         "commands": [
             ["python3", "-c",
              "from types import SimpleNamespace; "
              "from groundwork import depupgrade as m; "
              "c = SimpleNamespace(node_id='n', name='checkout', kind='function', file='app.py', line=1); "
              "e = m.generate('demo-depupgrade-62', c, ['x'], {}); "
              "print(m.grade(e, e['payload']['fixed'])['feedback']); "
              "print(m.grade(e, e['payload']['old_caller'])['feedback'])"],
         ]},
        {"type": "chrome", "duration": 8,
         "url_path": "/due",
         "focus": "#card-{seed_card_id}",
         "caption": "The upgrade card: pin bump, breaking note, and the stale caller.",
         "assert_js": "() => { const f = document.querySelector("
                      "\"form[action='/cards/{seed_card_id}/review']\"); "
                      "return !!f && !!f.querySelector(\"input[name='answer']\") && "
                      "document.body.innerText.includes('Breaking change'); }",
         "assert_want": "True"},
        {"type": "chrome", "duration": 13,
         "url_path": "/due",
         "caption": "Submit the migrated caller -- the verdict checks both shapes.",
         "js": ["() => { const f = document.querySelector(\"form[action='/cards/{seed_card_id}/review']\"); "
                "if (!f) return 'seed-form-missing'; "
                "const inp = f.querySelector(\"input[name='answer']\"); "
                "if (!inp) return 'no-input'; inp.value = {seed_answer_js}; "
                "const conf = f.querySelector(\"input[name='confidence'][value='4']\"); "
                "if (conf) conf.checked = true; "
                "f.submit(); return 'submitted'; }"],
         "poll_js": "() => document.body.innerText.slice(0, 12000)",
         "poll_want": "Caller migrated",
         "poll_required": True,
         "poll_timeout": 25,
         "assert_js": "() => !!document.querySelector('.verdict-stamp') && "
                      "document.body.innerText.includes('Caller migrated')",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 10",
         "title": "Migrated, not copied.",
         "subtitle": "depupgrade.py checks the shapes -- static, no sandbox."},
    ],
}

FRONT = 'Upgrade `storelib` `storelib==1.4.2` -> `storelib==2.0.0` for `checkout`.\nBreaking change: 2.0.0 renamed the `timeout_ms` keyword (milliseconds) to `timeout` (seconds).\nRewrite the caller lines below to the new API and submit them.\n```python\npage = client.fetch(key, timeout_ms=5000)\n```'
BACK = 'Migrated caller:\n```python\npage = client.fetch(key, timeout=5)\n```'
PAYLOAD = {'lib': 'storelib', 'old_pin': 'storelib==1.4.2', 'new_pin': 'storelib==2.0.0', 'change': '2.0.0 renamed the `timeout_ms` keyword (milliseconds) to `timeout` (seconds).', 'key': 'renamed-kwarg', 'old_caller': 'page = client.fetch(key, timeout_ms=5000)', 'fixed': 'page = client.fetch(key, timeout=5)', 'new': ['client\\.fetch\\s*\\(\\s*key\\s*,\\s*timeout\\s*=\\s*5(?:\\.0)?\\s*\\)'], 'old': ['timeout_ms\\s*='], 'grounded': True}
ANSWER = "page = client.fetch(key, timeout=5)"


def seed_db(db_path: str) -> dict:
    """Plant one type-62 card (generate() bytes) as the sole due card."""
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
            " VALUES(?, ?, '62', ?, ?, ?, '2000-01-01T00:00:00Z')",
            (CARD_ID, row[0], FRONT, BACK, json.dumps(PAYLOAD)))
        con.commit()
        return {"seeded": True, "card_id": CARD_ID,
                "answer_js": json.dumps(json.dumps(ANSWER))[1:-1]}
    finally:
        con.close()
