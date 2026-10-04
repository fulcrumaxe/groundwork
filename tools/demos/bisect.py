"""Feature demo: bisect drill (F-22, type 45).

Full behavior: name the breaking commit in a synthetic 6-commit
history -- hash or index, off-by-one fails. seed_db plants a
static type-45 card (generate() bytes) as the sole due card;
terminal runs hash-accept + green-parent reject, /due submits
the hash and polls the first-FAIL verdict.
"""
from __future__ import annotations

import json
import sqlite3

CARD_ID = "demo-bisect-45"

SCENARIO = {
    "id": "bisect",
    "kind": "feature",
    "batch": 8,
    "item": "F-22",
    "title": "Bisect drill",
    "blurb": ("Name the breaking commit in a synthetic history -- hash or "
              "index, off-by-one fails."),
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 8 - Feature F-22",
         "title": "Bisect drill",
         "subtitle": ("Six commits, one culprit -- name the first FAIL, "
                      "hash or index.")},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b8-bisect",
         "caption": ("Status homes the type: synthetic history, exact "
                     "hash-or-index match."),
         "assert_js": "() => !!document.querySelector('#status-b8-bisect')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": ("The rule in one line: the hash passes, the green "
                     "parent fails."),
         "commands": [
             ["python3", "-c",
              "from groundwork import bisect as m; "
              "ex = {'payload': {'commits': [{'index': 0}], 'breaking_index': 1, "
              "'breaking_hash': 'ef9ff3a'}}; "
              "print(m.grade(ex, 'ef9ff3a')['feedback']); "
              "print(m.grade(ex, '0')['feedback'])"],
         ]},
        {"type": "chrome", "duration": 8,
         "url_path": "/due",
         "focus": "#card-{seed_card_id}",
         "caption": ("The regression card: one PASS, five FAILs -- which "
                     "commit broke it?"),
         "assert_js": "() => { const f = document.querySelector("
                      "\"form[action='/cards/{seed_card_id}/review']\"); "
                      "return !!f && !!f.querySelector(\"input[name='answer']\") && "
                      "document.body.innerText.includes('Bisect the regression'); }",
         "assert_want": "True"},
        {"type": "chrome", "duration": 13,
         "url_path": "/due",
         "caption": "ef9ff3a -- the verdict confirms the first FAIL.",
         "js": ["() => { const f = document.querySelector(\"form[action='/cards/{seed_card_id}/review']\"); "
                "if (!f) return 'seed-form-missing'; "
                "const inp = f.querySelector(\"input[name='answer']\"); "
                "if (!inp) return 'no-input'; inp.value = {seed_answer_js}; "
                "const conf = f.querySelector(\"input[name='confidence'][value='4']\"); "
                "if (conf) conf.checked = true; "
                "f.submit(); return 'submitted'; }"],
         "poll_js": "() => document.body.innerText.slice(0, 12000)",
         "poll_want": "is the first FAIL",
         "poll_required": True,
         "poll_timeout": 25,
         "assert_js": "() => !!document.querySelector('.verdict-stamp') && "
                      "document.body.innerText.includes('is the first FAIL')",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 8",
         "title": "Halve the history.",
         "subtitle": "bisect.py grades the hash -- off-by-one fails, no sandbox."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Plant one type-45 card (generate() bytes) as the sole due card."""
    commits = [
        {"index": 0, "hash": "3157460", "message": "fix typo", "result": "PASS"},
        {"index": 1, "hash": "ef9ff3a", "message": "tweak logging", "result": "FAIL"},
        {"index": 2, "hash": "8a0f2e8", "message": "add helper", "result": "FAIL"},
        {"index": 3, "hash": "170b622", "message": "speed up query", "result": "FAIL"},
        {"index": 4, "hash": "b9087f6", "message": "tweak logging", "result": "FAIL"},
        {"index": 5, "hash": "9bc8490", "message": "refactor loop", "result": "FAIL"},
    ]
    table = "\n".join(f"{c['index']} {c['hash']} {c['message']} [{c['result']}]"
                      for c in commits)
    front = ("Bisect the regression in `fetch_user`: the test passed, now it "
             "fails.\nName the breaking commit (hash or index).\n```\n" +
             table + "\n```")
    back = "Breaking commit: 1 (ef9ff3a) \u2014 first FAIL."
    payload = {"commits": commits, "breaking_index": 1,
               "breaking_hash": "ef9ff3a", "grounded": True}
    answer = "ef9ff3a"
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
            " VALUES(?, ?, '45', ?, ?, ?, '2000-01-01T00:00:00Z')",
            (CARD_ID, row[0], front, back, json.dumps(payload)))
        con.commit()
        return {"seeded": True, "card_id": CARD_ID,
                "answer_js": json.dumps(json.dumps(answer))[1:-1]}
    finally:
        con.close()
