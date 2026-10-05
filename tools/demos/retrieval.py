"""Feature demo: retrieval-first lessons (F-63).

Full behavior: every generated lesson level opens with a recall probe
and orders questions before prose (since Batch 16 -- empty and hostile
blocks pass through unchanged). seed_db picks a module with lessons;
the module beat asserts the first section heading is the recall probe.
"""
from __future__ import annotations

import json
import sqlite3

SCENARIO = {
    "id": "retrieval",
    "kind": "feature",
    "batch": 13,
    "item": "F-63",
    "title": "Retrieval-first lessons",
    "blurb": "Every lesson asks before it tells -- attempt first, then read.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 13 - Feature F-63",
         "title": "Retrieval-first lessons",
         "subtitle": "Every lesson asks before it tells -- attempt first, then read."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b13-retrieval",
         "caption": "Status homes the template with a live prose-first sample, enforced.",
         "assert_js": "() => !!document.querySelector('#status-b13-retrieval')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "The rule in one line: prose-first fails, enforced order passes.",
         "commands": [
             ["python3", "-c",
              "from groundwork import retrieval as m; "
              "blocks = [('prose', 'Backoff doubles the sleep.'), ('question', 'How long is the third sleep?')]; "
              "print('before:', m.check_order(blocks)); "
              "fixed = m.enforce_template(blocks); "
              "print('after:', m.check_order(fixed), '| first:', fixed[0][0])"],
         ]},
        {"type": "chrome", "duration": 12,
         "url_path": "/modules/{seed_module_id}",
         "focus": "section[id^='lesson-']",
         "caption": "Every level opens with a recall probe -- questions first, prose after.",
         "assert_js": "() => { const s = document.querySelector(\"section[id^='lesson-'] h5\"); "
                      "return !!s && s.textContent === 'Recall first'; }",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 13",
         "title": "Struggle first, then learn.",
         "subtitle": "retrieval.py enforces the template -- generation prepends the probe."},
    ],
}


def seed_db(db_path: str) -> dict:
    """First module carrying at least one generated lesson."""
    con = sqlite3.connect(db_path)
    try:
        rows = con.execute(
            "SELECT id, lessons FROM modules ORDER BY rowid").fetchall()
        for mid, lessons_json in rows:
            try:
                lessons = json.loads(lessons_json or "[]")
            except ValueError:
                continue
            if [L for L in lessons if isinstance(L, dict)]:
                return {"seeded": True, "module_id": mid}
        return {"seeded": False, "reason": "no lessons"}
    finally:
        con.close()
