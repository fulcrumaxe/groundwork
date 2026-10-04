"""Feature demo: read-only modules API (Batch 2, F-451 first slice).

Full functionality: /api/modules.json lists every module newest-first
with concept and card counts. Chrome's JSON viewer clips injected
captions, so the beats film the Status link plus the library order it
mirrors while a terminal beat calls the generator directly. seed_db
tags the newest module summary with a marker the response must echo.
"""
from __future__ import annotations

import sqlite3

SCENARIO = {
    "id": "readonly-api",
    "kind": "feature",
    "batch": 2,
    "item": "F-451",
    "title": "Read-only modules API",
    "blurb": "Modules with concept and card counts as JSON, for dashboards.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 2 - Feature F-451",
         "title": "Read-only modules API",
         "subtitle": "Modules with concept and card counts as JSON, for dashboards."},
        {"type": "chrome", "duration": 7,
         "url_path": "/status",
         "focus": "#status-api",
         "caption": "Status documents the read-only API: modules with counts, for dashboards.",
         "assert_js": "() => !!document.querySelector('#status-api') && "
                      "!!document.querySelector(\"a[href='/api/modules.json']\")",
         "assert_want": "True"},
        {"type": "terminal", "duration": 10,
         "caption": "The generator, called directly: newest module first, counts attached.",
         "commands": [
             ["python3", "-c",
              "import json, os; from groundwork import api as a; "
              "d = json.loads(a.modules_json(os.environ.get('DEMO_DB', 'groundwork.db'))); "
              "m = d['modules'][0]; "
              "print(json.dumps(m, indent=1)); "
              "print('...', len(d['modules']), 'modules newest-first | marker:', '{seed_marker}' in m['task_summary'])"],
         ]},
        {"type": "chrome", "duration": 9,
         "url_path": "/modules",
         "caption": "The library behind the API: the marked module leads newest-first.",
         "assert_js": "() => document.querySelector('#library article h3').textContent",
         "assert_want": "{seed_marker}"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 2",
         "title": "Dashboards welcome.",
         "subtitle": "api.py serves every module with concept and card counts."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Tag the newest module summary; the API must echo the marker first."""
    con = sqlite3.connect(db_path)
    try:
        m = con.execute(
            "SELECT id FROM modules ORDER BY created_at DESC LIMIT 1").fetchone()
        if not m:
            return {"seeded": False, "reason": "no modules"}
        marker = "ApiSeed42"
        con.execute(
            "UPDATE modules SET task_summary = ? || ' ' || COALESCE(task_summary, id)"
            " WHERE id=?", (marker, m[0]))
        con.commit()
        n = con.execute("SELECT COUNT(*) FROM modules").fetchone()[0]
        return {"seeded": True, "mid": m[0], "marker": marker, "n": n}
    finally:
        con.close()
