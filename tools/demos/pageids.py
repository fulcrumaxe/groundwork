"""Improvement demo: per-page data-page hook registry (I-37).

Full behavior: web.page() stamps <body data-page='...'> from the
closed pageids registry on every response. seed_db deals one live
due card; Status shows the registry, terminal proves exact-match
validity, three live routes assert their distinct body hooks.
"""
from __future__ import annotations

import sqlite3

SCENARIO = {
    "id": "pageids",
    "kind": "improvement",
    "batch": 8,
    "item": "I-37",
    "title": "Per-page hooks",
    "blurb": ("Every page carries a data-page hook from a closed registry "
              "-- future pages cannot ship unstyled."),
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 8 - Improvement I-37",
         "title": "Per-page hooks",
         "subtitle": ("Every page stamps body[data-page] from a closed "
                      "registry of eight.")},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b8-pageids",
         "caption": ("Status carries the registry: eight hooks, one row "
                     "per page."),
         "assert_js": "() => !!document.querySelector('#status-b8-pageids')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "The rule in one line: exact ids pass, near-misses fail.",
         "commands": [
             ["python3", "-c",
              "from groundwork import pageids as m; "
              "print(m.valid('due'), m.valid('DUE'), m.valid('project')); "
              "print(m.extract(\"<body data-page='due'>\")); "
              "print(len(m.all_ids()))"],
         ]},
        {"type": "chrome", "duration": 8,
         "url_path": "/due",
         "caption": ("The Due queue stamps data-page='due' -- CSS targets "
                     "it exactly."),
         "assert_js": "() => document.body.getAttribute('data-page') === 'due'",
         "assert_want": "True"},
        {"type": "chrome", "duration": 8,
         "url_path": "/reviews",
         "caption": ("History stamps data-page='history' -- same shell, "
                     "different hook."),
         "assert_js": "() => document.body.getAttribute('data-page') === 'history'",
         "assert_want": "True"},
        {"type": "chrome", "duration": 6,
         "url_path": "/modules",
         "caption": ("The library stamps data-page='modules' -- detail, "
                     "reset, and 404s share it."),
         "assert_js": "() => document.body.getAttribute('data-page') === 'modules'",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 8",
         "title": "No page ships unhooked.",
         "subtitle": ("pageids.py owns the registry -- web.py stamps it on "
                      "every response.")},
    ],
}


def seed_db(db_path: str) -> dict:
    """Deal one live due card so /due films a queue, not empty state."""
    con = sqlite3.connect(db_path)
    try:
        row = con.execute(
            "SELECT id FROM cards ORDER BY due LIMIT 1").fetchone()
        if not row:
            return {"seeded": False, "reason": "no cards"}
        con.execute("UPDATE cards SET due='2000-01-01T00:00:00Z' WHERE id=?",
                    (row[0],))
        con.commit()
        return {"seeded": True, "card_id": row[0]}
    finally:
        con.close()
