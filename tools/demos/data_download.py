"""Feature demo: personal data download (Batch 4, F-292).

Full functionality: everything about the learner in one JSON via
/export/me.json, linked from Storage on Status. Chrome's JSON viewer
clips injected captions (batch-2 precedent), so the beats film the
Status link plus the journal surface it mirrors while a terminal beat
calls the generator directly. seed_db writes one journal entry, so
the export must carry its marker.
"""
from __future__ import annotations

import sqlite3

SCENARIO = {
    "id": "data-download",
    "kind": "feature",
    "batch": 4,
    "item": "F-292",
    "title": "Personal data download",
    "blurb": "Everything about you in one JSON -- portable, private.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 4 - Feature F-292",
         "title": "Personal data download",
         "subtitle": "Everything about you in one JSON -- portable, private."},
        {"type": "chrome", "duration": 8,
         "url_path": "/status",
         "focus": "#status-storage",
         "caption": "Storage links the full personal export.",
         "assert_js": "() => { const s = document.querySelector('#status-data a'); "
                      "return s ? s.getAttribute('href') : 'missing'; }",
         "assert_want": "/export/me.json"},
        {"type": "terminal", "duration": 8,
         "caption": "The export, called directly: every table, one document.",
         "commands": [
             ["python3", "-c",
              "import json, os; from groundwork import exports as x; "
              "doc = x.personal_json(os.environ.get('DEMO_DB', 'groundwork.db')); "
              "d = json.loads(doc); "
              "print('tables:', len(d), '| reviews:', len(d['reviews']), '| journal:', len(d['journal'])); "
              "print('marker present:', '{seed_marker}' in doc)"],
         ]},
        {"type": "chrome", "duration": 9,
         "url_path": "/journal",
         "focus": "#journal article",
         "caption": "The surface behind the export: the seeded entry, listed.",
         "assert_js": "() => document.body.innerText.includes('{seed_marker}')",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 4",
         "title": "Portable, private.",
         "subtitle": "exports.py dumps every table as one sorted JSON document."},
    ],
}


def seed_db(db_path: str) -> dict:
    """One journal entry; the export must carry its marker."""
    con = sqlite3.connect(db_path)
    try:
        marker = "DataSeed42"
        con.execute("DELETE FROM journal_entries WHERE body=?", (marker,))
        con.execute("INSERT INTO journal_entries(created_day, prompt, body)"
                    " VALUES('2026-01-01', 'export seed prompt', ?)",
                    (marker,))
        con.commit()
        return {"seeded": True, "marker": marker}
    finally:
        con.close()
