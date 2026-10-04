"""Feature demo: issue reproduction (F-21, type 44).

Full behavior: write a minimal failing repro from a bug report --
the sandbox executes it and a clean run fails the repro.
seed_db plants a static type-44 card (generate() bytes) as the
sole due card; terminal runs sandbox-pass / no-runner / bare-crash,
/due submits one failing assert and polls the verified verdict.
"""
from __future__ import annotations

import json
import sqlite3

CARD_ID = "demo-repro-44"

SCENARIO = {
    "id": "repro",
    "kind": "feature",
    "batch": 8,
    "item": "F-21",
    "title": "Issue reproduction",
    "blurb": ("Write a minimal repro script from a bug report; the sandbox "
              "confirms it fails."),
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 8 - Feature F-21",
         "title": "Issue reproduction",
         "subtitle": "A bug report, a blank script -- prove the failure runs."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b8-repro",
         "caption": ("Status homes the type: sandbox-run, failure required, "
                     "20 lines max."),
         "assert_js": "() => !!document.querySelector('#status-b8-repro')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": ("The rule in one line: no runner, no pass -- execution "
                     "is the proof."),
         "commands": [
             ["python3", "-c",
              "from groundwork import repro as m, sandbox as s; "
              "p = {'code': 'def ratio(a, b):\\n    return a // b', 'func': 'ratio', "
              "'bug_line': 2, 'report': 'r', 'fault': 'wrong operator', 'grounded': True, "
              "'max_lines': 20}; e = {'id': 'x', 'type': 44, 'payload': p}; "
              "print(m.grade(e, 'assert ratio(1, 2) == 0.5', s.SandboxRunner())['feedback']); "
              "print(m.grade(e, 'assert ratio(1, 2) == 0.5', None)['feedback']); "
              "print(m.grade(e, '1/0', s.SandboxRunner())['feedback'])"],
         ]},
        {"type": "chrome", "duration": 8,
         "url_path": "/due",
         "focus": "#card-{seed_card_id}",
         "caption": "The repro card: bug report plus the suspect code.",
         "assert_js": "() => { const f = document.querySelector("
                      "\"form[action='/cards/{seed_card_id}/review']\"); "
                      "return !!f && !!f.querySelector(\"input[name='answer']\") && "
                      "document.body.innerText.includes('repro'); }",
         "assert_want": "True"},
        {"type": "chrome", "duration": 14,
         "url_path": "/due",
         "caption": "One failing assert -- the sandbox confirms the bug is real.",
         "js": ["() => { const f = document.querySelector(\"form[action='/cards/{seed_card_id}/review']\"); "
                "if (!f) return 'seed-form-missing'; "
                "const inp = f.querySelector(\"input[name='answer']\"); "
                "if (!inp) return 'no-input'; inp.value = {seed_answer_js}; "
                "const conf = f.querySelector(\"input[name='confidence'][value='4']\"); "
                "if (conf) conf.checked = true; "
                "f.submit(); return 'submitted'; }"],
         "poll_js": "() => document.body.innerText.slice(0, 12000)",
         "poll_want": "Repro fails as reported",
         "poll_required": True,
         "poll_timeout": 25,
         "assert_js": "() => !!document.querySelector('.verdict-stamp') && "
                      "document.body.innerText.includes('minimal and verified')",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 8",
         "title": "Red means reproduced.",
         "subtitle": ("repro.py runs your script -- a clean run is a failed "
                      "repro.")},
    ],
}


def seed_db(db_path: str) -> dict:
    """Plant one type-44 card (generate() bytes) as the sole due card."""
    code = "def ratio(a, b):\n    return a // b"
    front = ("Bug report: `ratio` fails (wrong operator). Suspected line: 2.\n"
             "```python\n" + code + "\n```\n"
             "Write a minimal repro script (at most 20 lines) that "
             "exercises `ratio` and fails because of this bug.")
    back = ("Model repro: `assert ratio(...)  # minimal failing call` \u2014 "
            "any script under 20 lines that fails counts.")
    payload = {"code": code, "func": "ratio", "bug_line": 2,
               "report": "Bug report: `ratio` fails (wrong operator). "
                         "Suspected line: 2.",
               "fault": "wrong operator", "grounded": True, "max_lines": 20}
    answer = "assert ratio(1, 2) == 0.5"
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
            " VALUES(?, ?, '44', ?, ?, ?, '2000-01-01T00:00:00Z')",
            (CARD_ID, row[0], front, back, json.dumps(payload)))
        con.commit()
        return {"seeded": True, "card_id": CARD_ID,
                "answer_js": json.dumps(json.dumps(answer))[1:-1]}
    finally:
        con.close()
