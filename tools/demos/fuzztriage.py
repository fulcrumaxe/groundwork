"""Feature demo: fuzz-target triage (F-11, type 34).

Full behavior: a fuzzer crashed the function with a reported input --
write the minimal reproducing call and name the crashing line, and
either half counts. seed_db plants a static ratio() card (pipeline
shape) as the sole due card; the /due beat submits call plus line
and polls the pass verdict.
"""
from __future__ import annotations

import json
import sqlite3

CARD_ID = "demo-fuzztriage-34"

SCENARIO = {
    "id": "fuzztriage",
    "kind": "feature",
    "batch": 7,
    "item": "F-11",
    "title": "Fuzz-target triage",
    "blurb": "Reproduce a fuzzer-found crash: write the minimal failing call and name the crashing line.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 7 - Feature F-11",
         "title": "Fuzz-target triage",
         "subtitle": "The fuzzer found the crash -- you shrink it to the failing call and line."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b7-fuzztriage",
         "caption": "Status homes the type: exact crash call or crash line -- either half counts.",
         "assert_js": "() => !!document.querySelector('#status-b7-fuzztriage')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "The rule in one line: call digits are arguments, never line numbers.",
         "commands": [
             ["python3", "-c",
              "from groundwork import fuzztriage as m; "
              "ex = {'payload': {'code': 'def ratio(a, b):\\n    return a / b', 'func': 'ratio', 'crash_call': 'ratio(4, 0)', 'crash_line': 2}}; "
              "print(m.grade(ex, 'ratio(4, 0) @ line 2')['feedback']); "
              "print(m.grade(ex, 'ratio(1, 1)')['feedback'])"],
         ]},
        {"type": "chrome", "duration": 8,
         "url_path": "/due",
         "focus": "#card-{seed_card_id}",
         "caption": "The crasher card: fuzzer input on the front, your repro below.",
         "assert_js": "() => { const f = document.querySelector("
                      "\"form[action='/cards/{seed_card_id}/review']\"); "
                      "return !!f && !!f.querySelector(\"textarea[name='answer']\") && "
                      "document.body.innerText.includes('fuzzer'); }",
         "assert_want": "True"},
        {"type": "chrome", "duration": 13,
         "url_path": "/due",
         "caption": "Call plus line -- the verdict confirms the crasher reproduces.",
         "js": ["() => { const f = document.querySelector(\"form[action='/cards/{seed_card_id}/review']\"); "
                "if (!f) return 'seed-form-missing'; "
                "const ta = f.querySelector(\"textarea[name='answer']\"); "
                "if (!ta) return 'no-textarea'; ta.value = {seed_answer_js}; "
                "const conf = f.querySelector(\"input[name='confidence'][value='4']\"); "
                "if (conf) conf.checked = true; "
                "f.submit(); return 'submitted'; }"],
         "poll_js": "() => document.body.innerText.slice(0, 12000)",
         "poll_want": "reproduced at the right line",
         "poll_required": True,
         "poll_timeout": 25,
         "assert_js": "() => !!document.querySelector('.verdict-stamp') && "
                      "document.body.innerText.includes('reproduced at the right line')",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 7",
         "title": "Shrink the crash.",
         "subtitle": "fuzztriage.py matches the call or the line -- never a digit inside the call."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Plant one type-34 card (pipeline shape) as the sole due card.

    Static literals carrying the exact bytes generate() deals (front,
    back, payload); the filmed /due answer and verdict prove the card
    live, so the seed stays stdlib-only like the rest of the module.
    """
    code = "def ratio(a, b):\n    return a / b"
    front = ('A fuzzer crashed `ratio` with this input: `ratio(4, 0)` '
             '(ZeroDivisionError).\n```python\n' + code +
             '\n```\nReply with the minimal reproducing call and '
             'the crashing line number.')
    back = '`ratio(4, 0)` crashes at line 2 (ZeroDivisionError).'
    payload = {"code": code, "func": "ratio", "crash_call": "ratio(4, 0)",
               "reported": "ratio(4, 0)", "crash_line": 2,
               "fault": "ZeroDivisionError", "grounded": True}
    answer = "ratio(4, 0) @ line 2"
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
            " VALUES(?, ?, '34', ?, ?, ?, '2000-01-01T00:00:00Z')",
            (CARD_ID, row[0], front, back, json.dumps(payload)))
        con.commit()
        return {"seeded": True, "card_id": CARD_ID,
                "answer_js": json.dumps(json.dumps(answer))[1:-1]}
    finally:
        con.close()
