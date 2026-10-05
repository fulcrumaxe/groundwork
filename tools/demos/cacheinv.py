"""Feature demo: cache-invalidation reasoning exercise (F-46, type 69).

Full behavior: the learner studies a cached function plus four
lettered mutation paths and names every path that must bust the cache
-- and nothing else. One missed bust ships stale reads, one hot-path
bust wastes a hot cache: exact set match, no partial credit. The
single-line answer submits live through /due to a stamped verdict.
"""
from __future__ import annotations

import json
import sqlite3

CARD_ID = 'demo-cacheinv-69'
FRONT = '`lookup()` results are cached under key `lookup:{id}`. Name EVERY mutation path that must bust the cache \u2014 and bust nothing else.\nA. Update lookup via save_lookup() \u2014 changes the cached value.\nB. Delete lookup via drop_lookup() \u2014 removes the cached value.\nC. Append an audit row via log_event() \u2014 never touches lookup.\nD. Read lookup via lookup() \u2014 hot read path, served from cache.'
BACK = 'Bust A, B: the writers change or remove the cached value. Keep D cached (hot read path) and ignore the audit writer.'
PAYLOAD = {'func': 'lookup', 'cache_key': 'lookup:{id}', 'paths': [{'id': 'A', 'desc': 'Update lookup via save_lookup() \u2014 changes the cached value.'}, {'id': 'B', 'desc': 'Delete lookup via drop_lookup() \u2014 removes the cached value.'}, {'id': 'C', 'desc': 'Append an audit row via log_event() \u2014 never touches lookup.'}, {'id': 'D', 'desc': 'Read lookup via lookup() \u2014 hot read path, served from cache.'}], 'answer': ['A', 'B'], 'hot': ['D'], 'grounded': True}
ANSWER = 'A B'

SCENARIO = {
    "id": "cacheinv",
    "kind": "feature",
    "batch": 11,
    "item": "F-46",
    "title": "Cache invalidation",
    "blurb": "Name every bust -- miss one, stale reads; bust hot, waste.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 11 - Feature F-46",
         "title": "Cache invalidation",
         "subtitle": "Four paths, one exact bust set."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b11-cacheinv",
         "caption": "Status homes the type: writers bust, hot path stays, audit ignored.",
         "assert_js": "() => !!document.querySelector('#status-b11-cacheinv')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 8,
         "caption": "The rule in one line: the exact set passes, busting the hot path fails.",
         "commands": [
             ["python3", "-c",
              "import sys; sys.path.insert(0, 'tools'); "
              "from demos.cacheinv import PAYLOAD, ANSWER; "
              "from groundwork import cacheinv as m; "
              "ex = {'payload': PAYLOAD}; "
              "ok = m.grade(ex, ANSWER); bad = m.grade(ex, 'A B D'); "
              "print('good:', ok['pass'], '-', ok['feedback']); "
              "print('bad:', bad['pass'], '-', bad['feedback'])"],
         ]},
        {"type": "chrome", "duration": 8,
         "url_path": "/due",
         "focus": "#card-{seed_card_id}",
         "caption": "The invalidation card: cached function plus four lettered paths.",
         "assert_js": "() => { const f = document.querySelector("
                      "\"form[action='/cards/{seed_card_id}/review']\"); "
                      "return !!f && !!f.querySelector(\"[name='answer']\") && "
                      "document.body.innerText.includes('mutation path'); }",
         "assert_want": "True"},
        {"type": "chrome", "duration": 13,
         "url_path": "/due",
         "caption": "Bust A and B -- the writers -- and keep the hot read cached.",
         "js": ["() => { const f = document.querySelector(\"form[action='/cards/{seed_card_id}/review']\"); "
                "if (!f) return 'seed-form-missing'; "
                "const el = f.querySelector(\"[name='answer']\"); "
                "if (!el) return 'no-answer-field'; el.value = 'A B'; "
                "const conf = f.querySelector(\"input[name='confidence'][value='4']\"); "
                "if (conf) conf.checked = true; "
                "f.submit(); return 'submitted'; }"],
         "poll_js": "() => document.body.innerText.slice(0, 12000)",
         "poll_want": "Exact bust set",
         "poll_required": True,
         "poll_timeout": 25,
         "assert_js": "() => !!document.querySelector('.verdict-stamp') && "
                      "document.body.innerText.includes('Exact bust set')",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 11",
         "title": "Bust exactly right.",
         "subtitle": "cacheinv.py gates the set -- stale or wasteful both fail."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Plant one type-69 card (generated shape) as the sole due card."""
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
            " VALUES(?, ?, '69', ?, ?, ?, '2000-01-01T00:00:00Z')",
            (CARD_ID, row[0], FRONT, BACK, json.dumps(PAYLOAD)))
        con.commit()
        return {"seeded": True, "card_id": CARD_ID}
    finally:
        con.close()
