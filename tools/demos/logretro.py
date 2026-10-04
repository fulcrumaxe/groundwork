"""Feature demo: logging retrofit (F-7, type 29).

Full behavior: mark the lines that deserve a log call -- reply
id=level per marked line, checklist-graded with no sandbox. seed_db
plants a static card (pipeline shape) over a try/except snippet as
the sole due card.
"""
from __future__ import annotations

import json
import sqlite3

CARD_ID = "demo-logretro-29"

SCENARIO = {
    "id": "logretro",
    "kind": "feature",
    "batch": 6,
    "item": "F-7",
    "title": "Logging retrofit",
    "blurb": "Name the right log level for each marked line.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 6 - Feature F-7",
         "title": "Logging retrofit",
         "subtitle": "Entry is debug, a caught problem warns, a raise errors."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b6-logretro",
         "caption": "Status homes the type: checklist-graded, no sandbox needed.",
         "assert_js": "() => !!document.querySelector('#status-b6-logretro')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "The rule in one line: entry/exit debug, caught warns, raised errors.",
         "commands": [
             ["python3", "-c",
              "from groundwork import logretro as m; "
              "snip = ['def f():', '    try:', '        g()', '    except E:', '        raise F()', '    return 1']; "
              "print([(c['id'], c['kind'], c['level']) for c in m.pick_lines(snip)])"],
         ]},
        {"type": "chrome", "duration": 8,
         "url_path": "/due",
         "caption": "The logging card: numbered snippet, marked lines, levels below.",
         "assert_js": "() => { const f = document.querySelector("
                      "\"form[action='/cards/{seed_card_id}/review']\"); "
                      "return !!f && !!f.querySelector(\"textarea[name='answer']\") && "
                      "document.body.innerText.includes('id=level'); }",
         "assert_want": "True"},
        {"type": "chrome", "duration": 13,
         "url_path": "/due",
         "caption": "Place each level -- every marked line must match.",
         "js": ["() => { const f = document.querySelector(\"form[action='/cards/{seed_card_id}/review']\"); "
                "if (!f) return 'seed-form-missing'; "
                "const ta = f.querySelector(\"textarea[name='answer']\"); "
                "if (!ta) return 'no-textarea'; ta.value = {seed_answer_js}; "
                "const conf = f.querySelector(\"input[name='confidence'][value='4']\"); "
                "if (conf) conf.checked = true; "
                "f.submit(); return 'submitted'; }"],
         "poll_js": "() => document.body.innerText.slice(0, 12000)",
         "poll_want": "Every line logged",
         "poll_required": True,
         "poll_timeout": 25,
         "assert_js": "() => !!document.querySelector('.verdict-stamp') && "
                      "document.body.innerText.includes('Every line logged')",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 6",
         "title": "Log the right moment.",
         "subtitle": "logretro.py classifies lines -- you name their levels."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Plant one type-29 card (pipeline shape) as the sole due card.

    Static literals carrying the exact bytes generate() deals (front,
    back, payload); the filmed /due answer and verdict prove the card
    live, so the seed stays stdlib-only like the rest of the module.
    """
    front = 'Add logging at the right lines: reply `id=level` (one per line) using debug/info/warning/error.\n```\n1: def serve_order(order):  # (item 0)\n2:     try:\n3:         charge(order)\n4:     except CardError:  # (item 1)\n5:         refund(order)\n6:         raise RetryLater()  # (item 2)\n7:     return receipt(order)  # (item 3)\n```'
    back = '0=debug\n1=warning\n2=error\n3=debug'
    payload = {'checklist': [{'id': 0, 'line': 1, 'kind': 'entry', 'level': 'debug'}, {'id': 1, 'line': 4, 'kind': 'except', 'level': 'warning'}, {'id': 2, 'line': 6, 'kind': 'raise', 'level': 'error'}, {'id': 3, 'line': 7, 'kind': 'exit', 'level': 'debug'}], 'levels': ['debug', 'info', 'warning', 'error'], 'grounded': True}
    answer = '0=debug\n1=warning\n2=error\n3=debug'
    con = sqlite3.connect(db_path)
    try:
        row = con.execute(
            "SELECT id FROM concepts ORDER BY rowid LIMIT 1").fetchone()
        if not row:
            return {"seeded": False, "reason": "no concepts"}
        con.execute("UPDATE cards SET due='2030-01-01T00:00:00Z'")
        con.execute("DELETE FROM reviews WHERE card_id=?", ('demo-logretro-29',))
        con.execute(
            "INSERT OR REPLACE INTO cards(id, concept_id, exercise_type,"
            " front, back, payload, due)"
            " VALUES(?, ?, '29', ?, ?, ?, '2000-01-01T00:00:00Z')",
            ('demo-logretro-29', row[0], front, back, json.dumps(payload)))
        con.commit()
        return {"seeded": True, "card_id": 'demo-logretro-29',
                "answer_js": json.dumps(json.dumps(answer))[1:-1]}
    finally:
        con.close()
