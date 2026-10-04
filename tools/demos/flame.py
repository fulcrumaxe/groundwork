"""Feature demo: flame-graph reading (F-37, type 60).

Full behavior: read an ASCII flame graph where exactly ONE frame
dominates and name that frame plus one why-word -- widest bar wins,
not tallest or leftmost; both halves must match. seed_db plants a
static serve-dominant card (generate() bytes) as the sole due card;
the type-60 textarea takes frame+why and polls the hotspot verdict.
"""
from __future__ import annotations

import json
import sqlite3

CARD_ID = "demo-flame-60"

SCENARIO = {
    "id": "flame",
    "kind": "feature",
    "batch": 10,
    "item": "F-37",
    "title": "Flame-graph reading",
    "blurb": "Spot the frame that dominates a flame graph -- name it and say why (widest bar wins).",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 10 - Feature F-37",
         "title": "Flame-graph reading",
         "subtitle": "Width is heat -- the widest bar owns the samples."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b10-flame",
         "caption": "Status homes the type: dominant frame plus one why-word, both required.",
         "assert_js": "() => !!document.querySelector('#status-b10-flame')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "The rule in one line: frame plus widest passes, frame plus tallest fails.",
         "commands": [
             ["python3", "-c",
              "from groundwork import flame as m; "
              "ex = {'payload': {'dominant': 'serve', 'why': 'widest'}}; "
              "print(m.grade(ex, 'frame=serve\\nwhy=widest')['feedback']); "
              "print(m.grade(ex, 'frame=serve\\nwhy=tallest')['feedback'])"],
         ]},
        {"type": "chrome", "duration": 8,
         "url_path": "/due",
         "focus": "#card-{seed_card_id}",
         "caption": "The flame card: five bars summing to 100, one far wider than the rest.",
         "assert_js": "() => { const f = document.querySelector("
                      "\"form[action='/cards/{seed_card_id}/review']\"); "
                      "return !!f && !!f.querySelector(\"textarea[name='answer']\") && "
                      "document.body.innerText.includes('dominates the profile'); }",
         "assert_want": "True"},
        {"type": "chrome", "duration": 13,
         "url_path": "/due",
         "caption": "Name the frame and the why -- the verdict checks both halves.",
         "js": ["() => { const f = document.querySelector(\"form[action='/cards/{seed_card_id}/review']\"); "
                "if (!f) return 'seed-form-missing'; "
                "const ta = f.querySelector(\"textarea[name='answer']\"); "
                "if (!ta) return 'no-textarea'; ta.value = {seed_answer_js}; "
                "const conf = f.querySelector(\"input[name='confidence'][value='4']\"); "
                "if (conf) conf.checked = true; "
                "f.submit(); return 'submitted'; }"],
         "poll_js": "() => document.body.innerText.slice(0, 12000)",
         "poll_want": "widest bar",
         "poll_required": True,
         "poll_timeout": 25,
         "assert_js": "() => !!document.querySelector('.verdict-stamp') && "
                      "document.body.innerText.includes('widest bar')",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 10",
         "title": "Widest wins.",
         "subtitle": "flame.py grades frame plus why -- half answers fail."},
    ],
}

FRONT = 'One frame below dominates the profile. Reply with the dominant frame name AND one why-word (widest, tallest, leftmost).\n```\nserve  |#####################                   | 54%\nrender |#######                                 | 18%\nparse  |####                                    | 10%\nquery  |####                                    | 10%\nencode |###                                     | 8%\n```\nWidths = share of total samples.'
BACK = '`serve` dominates (54% of samples) because it is the widest bar.'
PAYLOAD = {'frames': [['serve', 54], ['render', 18], ['parse', 10], ['query', 10], ['encode', 8]], 'dominant': 'serve', 'why': 'widest', 'why_words': ['widest', 'tallest', 'leftmost'], 'grounded': True}
ANSWER = "frame=serve\nwhy=widest"


def seed_db(db_path: str) -> dict:
    """Plant one type-60 card (generate() bytes) as the sole due card."""
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
            " VALUES(?, ?, '60', ?, ?, ?, '2000-01-01T00:00:00Z')",
            (CARD_ID, row[0], FRONT, BACK, json.dumps(PAYLOAD)))
        con.commit()
        return {"seeded": True, "card_id": CARD_ID,
                "answer_js": json.dumps(json.dumps(ANSWER))[1:-1]}
    finally:
        con.close()
