"""Feature demo: storage meter (Batch 3, I-238).

Full functionality: the database file size plus per-module concept,
card, and review counts on Status (storage.section_html), backed by
storage.usage(). seed_db tags the newest module summary with a
marker and plants three reviews on one of its cards, so the Status
table and the usage() call must echo the manipulated row.
"""
from __future__ import annotations

import sqlite3

SCENARIO = {
    "id": "storage-meter",
    "kind": "feature",
    "batch": 3,
    "item": "I-238",
    "title": "Storage meter",
    "blurb": "Database size and per-module rows -- growth never surprises.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 3 - Feature I-238",
         "title": "Storage meter",
         "subtitle": "Database size and per-module rows -- growth never surprises."},
        {"type": "chrome", "duration": 8,
         "url_path": "/status",
         "js": ["() => { const h = document.querySelector('#status-storage'); "
                "if (!h) return 'no-storage'; let n = h.nextElementSibling; "
                "let done = 'no-table'; "
                "while (n && !/^H[23]$/.test(n.tagName)) { "
                "if (n.tagName === 'TABLE') { n.style.tableLayout = 'fixed'; "
                "n.style.width = '100%'; n.style.fontSize = '14px'; "
                "n.querySelectorAll('td,th').forEach(c => { c.style.wordBreak = 'break-word'; "
                "c.style.overflowWrap = 'anywhere'; c.style.whiteSpace = 'normal'; "
                "c.style.padding = '4px 6px'; }); "
                "n.querySelectorAll('a').forEach(a => { a.style.whiteSpace = 'normal'; }); "
                "done = 'sized'; } "
                "n = n.nextElementSibling; } return done; }"],
         "focus": "#status-storage",
         "caption": "Storage names the database file size and per-module rows.",
         "assert_js": "() => !!document.querySelector('#status-storage') && "
                      "document.body.innerText.includes('{seed_marker}')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 9,
         "caption": "The meter, called directly: file size plus the marked module row.",
         "commands": [
             ["python3", "-c",
              "import json, os; from groundwork import storage as s; "
              "info = s.usage(os.environ.get('DEMO_DB', 'groundwork.db')); "
              "print('file:', info['human'], '(' + str(info['bytes']) + ' bytes)'); "
              "print('disputes on record:', info['disputes']); "
              "m = [r for r in info['modules'] if '{seed_marker}' in r['task_summary']][0]; "
              "print(json.dumps(m, indent=1))"],
         ]},
        {"type": "chrome", "duration": 8,
         "url_path": "/modules/{seed_mid}",
         "caption": "The counted module itself: the marked summary behind the meter row.",
         "assert_js": "() => document.body.innerText.includes('{seed_marker}')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 5,
         "caption": "Human units from bytes to gigabytes, one helper.",
         "commands": [
             ["python3", "-c",
              "from groundwork import storage as s; "
              "print(s._human(500), '|', s._human(2048), '|', s._human(3 * 1024 * 1024))"],
         ]},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 3",
         "title": "Growth never surprises.",
         "subtitle": "storage.py meters the file and every module row."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Tag the newest module; plant three reviews on one of its cards."""
    con = sqlite3.connect(db_path)
    try:
        m = con.execute(
            "SELECT id FROM modules ORDER BY created_at DESC LIMIT 1").fetchone()
        if not m:
            return {"seeded": False, "reason": "no modules"}
        mid = m[0]
        marker = "StoreSeed42"
        con.execute(
            "UPDATE modules SET task_summary = ? || ' ' || COALESCE(task_summary, id)"
            " WHERE id=?", (marker, mid))
        card = con.execute(
            "SELECT cards.id FROM cards JOIN concepts"
            " ON concepts.id = cards.concept_id"
            " WHERE concepts.module_id=? LIMIT 1", (mid,)).fetchone()
        planted = 0
        if card:
            for i in range(3):
                con.execute(
                    "INSERT INTO reviews(card_id, grade, confidence, submission)"
                    " VALUES(?, 4, 5, ?)", (card[0], f"storage seed {i}"))
                planted += 1
        con.commit()
        return {"seeded": True, "mid": mid, "marker": marker,
                "planted": planted}
    finally:
        con.close()
