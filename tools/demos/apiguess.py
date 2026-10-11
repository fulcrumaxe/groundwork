"""Feature demo: API guessing (F-77, type 81).

Full behavior: commit to one stdlib call from four choices, then
verify against the recorded synopsis and docs pointer -- exact-choice
grading, no sandbox. seed_db plants the generated api-guess card as
the sole due card; the /due beat commits the right call and polls
the docs-confirm verdict.
"""
from __future__ import annotations

import json
import sqlite3

CARD_ID = "demo-b19-apiguess"
FRONT = ("Task: turn a JSON string into Python objects. Commit to one call "
         "(A) json.loads / B) re.search / C) os.path.join / D) pathlib.Path), "
         "then verify against the synopsis and docs pointer.")
BACK = "json.loads: Parse a JSON string into Python objects. (library/json)"
PAYLOAD = {"target": "json.loads", "module": "json",
           "choices": ["json.loads", "re.search", "os.path.join",
                       "pathlib.Path"],
           "answer": "json.loads",
           "synopsis": "Parse a JSON string into Python objects.",
           "docs": "library/json", "grounded": True}
ANSWER = "json.loads"

SCENARIO = {
    "id": "apiguess",
    "kind": "feature",
    "batch": 19,
    "item": "F-77",
    "title": "API guessing",
    "blurb": "Predict which stdlib call fits the task, then check the docs synopsis -- commit before you verify.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 19 - Feature F-77",
         "title": "API guessing",
         "subtitle": "Commit to one call from four, then verify against the synopsis."},
        {"type": "terminal", "duration": 7,
         "caption": "Exact-choice grading: the right call wins, a wrong one names the fit, silence commits nothing.",
         "commands": [
             ["python3", "-c",
              "from groundwork import apiguess as m; "
              "ex = {'payload': {'answer': 'json.loads', 'docs': 'library/json'}}; "
              "print(m.grade(ex, 'json.loads')['feedback']); "
              "print(m.grade(ex, 're.search')['feedback']); "
              "print(m.grade(ex, '')['feedback'])"],
         ]},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b19-apiguess",
         "caption": "Status homes the type: predict the call, verify against synopsis and docs.",
         "assert_js": "() => !!document.querySelector('#status-b19-apiguess')",
         "assert_want": "True"},
        {"type": "chrome", "duration": 8,
         "url_path": "/due",
         "focus": "#card-{seed_card_id} h3",
         "caption": "The guessing card: one task, four calls, commit before you verify.",
         "assert_js": "() => { const f = document.querySelector("
                     "\"form[action='/cards/{seed_card_id}/review']\"); "
                     "return !!f && document.body.innerText.includes('Commit to one call'); }",
         "assert_want": "True"},
        {"type": "chrome", "duration": 13,
         "url_path": "/due",
         "caption": "The right call committed -- the synopsis and docs confirm it.",
         "js": ["() => { const f = document.querySelector(\"form[action='/cards/{seed_card_id}/review']\"); "
                "if (!f) return 'seed-form-missing'; "
                "f.querySelectorAll(\"input[name='answer']\").forEach(i => i.value = {seed_answer_js}); "
                "const conf = f.querySelector(\"input[name='confidence'][value='4']\"); "
                "if (conf) conf.checked = true; "
                "f.submit(); return 'submitted'; }"],
         "poll_js": "() => document.body.innerText.slice(0, 12000)",
         "poll_want": "Right call",
         "poll_required": True,
         "poll_timeout": 25,
         "assert_js": "() => !!document.querySelector('.verdict-stamp') && "
                      "document.body.innerText.includes('docs confirm it')",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 19",
         "title": "Commit, then verify.",
         "subtitle": "apiguess.py grades the exact choice -- the synopsis is the check."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Plant the generated type-81 card (pipeline shape) as the sole due card."""
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
            " VALUES(?, ?, '81', ?, ?, ?, '2000-01-01T00:00:00Z')",
            (CARD_ID, row[0], FRONT, BACK, json.dumps(PAYLOAD)))
        con.commit()
        return {"seeded": True, "card_id": CARD_ID,
                "answer_js": json.dumps(json.dumps(ANSWER))[1:-1]}
    finally:
        con.close()
