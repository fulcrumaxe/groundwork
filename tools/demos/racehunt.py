"""Feature demo: race-hunt (F-14, type 37).

Full behavior: spot the shared mutable state in a numbered snippet --
name the exact line plus the fix (local copy, lock, or parameter),
with no threads ever spawned. seed_db plants a static record()
card (pipeline shape) as the sole due card; the /due beat submits
line 4 plus a local-copy fix and polls the pass verdict.
"""
from __future__ import annotations

import json
import sqlite3

CARD_ID = "demo-racehunt-37"

SCENARIO = {
    "id": "racehunt",
    "kind": "feature",
    "batch": 7,
    "item": "F-14",
    "title": "Race-hunt",
    "blurb": "Spot the shared mutable state: name the line plus the fix -- local copy, lock, or parameter.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 7 - Feature F-14",
         "title": "Race-hunt",
         "subtitle": "No threads spawned -- reason from the numbered code alone."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b7-racehunt",
         "caption": "Status homes the type: line match plus fix checklist, both halves required.",
         "assert_js": "() => !!document.querySelector('#status-b7-racehunt')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "The rule in one line: the global plus its mutation is the site -- then name the fix.",
         "commands": [
             ["python3", "-c",
              "from groundwork import racehunt as m; "
              "code = 'seen = []\\n\\ndef record(x):\\n    global seen\\n    seen.append(x)\\n    return len(seen)'; "
              "print(m.find_sites(code)[0]); "
              "print(m.grade({'payload': {'shared_line': 4, 'symbol': 'seen'}}, 'line: 4\\nfix: copy into a local')['feedback'])"],
         ]},
        {"type": "chrome", "duration": 8,
         "url_path": "/due",
         "focus": "#card-{seed_card_id}",
         "caption": "The race card: numbered snippet, one shared global hiding inside.",
         "assert_js": "() => { const f = document.querySelector("
                      "\"form[action='/cards/{seed_card_id}/review']\"); "
                      "return !!f && !!f.querySelector(\"textarea[name='answer']\") && "
                      "document.body.innerText.includes('shared-state'); }",
         "assert_want": "True"},
        {"type": "chrome", "duration": 13,
         "url_path": "/due",
         "caption": "Line 4, copy into a local -- the verdict accepts line plus fix.",
         "js": ["() => { const f = document.querySelector(\"form[action='/cards/{seed_card_id}/review']\"); "
                "if (!f) return 'seed-form-missing'; "
                "const ta = f.querySelector(\"textarea[name='answer']\"); "
                "if (!ta) return 'no-textarea'; ta.value = {seed_answer_js}; "
                "const conf = f.querySelector(\"input[name='confidence'][value='4']\"); "
                "if (conf) conf.checked = true; "
                "f.submit(); return 'submitted'; }"],
         "poll_js": "() => document.body.innerText.slice(0, 12000)",
         "poll_want": "fix accepted",
         "poll_required": True,
         "poll_timeout": 25,
         "assert_js": "() => !!document.querySelector('.verdict-stamp') && "
                      "document.body.innerText.includes('fix accepted')",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 7",
         "title": "Copy it local.",
         "subtitle": "racehunt.py detects globals, caches, class state -- the fix is copy, lock, or parameter."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Plant one type-37 card (pipeline shape) as the sole due card.

    Static literals carrying the exact bytes generate() deals (front,
    back, payload); the filmed /due answer and verdict prove the card
    live, so the seed stays stdlib-only like the rest of the module.
    """
    code = ("seen = []\n\ndef record(x):\n    global seen\n"
            "    seen.append(x)\n    return len(seen)")
    numbered = ("1: seen = []\n2: \n3: def record(x):\n4:     global seen\n"
                "5:     seen.append(x)\n6:     return len(seen)")
    front = ('Spot the shared-state race in `record`: which line reads or '
             'writes shared mutable state (module global, shared cache, or '
             'mutable class attribute)? Reply with the line number plus '
             'your fix — a local copy, a lock, or a parameter. No threads '
             'are spawned; reason from the code alone.\n```python\n' +
             numbered + '\n```')
    back = ('Line 4: shared module-global `seen`. Fix: copy it into a '
            'local (or guard it with a lock, or pass it as a parameter).')
    payload = {"code": code, "numbered": numbered, "shared_line": 4,
               "symbol": "seen", "kind": "module-global",
               "fix_keywords": ["copy", "deepcopy", "local", "lock",
                                "parameter", "argument", "inject",
                                "immutable", "tuple", "frozen"],
               "grounded": True}
    answer = "line: 4\nfix: copy into a local"
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
            " VALUES(?, ?, '37', ?, ?, ?, '2000-01-01T00:00:00Z')",
            (CARD_ID, row[0], front, back, json.dumps(payload)))
        con.commit()
        return {"seeded": True, "card_id": CARD_ID,
                "answer_js": json.dumps(json.dumps(answer))[1:-1]}
    finally:
        con.close()
