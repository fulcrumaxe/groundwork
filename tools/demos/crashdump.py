"""Feature demo: crash triage (F-38, type 61).

Full behavior: read a short synthetic traceback and name the
crashing frame's function plus the fix category -- both halves
must match as isolated fields, so pasting the traceback never
passes. seed_db plants a static get_item/bounds-check card
(generate() bytes) as the sole due card; the type-61 textarea
takes frame+fix and polls the triage verdict.
"""
from __future__ import annotations

import json
import sqlite3

CARD_ID = "demo-crashdump-61"

SCENARIO = {
    "id": "crashdump",
    "kind": "feature",
    "batch": 10,
    "item": "F-38",
    "title": "Crash triage",
    "blurb": "Read a mini traceback -- name the crashing function and the fix category.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 10 - Feature F-38",
         "title": "Crash triage",
         "subtitle": "Read bottom-up -- the innermost frame raised."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b10-crashdump",
         "caption": "Status homes the type: crashing frame plus fix category, both isolated.",
         "assert_js": "() => !!document.querySelector('#status-b10-crashdump')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "The rule in one line: innermost frame passes, naming a caller fails.",
         "commands": [
             ["python3", "-c",
              "from groundwork import crashdump as m; "
              "ex = {'payload': {'crash_frame': 'get_item', 'fix': 'bounds-check'}}; "
              "print(m.grade(ex, 'frame: get_item\\nfix: bounds-check')['feedback']); "
              "print(m.grade(ex, 'serve\\nbounds-check')['feedback'])"],
         ]},
        {"type": "chrome", "duration": 8,
         "url_path": "/due",
         "focus": "#card-{seed_card_id}",
         "caption": "The triage card: four frames, one IndexError -- name the crasher.",
         "assert_js": "() => { const f = document.querySelector("
                      "\"form[action='/cards/{seed_card_id}/review']\"); "
                      "return !!f && !!f.querySelector(\"textarea[name='answer']\") && "
                      "document.body.innerText.includes('CRASHING function'); }",
         "assert_want": "True"},
        {"type": "chrome", "duration": 13,
         "url_path": "/due",
         "caption": "Name frame plus fix -- the verdict checks both halves.",
         "js": ["() => { const f = document.querySelector(\"form[action='/cards/{seed_card_id}/review']\"); "
                "if (!f) return 'seed-form-missing'; "
                "const ta = f.querySelector(\"textarea[name='answer']\"); "
                "if (!ta) return 'no-textarea'; ta.value = {seed_answer_js}; "
                "const conf = f.querySelector(\"input[name='confidence'][value='4']\"); "
                "if (conf) conf.checked = true; "
                "f.submit(); return 'submitted'; }"],
         "poll_js": "() => document.body.innerText.slice(0, 12000)",
         "poll_want": "Crash in `get_item`",
         "poll_required": True,
         "poll_timeout": 25,
         "assert_js": "() => !!document.querySelector('.verdict-stamp') && "
                      "document.body.innerText.includes('Crash in `get_item`')",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 10",
         "title": "Bottom-up wins.",
         "subtitle": "crashdump.py grades frame plus fix -- dumps never count."},
    ],
}

FRONT = 'Read this traceback. Reply with the CRASHING function (innermost frame) and the fix category — one per line (or as `frame=<name>` / `fix=<category>`).\nFix categories: guard-missing-key, zero-check, none-check, type-check, bounds-check.\n```pytb\nTraceback (most recent call last):\n  File "app.py", line 14, in serve\n    page = paginate(items, n)\n  File "app.py", line 19, in paginate\n    chunk = fetch_page(items, n)\n  File "app.py", line 25, in fetch_page\n    entry = get_item(items, n)\n  File "app.py", line 30, in get_item\n    return items[n]\nIndexError: list index out of range\n```'
BACK = 'Crash in `get_item` (IndexError: list index out of range) — fix: `bounds-check` (n runs past the end — check the length first.)'
PAYLOAD = {'traceback': 'Traceback (most recent call last):\n  File "app.py", line 14, in serve\n    page = paginate(items, n)\n  File "app.py", line 19, in paginate\n    chunk = fetch_page(items, n)\n  File "app.py", line 25, in fetch_page\n    entry = get_item(items, n)\n  File "app.py", line 30, in get_item\n    return items[n]\nIndexError: list index out of range', 'frames': [['serve', 'page = paginate(items, n)', 14], ['paginate', 'chunk = fetch_page(items, n)', 19], ['fetch_page', 'entry = get_item(items, n)', 25], ['get_item', 'return items[n]', 30]], 'crash_frame': 'get_item', 'error': 'IndexError: list index out of range', 'fix': 'bounds-check', 'fixes': ['guard-missing-key', 'zero-check', 'none-check', 'type-check', 'bounds-check'], 'grounded': True}
ANSWER = "frame: get_item\nfix: bounds-check"


def seed_db(db_path: str) -> dict:
    """Plant one type-61 card (generate() bytes) as the sole due card."""
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
            " VALUES(?, ?, '61', ?, ?, ?, '2000-01-01T00:00:00Z')",
            (CARD_ID, row[0], FRONT, BACK, json.dumps(PAYLOAD)))
        con.commit()
        return {"seeded": True, "card_id": CARD_ID,
                "answer_js": json.dumps(json.dumps(ANSWER))[1:-1]}
    finally:
        con.close()
