"""Feature demo: rebase-conflict resolution (F-23, type 46).

Full behavior: resolve a planted ours/theirs conflict keeping
both sides -- markers gone, code parses, same-name def. seed_db
plants a static type-46 card (generate() bytes) as the sole due
card; terminal runs reference-accept + dropped-side partial,
/due submits the resolved function in the type-46 textarea and
polls the 5/5 verdict.
"""
from __future__ import annotations

import json
import sqlite3

CARD_ID = "demo-rebase-46"

SCENARIO = {
    "id": "rebase",
    "kind": "feature",
    "batch": 8,
    "item": "F-23",
    "title": "Rebase-conflict resolution",
    "blurb": ("Resolve a planted git-conflict block keeping both sides -- "
              "markers gone, code parses."),
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 8 - Feature F-23",
         "title": "Rebase-conflict resolution",
         "subtitle": ("Keep both sides, drop the markers -- the merge, "
                      "graded statically.")},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b8-rebase",
         "caption": ("Status homes the type: markers gone, both sides "
                     "kept, parses -- no sandbox."),
         "assert_js": "() => !!document.querySelector('#status-b8-rebase')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": ("The rule in one line: both lines kept resolves; one "
                     "dropped names the debt."),
         "commands": [
             ["python3", "-c",
              "from groundwork import rebase as m; "
              "ex = {'payload': {'func': 'total', 'ours': ['return s'], 'theirs': "
              "['return s # theirs']}}; "
              "print(m.grade(ex, 'def total(a, b):\\n    s = a + b\\n    return s\\n    return s  # theirs')['feedback']); "
              "print(m.grade(ex, 'def total(a, b):\\n    s = a + b\\n    return s')['feedback'])"],
         ]},
        {"type": "chrome", "duration": 8,
         "url_path": "/due",
         "focus": "#card-{seed_card_id}",
         "caption": "The conflict card: total() with a planted ours/theirs split.",
         "assert_js": "() => { const f = document.querySelector("
                      "\"form[action='/cards/{seed_card_id}/review']\"); "
                      "return !!f && !!f.querySelector(\"textarea[name='answer']\") && "
                      "document.body.innerText.includes('rebase conflict'); }",
         "assert_want": "True"},
        {"type": "chrome", "duration": 13,
         "url_path": "/due",
         "caption": ("Both sides kept, markers gone -- the verdict resolves "
                     "the conflict."),
         "js": ["() => { const f = document.querySelector(\"form[action='/cards/{seed_card_id}/review']\"); "
                "if (!f) return 'seed-form-missing'; "
                "const ta = f.querySelector(\"textarea[name='answer']\"); "
                "if (!ta) return 'no-textarea'; ta.value = {seed_answer_js}; "
                "const conf = f.querySelector(\"input[name='confidence'][value='4']\"); "
                "if (conf) conf.checked = true; "
                "f.submit(); return 'submitted'; }"],
         "poll_js": "() => document.body.innerText.slice(0, 12000)",
         "poll_want": "Conflict resolved",
         "poll_required": True,
         "poll_timeout": 25,
         "assert_js": "() => !!document.querySelector('.verdict-stamp') && "
                      "document.body.innerText.includes('5/5 rubric points')",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 8",
         "title": "Neither side wins outright.",
         "subtitle": ("rebase.py checks the merge -- lines kept, markers "
                      "out, code parses.")},
    ],
}


def seed_db(db_path: str) -> dict:
    """Plant one type-46 card (generate() bytes) as the sole due card."""
    conflicted = ("def total(a, b):\n    s = a + b\n<<<<<<< ours\n    return s\n"
                  "=======\n    return s  # theirs\n>>>>>>> theirs")
    reference = ("def total(a, b):\n    s = a + b\n    return s\n"
                 "    return s  # theirs")
    front = ("Resolve the rebase conflict in `total` (function in calc.py): "
             "keep BOTH sides' lines, drop the conflict markers, and reply with "
             "the full function.\n```python\n" + conflicted + "\n```")
    back = (reference + "  (model answer \u2014 markers gone, both sides kept).")
    payload = {"func": "total", "ours": ["    return s"],
               "theirs": ["    return s  # theirs"],
               "conflicted": conflicted, "reference": reference,
               "grounded": True}
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
            " VALUES(?, ?, '46', ?, ?, ?, '2000-01-01T00:00:00Z')",
            (CARD_ID, row[0], front, back, json.dumps(payload)))
        con.commit()
        return {"seeded": True, "card_id": CARD_ID,
                "answer_js": json.dumps(json.dumps(reference))[1:-1]}
    finally:
        con.close()
