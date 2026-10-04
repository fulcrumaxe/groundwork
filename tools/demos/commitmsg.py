"""Feature demo: commit-message authorship (F-19, type 42).

Full behavior: summarize a diff as one imperative subject naming
the what + why -- a 4-point rubric grades verb, length, what,
why. seed_db plants a static type-42 card (generate() bytes) as
the sole due card; terminal runs accept + past-tense reject,
/due submits the subject and polls the 4/4 verdict.
"""
from __future__ import annotations

import json
import sqlite3

CARD_ID = "demo-commitmsg-42"

SCENARIO = {
    "id": "commitmsg",
    "kind": "feature",
    "batch": 8,
    "item": "F-19",
    "title": "Commit-message authorship",
    "blurb": ("Summarize a diff as a commit message: imperative subject "
              "naming the what and the why."),
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 8 - Feature F-19",
         "title": "Commit-message authorship",
         "subtitle": "One imperative line: name the what and the why."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b8-commitmsg",
         "caption": "Status homes the type: imperative, 72 chars, what + why.",
         "assert_js": "() => !!document.querySelector('#status-b8-commitmsg')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": ("The rule in one line: four rubric points, every one "
                     "required."),
         "commands": [
             ["python3", "-c",
              "from groundwork import commitmsg as m; "
              "from types import SimpleNamespace; c = SimpleNamespace(node_id='f', "
              "name='fetch_user', kind='function', file='users.py', line=1); "
              "d = ['-def fetch_user(uid):', '+def fetch_user(user_id, timeout=30):', ' retry on timeout for flaky auth']; "
              "e = m.generate('x', c, d, {'decisions': [{'note': 'flaky auth retry'}]}); "
              "print(m.grade(e, 'Update fetch for flaky auth')['feedback']); "
              "print(m.grade(e, 'Updated fetch for retry')['feedback'])"],
         ]},
        {"type": "chrome", "duration": 8,
         "url_path": "/due",
         "focus": "#card-{seed_card_id}",
         "caption": "The commit card: the diff on the front, your subject below.",
         "assert_js": "() => { const f = document.querySelector("
                      "\"form[action='/cards/{seed_card_id}/review']\"); "
                      "return !!f && !!f.querySelector(\"input[name='answer']\") && "
                      "document.body.innerText.includes('commit message'); }",
         "assert_want": "True"},
        {"type": "chrome", "duration": 13,
         "url_path": "/due",
         "caption": ("Imperative, short, what + why -- the verdict takes "
                     "the message."),
         "js": ["() => { const f = document.querySelector(\"form[action='/cards/{seed_card_id}/review']\"); "
                "if (!f) return 'seed-form-missing'; "
                "const inp = f.querySelector(\"input[name='answer']\"); "
                "if (!inp) return 'no-input'; inp.value = {seed_answer_js}; "
                "const conf = f.querySelector(\"input[name='confidence'][value='4']\"); "
                "if (conf) conf.checked = true; "
                "f.submit(); return 'submitted'; }"],
         "poll_js": "() => document.body.innerText.slice(0, 12000)",
         "poll_want": "Commit message accepted",
         "poll_required": True,
         "poll_timeout": 25,
         "assert_js": "() => !!document.querySelector('.verdict-stamp') && "
                      "document.body.innerText.includes('4/4 rubric points')",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 8",
         "title": "Subjects that explain.",
         "subtitle": "commitmsg.py grades the line -- verb, length, what, why."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Plant one type-42 card (generate() bytes) as the sole due card."""
    diff = ("-def fetch_user(uid):\n+def fetch_user(user_id, timeout=30):\n"
            " retry on timeout for flaky auth")
    front = ("Summarize this change to `fetch_user` as a commit message.\n"
             "Subject line: imperative, <= 72 chars, naming WHAT changed "
             "(`fetch`, `user`, `users`) and WHY (`flaky`, `auth`).\n"
             "```diff\n" + diff + "\n```")
    back = ("Update fetch for flaky  (model answer \u2014 any imperative subject "
            "<=72 chars naming the what + why counts).")
    payload = {"diff": diff, "what": ["fetch", "user", "users"],
               "why_keywords": ["flaky", "auth"],
               "reference": "Update fetch for flaky", "grounded": True}
    answer = "Update fetch for flaky auth"
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
            " VALUES(?, ?, '42', ?, ?, ?, '2000-01-01T00:00:00Z')",
            (CARD_ID, row[0], front, back, json.dumps(payload)))
        con.commit()
        return {"seeded": True, "card_id": CARD_ID,
                "answer_js": json.dumps(json.dumps(answer))[1:-1]}
    finally:
        con.close()
