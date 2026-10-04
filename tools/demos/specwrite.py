"""Feature demo: spec writing (F-18, type 41).

Full behavior: write acceptance criteria for fetch_user -- every
checklist point's needles must appear or the miss is named.
seed_db plants a static type-41 card (generate() bytes) as the
sole due card; terminal runs accept + named miss, /due submits
a complete set and polls the 5/5 verdict.
"""
from __future__ import annotations

import json
import sqlite3

CARD_ID = "demo-specwrite-41"

SCENARIO = {
    "id": "specwrite",
    "kind": "feature",
    "batch": 8,
    "item": "F-18",
    "title": "Spec writing",
    "blurb": ("Write acceptance criteria for a function: every checkbox "
              "-- inputs, returns, edge cases -- must appear."),
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 8 - Feature F-18",
         "title": "Spec writing",
         "subtitle": ("Acceptance criteria a reviewer could verify -- every "
                      "checkbox must appear.")},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b8-specwrite",
         "caption": ("Status homes the type: checklist grading, partial "
                     "credit, no sandbox."),
         "assert_js": "() => !!document.querySelector('#status-b8-specwrite')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": ("The rule in one line: every needle must appear; "
                     "misses are named."),
         "commands": [
             ["python3", "-c",
              "from groundwork import specwrite as m; "
              "from types import SimpleNamespace; c = SimpleNamespace(node_id='f', "
              "name='fetch_user', kind='function', file='users.py', line=1); "
              "code = 'def fetch_user(user_id, timeout=30):\\n    if not user_id:\\n        raise ValueError(1)\\n    return {}'; "
              "e = m.generate('x', c, code.splitlines(), {}); "
              "print(m.grade(e, 'fetch_user takes user_id and timeout and returns the user dict, raising an error on bad input.')['feedback']); "
              "print(m.grade(e, 'fetch_user takes user_id.')['feedback'])"],
         ]},
        {"type": "chrome", "duration": 8,
         "url_path": "/due",
         "focus": "#card-{seed_card_id}",
         "caption": "The spec card: fetch_user on the front, your criteria below.",
         "assert_js": "() => { const f = document.querySelector("
                      "\"form[action='/cards/{seed_card_id}/review']\"); "
                      "return !!f && !!f.querySelector(\"input[name='answer']\") && "
                      "document.body.innerText.includes('acceptance criteria'); }",
         "assert_want": "True"},
        {"type": "chrome", "duration": 13,
         "url_path": "/due",
         "caption": ("Criteria covering all five points -- the verdict "
                     "accepts the spec."),
         "js": ["() => { const f = document.querySelector(\"form[action='/cards/{seed_card_id}/review']\"); "
                "if (!f) return 'seed-form-missing'; "
                "const inp = f.querySelector(\"input[name='answer']\"); "
                "if (!inp) return 'no-input'; inp.value = {seed_answer_js}; "
                "const conf = f.querySelector(\"input[name='confidence'][value='4']\"); "
                "if (conf) conf.checked = true; "
                "f.submit(); return 'submitted'; }"],
         "poll_js": "() => document.body.innerText.slice(0, 12000)",
         "poll_want": "Spec accepted",
         "poll_required": True,
         "poll_timeout": 25,
         "assert_js": "() => !!document.querySelector('.verdict-stamp') && "
                      "document.body.innerText.includes('5/5 acceptance points')",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 8",
         "title": "Checklists, not vibes.",
         "subtitle": ("specwrite.py grades the words -- names, inputs, "
                      "returns, edge cases.")},
    ],
}


def seed_db(db_path: str) -> dict:
    """Plant one type-41 card (generate() bytes) as the sole due card."""
    back = ("Names `fetch_user` as the subject; Documents parameter `user_id`; "
            "Documents parameter `timeout`; States what is returned; "
            "States the error/invalid-input behavior.")
    front = ("Write acceptance criteria for `fetch_user` (function in users.py): "
             "a short checklist a reviewer could verify against an implementation.\n"
             "Cover every checkbox: " + back)
    payload = {"func": "fetch_user",
               "points": [
                   {"id": "names", "label": "Names `fetch_user` as the subject",
                    "needles": ["fetch_user"], "any_of": False},
                   {"id": "param-user_id", "label": "Documents parameter `user_id`",
                    "needles": ["user_id"], "any_of": False},
                   {"id": "param-timeout", "label": "Documents parameter `timeout`",
                    "needles": ["timeout"], "any_of": False},
                   {"id": "returns", "label": "States what is returned",
                    "needles": ["return"], "any_of": False},
                   {"id": "edge", "label": "States the error/invalid-input behavior",
                    "needles": ["error", "raise", "exception", "invalid"],
                    "any_of": True}],
               "callers": [], "reference": back, "grounded": True}
    answer = ("fetch_user takes user_id and timeout and returns the user dict, "
              "raising an error on bad input.")
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
            " VALUES(?, ?, '41', ?, ?, ?, '2000-01-01T00:00:00Z')",
            (CARD_ID, row[0], front, back, json.dumps(payload)))
        con.commit()
        return {"seeded": True, "card_id": CARD_ID,
                "answer_js": json.dumps(json.dumps(answer))[1:-1]}
    finally:
        con.close()
