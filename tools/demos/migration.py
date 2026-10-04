"""Feature demo: migration authoring (F-24, type 47).

Full behavior: rename record field name -> title with an
'untitled' default across fixture rows -- a move, never a copy.
seed_db plants a static type-47 card (generate() bytes) as the
sole due card; terminal runs exact-rows accept + old-shape
reject, /due submits compact JSON and polls the 2-row verdict.
"""
from __future__ import annotations

import json
import sqlite3

CARD_ID = "demo-migration-47"

SCENARIO = {
    "id": "migration",
    "kind": "feature",
    "batch": 8,
    "item": "F-24",
    "title": "Migration authoring",
    "blurb": ("Rename a record field with a default across fixture rows "
              "-- a move, never a copy."),
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 8 - Feature F-24",
         "title": "Migration authoring",
         "subtitle": ("name becomes title across every row -- moves, "
                      "defaults, no copies.")},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b8-migration",
         "caption": ("Status homes the type: fixture comparison, exact "
                     "rows, no sandbox."),
         "assert_js": "() => !!document.querySelector('#status-b8-migration')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": ("The rule in one line: renamed rows pass; the old "
                     "shape names its fault."),
         "commands": [
             ["python3", "-c",
              "from groundwork import migration as m; "
              "ex = {'payload': {'old_field': 'name', 'expected': [{'id': 1, 'title': "
              "'profile-alpha', 'count': 2}, {'id': 2, 'title': 'profile-beta', "
              "'count': 5}]}}; "
              "print(m.grade(ex, '[{\"id\": 1, \"title\": \"profile-alpha\", \"count\": "
              "2}, {\"id\": 2, \"title\": \"profile-beta\", \"count\": 5}]')['feedback']); "
              "print(m.grade(ex, '[{\"id\": 1, \"name\": \"profile-alpha\", \"count\": "
              "2}]')['feedback'])"],
         ]},
        {"type": "chrome", "duration": 8,
         "url_path": "/due",
         "focus": "#card-{seed_card_id}",
         "caption": "The migration card: two profile rows waiting for their rename.",
         "assert_js": "() => { const f = document.querySelector("
                      "\"form[action='/cards/{seed_card_id}/review']\"); "
                      "return !!f && !!f.querySelector(\"input[name='answer']\") && "
                      "document.body.innerText.includes('Migrate 2'); }",
         "assert_want": "True"},
        {"type": "chrome", "duration": 13,
         "url_path": "/due",
         "caption": "Renamed rows as JSON -- the verdict confirms the migration.",
         "js": ["() => { const f = document.querySelector(\"form[action='/cards/{seed_card_id}/review']\"); "
                "if (!f) return 'seed-form-missing'; "
                "const inp = f.querySelector(\"input[name='answer']\"); "
                "if (!inp) return 'no-input'; inp.value = {seed_answer_js}; "
                "const conf = f.querySelector(\"input[name='confidence'][value='4']\"); "
                "if (conf) conf.checked = true; "
                "f.submit(); return 'submitted'; }"],
         "poll_js": "() => document.body.innerText.slice(0, 12000)",
         "poll_want": "Migration correct",
         "poll_required": True,
         "poll_timeout": 25,
         "assert_js": "() => !!document.querySelector('.verdict-stamp') && "
                      "document.body.innerText.includes('Migration correct (2 rows)')",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 8",
         "title": "Move it, don't copy it.",
         "subtitle": ("migration.py compares fixtures -- renamed, defaulted, "
                      "same order.")},
    ],
}


def seed_db(db_path: str) -> dict:
    """Plant one type-47 card (generate() bytes) as the sole due card."""
    old_rows = [{"id": 1, "name": "profile-alpha", "count": 2},
                {"id": 2, "name": "profile-beta", "count": 5}]
    expected = [{"id": 1, "title": "profile-alpha", "count": 2},
                {"id": 2, "title": "profile-beta", "count": 5}]
    front = ("Migrate 2 `profile` rows: rename field `name` -> `title`; "
             "rows missing `name` get `\\'untitled\\'`. Keep `id` and `count` "
             "unchanged.\nOld rows:\n```json\n" +
             json.dumps(old_rows, indent=2) +
             "\n```\nReply with the migrated rows as a JSON list.")
    back = json.dumps(expected, indent=2)
    payload = {"func": "migrate", "old_field": "name", "new_field": "title",
               "default": "untitled", "old_rows": old_rows,
               "expected": expected,
               "reference": ("def migrate(rows):\n    return [dict(r, title=r.get('name', "
                             "'untitled')) if 'name' in r else dict(r, title='untitled') "
                             "for r in rows]"),
               "grounded": True}
    answer = json.dumps(expected, separators=(", ", ": "))
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
            " VALUES(?, ?, '47', ?, ?, ?, '2000-01-01T00:00:00Z')",
            (CARD_ID, row[0], front, back, json.dumps(payload)))
        con.commit()
        return {"seeded": True, "card_id": CARD_ID,
                "answer_js": json.dumps(json.dumps(answer))[1:-1]}
    finally:
        con.close()
