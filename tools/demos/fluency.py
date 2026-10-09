"""Feature demo: reading fluency (F-75, type 79).

Full behavior: skim a snippet on a 90s budget, form a one-line gist,
then verify it against three probes (keyword, locate, owner) --
reply with the probe letters, all correct passes with partial credit
per probe. seed_db plants the generated fluency card as the sole due
card; the /due beat answers the letters and polls the verified-gist
verdict.
"""
from __future__ import annotations

import json
import sqlite3

CARD_ID = "demo-b18-fluency"
NUMBERED = "1: def add(a, b):\n2:     total = a + b\n3:     return total"
FRONT = ("Skim the snippet below (90s budget), form a one-line gist, then verify it: reply with "
         "the 3 probe letters in order (e.g. `BCA`). All correct passes; partial credit per probe.\n"
         "```\n" + NUMBERED + "\n```\n"
         "Probe 1: Which of these tokens appears in the snippet? (A=import, B=if, C=return)\n"
         "Probe 2: Which line mentions `add`? (A=line 3, B=line 2, C=line 1)\n"
         "Probe 3: Which file does this snippet come from? (A=another module, B=the test suite, C=calc.py)")
BACK = "CCC \u2014 Probe 1: return; Probe 2: line 1; Probe 3: calc.py"
PROBES = [{"q": "Which of these tokens appears in the snippet?",
           "choices": ["import", "if", "return"], "answer": "return"},
          {"q": "Which line mentions `add`?",
           "choices": ["line 3", "line 2", "line 1"], "answer": "line 1"},
          {"q": "Which file does this snippet come from?",
           "choices": ["another module", "the test suite", "calc.py"],
           "answer": "calc.py"}]
PAYLOAD = {"lines": NUMBERED, "probes": PROBES, "key": "CCC",
           "time_s": 90, "reference": "CCC", "grounded": True}
ANSWER = "CCC"

SCENARIO = {
    "id": "fluency",
    "kind": "feature",
    "batch": 18,
    "item": "F-75",
    "title": "Reading fluency",
    "blurb": "Skim a snippet on a 90s budget, gist it in one line, then verify with three probes -- keyword, locate, owner.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 18 - Feature F-75",
         "title": "Reading fluency",
         "subtitle": "Skim, gist, verify -- three probes check the one-line gist."},
        {"type": "terminal", "duration": 7,
         "caption": "The verify in one call: all letters green, or the wrong probe named.",
         "commands": [
             ["python3", "-c",
              "from groundwork import fluency as m; "
              "ex = {'payload': {'probes': [{}, {}, {}], 'key': 'CCC'}}; "
              "print(m.grade(ex, 'CCC')['feedback']); "
              "print(m.grade(ex, 'CCA')['feedback'])"],
         ]},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b18-fluency",
         "caption": "Status homes the type: keyword, locate, owner -- new understand tier.",
         "assert_js": "() => !!document.querySelector('#status-b18-fluency')",
         "assert_want": "True"},
        {"type": "chrome", "duration": 8,
         "url_path": "/due",
         "focus": "#card-{seed_card_id} h3",
         "caption": "The fluency card: skim, gist, then three lettered probes.",
         "assert_js": "() => { const f = document.querySelector("
                      "\"form[action='/cards/{seed_card_id}/review']\"); "
                      "return !!f && document.body.innerText.includes('probe letters'); }",
         "assert_want": "True"},
        {"type": "chrome", "duration": 13,
         "url_path": "/due",
         "caption": "Three letters, all green -- the gist holds.",
         "js": ["() => { const f = document.querySelector(\"form[action='/cards/{seed_card_id}/review']\"); "
                "if (!f) return 'seed-form-missing'; "
                "f.querySelectorAll(\"input[name='answer']\").forEach(i => i.value = {seed_answer_js}); "
                "const conf = f.querySelector(\"input[name='confidence'][value='4']\"); "
                "if (conf) conf.checked = true; "
                "f.submit(); return 'submitted'; }"],
         "poll_js": "() => document.body.innerText.slice(0, 12000)",
         "poll_want": "probes green",
         "poll_required": True,
         "poll_timeout": 25,
         "assert_js": "() => !!document.querySelector('.verdict-stamp') && "
                      "document.body.innerText.includes('Gist verified')",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 18",
         "title": "Skim, then check.",
         "subtitle": "fluency.py probes the gist -- keyword, line, file."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Plant the generated type-79 card (pipeline shape) as the sole due card."""
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
            " VALUES(?, ?, '79', ?, ?, ?, '2000-01-01T00:00:00Z')",
            (CARD_ID, row[0], FRONT, BACK, json.dumps(PAYLOAD)))
        con.commit()
        return {"seeded": True, "card_id": CARD_ID,
                "answer_js": json.dumps(json.dumps(ANSWER))[1:-1]}
    finally:
        con.close()
