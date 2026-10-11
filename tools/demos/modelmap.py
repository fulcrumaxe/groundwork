"""Feature demo: mental-model mapping (F-78, type 82).

Full behavior: draw the data flow through a concept from memory --
one edge per line -- graph-diff graded with partial credit per
edge. seed_db plants the generated model-map card as the sole due
card; the /due beat sketches both edges and polls the verified
verdict.
"""
from __future__ import annotations

import json
import sqlite3

CARD_ID = "demo-b19-modelmap"
FRONT = ("Draw the data flow through `add` from memory — one edge per line, "
         "like \"caller -> concept\".\n```python\ndef add(a, b):\n    return a + b\n```")
BACK = "serve -> add -> total"
PAYLOAD = {"nodes": ["serve", "add", "total"],
           "edges": [["serve", "add"], ["add", "total"]],
           "key": "serve -> add -> total", "grounded": True}
ANSWER = "serve -> add\nadd -> total"

SCENARIO = {
    "id": "modelmap",
    "kind": "feature",
    "batch": 19,
    "item": "F-78",
    "title": "Mental-model mapping",
    "blurb": "Draw the data flow from memory -- graph-diff graded, partial credit per edge.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 19 - Feature F-78",
         "title": "Mental-model mapping",
         "subtitle": "Sketch the flow from memory -- exact set passes, edges earn partial credit."},
        {"type": "terminal", "duration": 7,
         "caption": "Graph-diff grading: the full set verifies, half the edges earn half credit.",
         "commands": [
             ["python3", "-c",
              "from groundwork import modelmap as m; "
              "ex = {'payload': {'edges': [['serve', 'add'], ['add', 'total']]}}; "
              "print(m.grade(ex, 'serve -> add\\nadd -> total')['feedback']); "
              "print(m.grade(ex, 'serve -> add')['feedback']); "
              "print(m.grade(ex, '')['feedback'])"],
         ]},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b19-modelmap",
         "caption": "Status homes the type: memory-drawn flow, graph-diff graded.",
         "assert_js": "() => !!document.querySelector('#status-b19-modelmap')",
         "assert_want": "True"},
        {"type": "chrome", "duration": 8,
         "url_path": "/due",
         "focus": "#card-{seed_card_id} h3",
         "caption": "The mapping card: no diagram given -- the flow comes from memory.",
         "assert_js": "() => { const f = document.querySelector("
                     "\"form[action='/cards/{seed_card_id}/review']\"); "
                     "return !!f && document.body.innerText.includes('from memory'); }",
         "assert_want": "True"},
        {"type": "chrome", "duration": 13,
         "url_path": "/due",
         "caption": "Both edges sketched -- the drawn flow matches the recorded one.",
         "js": ["() => { const f = document.querySelector(\"form[action='/cards/{seed_card_id}/review']\"); "
                "if (!f) return 'seed-form-missing'; "
                "const nf = document.createElement('form'); nf.method = 'post'; nf.action = f.action; "
                "const ta = document.createElement('textarea'); ta.name = 'answer'; ta.value = {seed_answer_js}; "
                "const cf = document.createElement('input'); cf.type = 'hidden'; cf.name = 'confidence'; cf.value = '4'; "
                "const og = document.createElement('input'); og.type = 'hidden'; og.name = 'origin'; og.value = '/due'; "
                "nf.appendChild(ta); nf.appendChild(cf); nf.appendChild(og); "
                "document.body.appendChild(nf); nf.submit(); return 'submitted'; }"],
         "poll_js": "() => document.body.innerText.slice(0, 12000)",
         "poll_want": "Flow matches",
         "poll_required": True,
         "poll_timeout": 25,
         "assert_js": "() => !!document.querySelector('.verdict-stamp') && "
                      "document.body.innerText.includes('model verified')",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 19",
         "title": "Draw it to prove it.",
         "subtitle": "modelmap.py diffs your edges -- memory, not recognition."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Plant the generated type-82 card (pipeline shape) as the sole due card."""
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
            " VALUES(?, ?, '82', ?, ?, ?, '2000-01-01T00:00:00Z')",
            (CARD_ID, row[0], FRONT, BACK, json.dumps(PAYLOAD)))
        con.commit()
        return {"seeded": True, "card_id": CARD_ID,
                "answer_js": json.dumps(json.dumps(ANSWER))[1:-1]}
    finally:
        con.close()
