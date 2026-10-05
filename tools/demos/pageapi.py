"""Feature demo: pagination-retrofit exercise (F-45, type 68).

Full behavior: the learner retrofits ?page=/?per_page= paging onto an
unpaged list endpoint and submits three page lines (pages 1, 2, 99).
The grader recomputes the expected slices from the in-payload fixture
(23 rows): exact slices, one consistent total, stable order, empty
out-of-range page -- no partial credit. Static, deterministic.
"""
from __future__ import annotations

import json
import sqlite3

CARD_ID = 'demo-pageapi-68'
FRONT = 'Page this endpoint (default `per_page=5`, max 20):\n```python\ndef list_items():\n    return get_all_items()  # full list, no paging\n```\nContract: `GET /items?page=` (1-based, default 1) and `?per_page=` (default 5). Reply with three `page=<json>` lines (pages 1, 2, and 99) shaped `{"items": [...], "page": p, "per_page": n, "total": T}` using `per_page=5`.'
BACK = 'Reference (page 1):\n{"items": [{"id": 1, "name": "items-92e000-01"}, {"id": 2, "name": "items-92e000-02"}, {"id": 3, "name": "items-92e000-03"}, {"id": 4, "name": "items-92e000-04"}, {"id": 5, "name": "items-92e000-05"}], "page": 1, "per_page": 5, "total": 23}'
PAYLOAD = {'resource': 'items', 'rows': [{'id': 1, 'name': 'items-92e000-01'}, {'id': 2, 'name': 'items-92e000-02'}, {'id': 3, 'name': 'items-92e000-03'}, {'id': 4, 'name': 'items-92e000-04'}, {'id': 5, 'name': 'items-92e000-05'}, {'id': 6, 'name': 'items-92e000-06'}, {'id': 7, 'name': 'items-92e000-07'}, {'id': 8, 'name': 'items-92e000-08'}, {'id': 9, 'name': 'items-92e000-09'}, {'id': 10, 'name': 'items-92e000-10'}, {'id': 11, 'name': 'items-92e000-11'}, {'id': 12, 'name': 'items-92e000-12'}, {'id': 13, 'name': 'items-92e000-13'}, {'id': 14, 'name': 'items-92e000-14'}, {'id': 15, 'name': 'items-92e000-15'}, {'id': 16, 'name': 'items-92e000-16'}, {'id': 17, 'name': 'items-92e000-17'}, {'id': 18, 'name': 'items-92e000-18'}, {'id': 19, 'name': 'items-92e000-19'}, {'id': 20, 'name': 'items-92e000-20'}, {'id': 21, 'name': 'items-92e000-21'}, {'id': 22, 'name': 'items-92e000-22'}, {'id': 23, 'name': 'items-92e000-23'}], 'per_page_default': 5, 'per_page_max': 20, 'total': 23, 'grounded': True}
ANSWER = 'page1={"items": [{"id": 1, "name": "items-92e000-01"}, {"id": 2, "name": "items-92e000-02"}, {"id": 3, "name": "items-92e000-03"}, {"id": 4, "name": "items-92e000-04"}, {"id": 5, "name": "items-92e000-05"}], "page": 1, "per_page": 5, "total": 23}\npage2={"items": [{"id": 6, "name": "items-92e000-06"}, {"id": 7, "name": "items-92e000-07"}, {"id": 8, "name": "items-92e000-08"}, {"id": 9, "name": "items-92e000-09"}, {"id": 10, "name": "items-92e000-10"}], "page": 2, "per_page": 5, "total": 23}\npage99={"items": [], "page": 99, "per_page": 5, "total": 23}'

SCENARIO = {
    "id": "pageapi",
    "kind": "feature",
    "batch": 11,
    "item": "F-45",
    "title": "Page the endpoint",
    "blurb": "Retrofit paging -- slices, total, order, all exact.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 11 - Feature F-45",
         "title": "Page the endpoint",
         "subtitle": "Three page lines -- the contract holds or it does not."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b11-pageapi",
         "caption": "Status homes the type: fixture slices, one total, stable order.",
         "assert_js": "() => !!document.querySelector('#status-b11-pageapi')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 8,
         "caption": "The rule in one line: exact slices pass, a gapped page 2 fails.",
         "commands": [
             ["python3", "-c",
              "import sys; sys.path.insert(0, 'tools'); "
              "from demos.pageapi import PAYLOAD, ANSWER; "
              "from groundwork import pageapi as m; "
              "ex = {'payload': PAYLOAD}; "
              "ok = m.grade(ex, ANSWER); bad = m.grade(ex, 'page1=1'); "
              "print('good:', ok['pass'], '-', ok['feedback']); "
              "print('bad:', bad['pass'], '-', bad['feedback'])"],
         ]},
        {"type": "chrome", "duration": 8,
         "url_path": "/due",
         "focus": "#card-{seed_card_id}",
         "caption": "The paging card: unpaged endpoint on top, three pages below.",
         "assert_js": "() => { const f = document.querySelector("
                      "\"form[action='/cards/{seed_card_id}/review']\"); "
                      "return !!f && !!f.querySelector(\"[name='answer']\") && "
                      "document.body.innerText.includes('per_page=5'); }",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 11",
         "title": "No overlap, no gap.",
         "subtitle": "pageapi.py recomputes the slices -- the fixture is truth."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Plant one type-68 card (generated shape) as the sole due card."""
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
            " VALUES(?, ?, '68', ?, ?, ?, '2000-01-01T00:00:00Z')",
            (CARD_ID, row[0], FRONT, BACK, json.dumps(PAYLOAD)))
        con.commit()
        return {"seeded": True, "card_id": CARD_ID}
    finally:
        con.close()
