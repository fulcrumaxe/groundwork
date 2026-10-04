"""Feature demo: memory-profile reading (F-13, type 36).

Full behavior: read a deterministic tracemalloc-style snapshot and
name the top-allocating line as file:line -- exact normalized match,
no sandbox. seed_db plants a static load_users() card (pipeline
shape) as the sole due card; the /due beat answers store.py:4 and
polls the pass verdict.
"""
from __future__ import annotations

import json
import sqlite3

CARD_ID = "demo-memprofile-36"

SCENARIO = {
    "id": "memprofile",
    "kind": "feature",
    "batch": 7,
    "item": "F-13",
    "title": "Memory-profile reading",
    "blurb": "Read a tracemalloc-style snapshot and name the top-allocating line.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 7 - Feature F-13",
         "title": "Memory-profile reading",
         "subtitle": "Rank the rows by KiB -- the hungriest line wins."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b7-memprofile",
         "caption": "Status homes the type: deterministic snapshot, exact file:line match.",
         "assert_js": "() => !!document.querySelector('#status-b7-memprofile')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "The rule in one line: the top KiB row is the answer -- re-rank on a miss.",
         "commands": [
             ["python3", "-c",
              "from groundwork import memprofile as m; "
              "ex = {'payload': {'answer': 'store.py:4', 'top_lineno': 4}}; "
              "print(m.grade(ex, 'store.py:4')['feedback']); "
              "print(m.grade(ex, 'store.py:2')['feedback'])"],
         ]},
        {"type": "chrome", "duration": 8,
         "url_path": "/due",
         "focus": "#card-{seed_card_id}",
         "caption": "The snapshot card: four frames ranked by KiB, top row darkest.",
         "assert_js": "() => { const f = document.querySelector("
                      "\"form[action='/cards/{seed_card_id}/review']\"); "
                      "return !!f && !!f.querySelector(\"input[name='answer']\") && "
                      "document.body.innerText.includes('snapshot'); }",
         "assert_want": "True"},
        {"type": "chrome", "duration": 13,
         "url_path": "/due",
         "caption": "store.py:4 -- the 199.1 KiB row out-allocates every other.",
         "js": ["() => { const f = document.querySelector(\"form[action='/cards/{seed_card_id}/review']\"); "
                "if (!f) return 'seed-form-missing'; "
                "const inp = f.querySelector(\"input[name='answer']\"); "
                "if (!inp) return 'no-input'; inp.value = {seed_answer_js}; "
                "const conf = f.querySelector(\"input[name='confidence'][value='4']\"); "
                "if (conf) conf.checked = true; "
                "f.submit(); return 'submitted'; }"],
         "poll_js": "() => document.body.innerText.slice(0, 12000)",
         "poll_want": "Top allocator found",
         "poll_required": True,
         "poll_timeout": 25,
         "assert_js": "() => !!document.querySelector('.verdict-stamp') && "
                      "document.body.innerText.includes('Top allocator found')",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 7",
         "title": "Follow the KiB.",
         "subtitle": "memprofile.py fabricates stable snapshots -- the shown rows always rank true."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Plant one type-36 card (pipeline shape) as the sole due card.

    Static literals carrying the exact bytes generate() deals (front,
    back, payload); the filmed /due answer and verdict prove the card
    live, so the seed stays stdlib-only like the rest of the module.
    """
    front = ('Read this tracemalloc-style snapshot for `load_users` and '
             'name the top-allocating line (reply `file:line`):\n```\n'
             'Traceback-free snapshot (top 6 lines by allocated KiB):\n'
             '  store.py:4 (load_users): 199.1 KiB (8 blocks) | '
             'return [r.strip() for r in rows]\n'
             '  store.py:2 (load_users): 172.3 KiB (7 blocks) | '
             'data = open(path).read()\n'
             '  store.py:3 (load_users): 128.9 KiB (6 blocks) | '
             'rows = data.splitlines()\n'
             '  store.py:1 (load_users): 40.3 KiB (3 blocks) | '
             'def load_users(path):\n```')
    back = 'store.py:4 (load_users) allocates the most (199.1 KiB).'
    payload = {
        "snapshot": [
            {"frame": "store.py:4 (load_users)", "line": 4,
             "func": "load_users", "code": "return [r.strip() for r in rows]",
             "kb": 199.1, "count": 8},
            {"frame": "store.py:2 (load_users)", "line": 2,
             "func": "load_users", "code": "data = open(path).read()",
             "kb": 172.3, "count": 7},
            {"frame": "store.py:3 (load_users)", "line": 3,
             "func": "load_users", "code": "rows = data.splitlines()",
             "kb": 128.9, "count": 6},
            {"frame": "store.py:1 (load_users)", "line": 1,
             "func": "load_users", "code": "def load_users(path):",
             "kb": 40.3, "count": 3},
        ],
        "answer": "store.py:4", "top_lineno": 4,
        "top_func": "load_users",
        "code": ("def load_users(path):\n    data = open(path).read()\n"
                 "    rows = data.splitlines()\n"
                 "    return [r.strip() for r in rows]"),
        "grounded": True,
    }
    answer = "store.py:4"
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
            " VALUES(?, ?, '36', ?, ?, ?, '2000-01-01T00:00:00Z')",
            (CARD_ID, row[0], front, back, json.dumps(payload)))
        con.commit()
        return {"seeded": True, "card_id": CARD_ID,
                "answer_js": json.dumps(json.dumps(answer))[1:-1]}
    finally:
        con.close()
