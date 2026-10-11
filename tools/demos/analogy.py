"""Feature demo: analogy builder (F-82, type 86).

Full behavior: map the concept onto an assigned familiar domain --
a public library here -- then state exactly where the analogy
breaks; keyword half-bar grading names missing points. seed_db
plants the generated analogy card as the sole due card; the /due
beat maps it and names the break, polling the mapping-holds
verdict.
"""
from __future__ import annotations

import json
import sqlite3

CARD_ID = "demo-b19-analogy"
FRONT = ("Explain `add` through a public library: map each part, then state "
         "exactly where the analogy breaks.\n"
         "```python\ndef add(a, b):\n    return a + b\n```")
BACK = "sum; inputs; return as a public library"
PAYLOAD = {"domain": "a public library",
           "rubric": ["sum", "inputs", "return"],
           "code": "def add(a, b):\n    return a + b",
           "grounded": True}
ANSWER = ("add is like the returns desk: two inputs arrive as separate "
          "stacks and leave as one combined sum pile, and the desk hands "
          "the total back; it breaks because a desk cannot add numbers, "
          "it only shelves them")

SCENARIO = {
    "id": "analogy",
    "kind": "feature",
    "batch": 19,
    "item": "F-82",
    "title": "Analogy builder",
    "blurb": "Map it onto a familiar domain -- then state where the analogy breaks.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 19 - Feature F-82",
         "title": "Analogy builder",
         "subtitle": "Map the concept to the domain -- then name where it breaks."},
        {"type": "terminal", "duration": 7,
         "caption": "Half-bar grading on the mapped points; thin mappings name the gaps.",
         "commands": [
             ["python3", "-c",
              "from groundwork import analogy as m; "
              "ex = {'payload': {'rubric': ['sum', 'inputs', 'return']}}; "
              "print(m.grade(ex, 'two inputs return as one sum')['feedback']); "
              "print(m.grade(ex, 'it is like a library')['feedback']); "
              "print(m.grade(ex, '')['feedback'])"],
         ]},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b19-analogy",
         "caption": "Status homes the type: assigned domain, mapped points, stated break.",
         "assert_js": "() => !!document.querySelector('#status-b19-analogy')",
         "assert_want": "True"},
        {"type": "chrome", "duration": 8,
         "url_path": "/due",
         "focus": "#card-{seed_card_id} h3",
         "caption": "The analogy card: the domain is assigned, the mapping is yours.",
         "assert_js": "() => { const f = document.querySelector("
                     "\"form[action='/cards/{seed_card_id}/review']\"); "
                     "return !!f && document.body.innerText.includes('where the analogy'); }",
         "assert_want": "True"},
        {"type": "chrome", "duration": 13,
         "url_path": "/due",
         "caption": "Mapped to the library, break stated -- the mapping holds with limits.",
         "js": ["() => { const f = document.querySelector(\"form[action='/cards/{seed_card_id}/review']\"); "
                "if (!f) return 'seed-form-missing'; "
                "const nf = document.createElement('form'); nf.method = 'post'; nf.action = f.action; "
                "const ta = document.createElement('textarea'); ta.name = 'answer'; ta.value = {seed_answer_js}; "
                "const cf = document.createElement('input'); cf.type = 'hidden'; cf.name = 'confidence'; cf.value = '4'; "
                "const og = document.createElement('input'); og.type = 'hidden'; og.name = 'origin'; og.value = '/due'; "
                "nf.appendChild(ta); nf.appendChild(cf); nf.appendChild(og); "
                "document.body.appendChild(nf); nf.submit(); return 'submitted'; }"],
         "poll_js": "() => document.body.innerText.slice(0, 12000)",
         "poll_want": "Mapping holds",
         "poll_required": True,
         "poll_timeout": 25,
         "assert_js": "() => !!document.querySelector('.verdict-stamp') && "
                      "document.body.innerText.includes('named its limit')",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 19",
         "title": "Map it, then break it.",
         "subtitle": "analogy.py assigns the domain -- your mapping covers the points."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Plant the generated type-86 card (pipeline shape) as the sole due card."""
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
            " VALUES(?, ?, '86', ?, ?, ?, '2000-01-01T00:00:00Z')",
            (CARD_ID, row[0], FRONT, BACK, json.dumps(PAYLOAD)))
        con.commit()
        return {"seeded": True, "card_id": CARD_ID,
                "answer_js": json.dumps(json.dumps(ANSWER))[1:-1]}
    finally:
        con.close()
