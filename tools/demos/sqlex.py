"""Feature demo: SQL authoring (F-32, type 55).

Full behavior: write a SELECT from the spec -- names at qty 2-plus,
A-Z -- run live on a fresh in-memory fixture, order graded exactly
under ORDER BY. seed_db plants a static type-55 card (generate()
bytes) as the sole due card; terminal runs accept + wrong-columns
reject, /due submits the query and polls the ordered verdict.
"""
from __future__ import annotations

import json
import sqlite3

CARD_ID = "demo-sqlex-55"

SCENARIO = {
    "id": "sqlex",
    "kind": "feature",
    "batch": 9,
    "item": "F-32",
    "title": "SQL authoring",
    "blurb": "Write a SELECT from a spec -- graded on the rows it returns.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 9 - Feature F-32",
         "title": "SQL authoring",
         "subtitle": "One query -- graded on a fresh in-memory fixture."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b9-sqlex",
         "caption": "Status homes the type: spec plus fixture, sets must match.",
         "assert_js": "() => !!document.querySelector('#status-b9-sqlex')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "The rule in one line: run it on the fixture -- the set must match.",
         "commands": [
             ["python3", "-c",
              "from types import SimpleNamespace; "
              "from groundwork import sqlex as m; "
              "c = SimpleNamespace(node_id='n-record', "
              "name='record', kind='function', file='svc.py', line=1); "
              "e = m.generate('demo-sqlex-55', c, [], {}); "
              "print(m.grade(e, 'SELECT name FROM items WHERE qty >= 2 ORDER BY name')['feedback']); "
              "print(m.grade(e, 'SELECT * FROM items')['feedback'])"],
         ]},
        {"type": "chrome", "duration": 8,
         "url_path": "/due",
         "focus": "#card-{seed_card_id}",
         "caption": "The SQL card: the spec and rows on the front, your query below.",
         "assert_js": "() => { const f = document.querySelector("
                      "\"form[action='/cards/{seed_card_id}/review']\"); "
                      "return !!f && !!f.querySelector(\"input[name='answer']\") && "
                      "document.body.innerText.includes('Write a SQL SELECT'); }",
         "assert_want": "True"},
        {"type": "chrome", "duration": 13,
         "url_path": "/due",
         "caption": "Names at qty 2-plus, A-Z -- the verdict takes the query.",
         "js": ["() => { const f = document.querySelector(\"form[action='/cards/{seed_card_id}/review']\"); "
                "if (!f) return 'seed-form-missing'; "
                "const inp = f.querySelector(\"input[name='answer']\"); "
                "if (!inp) return 'no-input'; inp.value = {seed_answer_js}; "
                "const conf = f.querySelector(\"input[name='confidence'][value='4']\"); "
                "if (conf) conf.checked = true; "
                "f.submit(); return 'submitted'; }"],
         "poll_js": "() => document.body.innerText.slice(0, 12000)",
         "poll_want": "Correct result set (3 rows in order).",
         "poll_required": True,
         "poll_timeout": 25,
         "assert_js": "() => !!document.querySelector('.verdict-stamp') && "
                      "document.body.innerText.includes('Correct result set (3 rows in order).')",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 9",
         "title": "Queries, run.",
         "subtitle": "sqlex.py runs your SELECT on a fresh fixture -- sets must match."},
    ],
}

FRONT = 'Write a SQL SELECT for `record` rows.\nFixture schema:\n```sql\nCREATE TABLE items (id INTEGER PRIMARY KEY, name TEXT, qty INTEGER);\n```\nFixture rows (id, name, qty):\n```\n(1, \'record-alpha\', 2)\n(2, \'record-beta\', 6)\n(3, \'record-gamma\', 3)\n(4, \'record-delta\', 1)\n```\nTask: List the `name` of rows with `qty` >= 2, ordered by `name` A-Z (one column; row order matters).\nReply with a single SELECT query (a WITH ... SELECT is fine).'
BACK = "SELECT name FROM items WHERE qty >= 2 ORDER BY name;\n-- expected result set:\n('record-alpha')\n('record-beta')\n('record-gamma')"
PAYLOAD = {'table': 'items', 'schema': 'CREATE TABLE items (id INTEGER PRIMARY KEY, name TEXT, qty INTEGER)', 'rows': [[1, 'record-alpha', 2], [2, 'record-beta', 6], [3, 'record-gamma', 3], [4, 'record-delta', 1]], 'task': 'List the `name` of rows with `qty` >= 2, ordered by `name` A-Z (one column; row order matters).', 'reference': 'SELECT name FROM items WHERE qty >= 2 ORDER BY name', 'expected': [['record-alpha'], ['record-beta'], ['record-gamma']], 'ordered': True, 'grounded': True}
ANSWER = 'SELECT name FROM items WHERE qty >= 2 ORDER BY name'


def seed_db(db_path: str) -> dict:
    """Plant one type-55 card (generate() bytes) as the sole due card."""
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
            " VALUES(?, ?, '55', ?, ?, ?, '2000-01-01T00:00:00Z')",
            (CARD_ID, row[0], FRONT, BACK, json.dumps(PAYLOAD)))
        con.commit()
        return {"seeded": True, "card_id": CARD_ID,
                "answer_js": json.dumps(json.dumps(ANSWER))[1:-1]}
    finally:
        con.close()
