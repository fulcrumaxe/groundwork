"""Feature demo: boundary-value drills (F-84, type 88).

Full behavior: name the ONE edge integer to probe first at a
comparison or range site -- first-integer-token match, no partial
credit, neighbours told exactly how far off they are. seed_db
plants the generated boundary card as the sole due card; the /due
beat names the edge and polls the edge-nailed verdict.
"""
from __future__ import annotations

import json
import sqlite3

CARD_ID = "demo-b19-boundary"
CODE = "def get(xs, i):\n    if i < 10:\n        return xs[i]\n    return None\n"
FRONT = ("Which value must you probe first at `i < 10`? "
         "Reply with the edge integer.\n```python\n" + CODE + "```")
BACK = "10: probe 9 / 10 / 11 — the literal itself is the edge."
PAYLOAD = {"choices": ["9", "10", "11"], "answer": "10",
           "site": "i < 10", "kind": "compare",
           "reference": "10", "grounded": True}
ANSWER = "10"

SCENARIO = {
    "id": "boundary",
    "kind": "feature",
    "batch": 19,
    "item": "F-84",
    "title": "Boundary-value drills",
    "blurb": "Name the ONE edge integer to probe first -- off-by-one bootcamp.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 19 - Feature F-84",
         "title": "Boundary-value drills",
         "subtitle": "The literal is the edge -- probe it first, neighbours miss by one."},
        {"type": "terminal", "duration": 7,
         "caption": "Exact edge wins; a neighbour is told precisely how far off it is.",
         "commands": [
             ["python3", "-c",
              "from groundwork import boundary as m; "
              "ex = {'payload': {'answer': '10'}}; "
              "print(m.grade(ex, '10')['feedback']); "
              "print(m.grade(ex, '9')['feedback']); "
              "print(m.grade(ex, '')['feedback'])"],
         ]},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b19-boundary",
         "caption": "Status homes the type: comparison and range sites, edge-first habit.",
         "assert_js": "() => !!document.querySelector('#status-b19-boundary')",
         "assert_want": "True"},
        {"type": "chrome", "duration": 8,
         "url_path": "/due",
         "focus": "#card-{seed_card_id} h3",
         "caption": "The drill card: one comparison site, one edge integer to name.",
         "assert_js": "() => { const f = document.querySelector("
                     "\"form[action='/cards/{seed_card_id}/review']\"); "
                     "return !!f && document.body.innerText.includes('Reply with the edge integer'); }",
         "assert_want": "True"},
        {"type": "chrome", "duration": 13,
         "url_path": "/due",
         "caption": "Ten is the edge -- nine and eleven are the off-by-one neighbours.",
         "js": ["() => { const f = document.querySelector(\"form[action='/cards/{seed_card_id}/review']\"); "
                "if (!f) return 'seed-form-missing'; "
                "f.querySelectorAll(\"input[name='answer']\").forEach(i => i.value = {seed_answer_js}); "
                "const conf = f.querySelector(\"input[name='confidence'][value='4']\"); "
                "if (conf) conf.checked = true; "
                "f.submit(); return 'submitted'; }"],
         "poll_js": "() => document.body.innerText.slice(0, 12000)",
         "poll_want": "Edge nailed",
         "poll_required": True,
         "poll_timeout": 25,
         "assert_js": "() => !!document.querySelector('.verdict-stamp') && "
                      "document.body.innerText.includes('triple habit holds')",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 19",
         "title": "Probe the edge first.",
         "subtitle": "boundary.py grades the first integer -- L-1, L, L+1."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Plant the generated type-88 card (pipeline shape) as the sole due card."""
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
            " VALUES(?, ?, '88', ?, ?, ?, '2000-01-01T00:00:00Z')",
            (CARD_ID, row[0], FRONT, BACK, json.dumps(PAYLOAD)))
        con.commit()
        return {"seeded": True, "card_id": CARD_ID,
                "answer_js": json.dumps(json.dumps(ANSWER))[1:-1]}
    finally:
        con.close()
