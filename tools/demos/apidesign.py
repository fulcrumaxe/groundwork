"""Feature demo: API-signature design (F-17, type 40).

Full behavior: design a function signature -- name, parameters with
defaults, return annotation -- for a stated requirement, graded by
AST rubric with partial credit and no sandbox. seed_db plants a
static fetch_user() card (pipeline shape) as the sole due card;
the /due beat submits the stub and polls the pass verdict.
"""
from __future__ import annotations

import json
import sqlite3

CARD_ID = "demo-apidesign-40"

SCENARIO = {
    "id": "apidesign",
    "kind": "feature",
    "batch": 7,
    "item": "F-17",
    "title": "API-signature design",
    "blurb": "Design a function signature -- name, params with defaults, return annotation.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 7 - Feature F-17",
         "title": "API-signature design",
         "subtitle": "Name it, shape it, annotate it -- the rubric scores every point."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b7-apidesign",
         "caption": "Status homes the type: AST rubric check, partial credit, no sandbox.",
         "assert_js": "() => !!document.querySelector('#status-b7-apidesign')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "The rule in one line: pass needs every rubric point -- a missing default fails.",
         "commands": [
             ["python3", "-c",
              "from groundwork import apidesign as m; "
              "ex = {'payload': {'func': 'fetch_user', 'required': ['user_id', 'limit'], 'defaults': {'limit': '10'}, 'want_return': True}}; "
              "print(m.grade(ex, 'def fetch_user(user_id, limit=10) -> dict:\\n    ...')['feedback']); "
              "print(m.grade(ex, 'def fetch_user(user_id, limit) -> dict:\\n    ...')['feedback'])"],
         ]},
        {"type": "chrome", "duration": 8,
         "url_path": "/due",
         "focus": "#card-{seed_card_id}",
         "caption": "The signature card: required user_id, optional limit, annotated return.",
         "assert_js": "() => { const f = document.querySelector("
                      "\"form[action='/cards/{seed_card_id}/review']\"); "
                      "return !!f && !!f.querySelector(\"textarea[name='answer']\") && "
                      "document.body.innerText.includes('signature'); }",
         "assert_want": "True"},
        {"type": "chrome", "duration": 13,
         "url_path": "/due",
         "caption": "Five of five rubric points -- the verdict accepts the stub.",
         "js": ["() => { const f = document.querySelector(\"form[action='/cards/{seed_card_id}/review']\"); "
                "if (!f) return 'seed-form-missing'; "
                "const ta = f.querySelector(\"textarea[name='answer']\"); "
                "if (!ta) return 'no-textarea'; ta.value = {seed_answer_js}; "
                "const conf = f.querySelector(\"input[name='confidence'][value='4']\"); "
                "if (conf) conf.checked = true; "
                "f.submit(); return 'submitted'; }"],
         "poll_js": "() => document.body.innerText.slice(0, 12000)",
         "poll_want": "Signature accepted",
         "poll_required": True,
         "poll_timeout": 25,
         "assert_js": "() => !!document.querySelector('.verdict-stamp') && "
                      "document.body.innerText.includes('Signature accepted')",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 7",
         "title": "Design the contract.",
         "subtitle": "apidesign.py grades names, defaults, returns -- a stub is enough."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Plant one type-40 card (pipeline shape) as the sole due card.

    Static literals carrying the exact bytes generate() deals (front,
    back, payload); the filmed /due answer and verdict prove the card
    live, so the seed stays stdlib-only like the rest of the module.
    """
    reference = "def fetch_user(user_id, limit=10) -> dict:\n    ..."
    front = ('Design the signature for a new function `fetch_user` that '
             'helps callers work with `fetch_user` (function in store.py).\n'
             'It must accept: `user_id` (required); `limit` (optional, '
             'default `10`).\n'
             'Annotate what it returns (`-> ...`).\n'
             'Reply with a single `def` stub — name, parameters with '
             'defaults, return annotation; the body may be `...`.')
    back = (reference + '  (model answer — any signature with the same '
            'names, defaults, and return annotation counts).')
    payload = {"func": "fetch_user", "required": ["user_id", "limit"],
               "defaults": {"limit": "10"}, "want_return": True,
               "return": "dict", "reference": reference, "grounded": True}
    answer = reference
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
            " VALUES(?, ?, '40', ?, ?, ?, '2000-01-01T00:00:00Z')",
            (CARD_ID, row[0], front, back, json.dumps(payload)))
        con.commit()
        return {"seeded": True, "card_id": CARD_ID,
                "answer_js": json.dumps(json.dumps(answer))[1:-1]}
    finally:
        con.close()
