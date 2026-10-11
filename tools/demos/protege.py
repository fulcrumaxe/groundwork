"""Feature demo: protege-effect studio (F-80, type 84).

Full behavior: teach a simulated junior -- correct their claim
against a keyword half-bar, then answer the follow-up with its
letter; both halves must pass. seed_db plants the generated
protege card as the sole due card; the /due beat teaches both
halves and polls the teaching-lands verdict.
"""
from __future__ import annotations

import json
import sqlite3

CARD_ID = "demo-b19-protege"
FRONT = ("A junior says: \"add(a, b) multiplies a and b\"\n"
         "Correct them, then answer their follow-up: What does add(2, 3) return?\n"
         "A) 6\nB) 5\nC) 23\n"
         "```python\ndef add(a, b):\n    return a + b\n```")
BACK = "Correction covers: sum, inputs. Follow-up answer: B."
PAYLOAD = {"rubric": ["sum", "inputs"],
           "junior_claim": "add(a, b) multiplies a and b",
           "followup": {"q": "What does add(2, 3) return?",
                        "choices": ["6", "5", "23"],
                        "answer": "B", "key": "B"},
           "key": "B", "reference": "sum, inputs", "grounded": True}
ANSWER = ("The junior is wrong: add returns the sum of its inputs, "
          "not their product.\nB")

SCENARIO = {
    "id": "protege",
    "kind": "feature",
    "batch": 19,
    "item": "F-80",
    "title": "Protege-effect studio",
    "blurb": "Teach a simulated junior -- correct the claim, answer the follow-up, both must pass.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 19 - Feature F-80",
         "title": "Protege-effect studio",
         "subtitle": "Correct the junior AND answer the follow-up -- both halves must pass."},
        {"type": "terminal", "duration": 7,
         "caption": "Two gates: the correction covers the points, the letter answers the follow-up.",
         "commands": [
             ["python3", "-c",
              "from groundwork import protege as m; "
              "ex = {'payload': {'rubric': ['sum', 'inputs'], 'key': 'B'}}; "
              "print(m.grade(ex, 'add returns the sum of its inputs\\nB')['feedback']); "
              "print(m.grade(ex, 'add multiplies things\\nC')['feedback']); "
              "print(m.grade(ex, '')['feedback'])"],
         ]},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b19-protege",
         "caption": "Status homes the type: staged junior claim, correction plus follow-up.",
         "assert_js": "() => !!document.querySelector('#status-b19-protege')",
         "assert_want": "True"},
        {"type": "chrome", "duration": 8,
         "url_path": "/due",
         "focus": "#card-{seed_card_id} h3",
         "caption": "The studio card: a junior's wrong claim, then a follow-up to answer.",
         "assert_js": "() => { const f = document.querySelector("
                     "\"form[action='/cards/{seed_card_id}/review']\"); "
                     "return !!f && document.body.innerText.includes('junior says'); }",
         "assert_want": "True"},
        {"type": "chrome", "duration": 13,
         "url_path": "/due",
         "caption": "Claim corrected, follow-up lettered -- the junior is taught.",
         "js": ["() => { const f = document.querySelector(\"form[action='/cards/{seed_card_id}/review']\"); "
                "if (!f) return 'seed-form-missing'; "
                "const nf = document.createElement('form'); nf.method = 'post'; nf.action = f.action; "
                "const ta = document.createElement('textarea'); ta.name = 'answer'; ta.value = {seed_answer_js}; "
                "const cf = document.createElement('input'); cf.type = 'hidden'; cf.name = 'confidence'; cf.value = '4'; "
                "const og = document.createElement('input'); og.type = 'hidden'; og.name = 'origin'; og.value = '/due'; "
                "nf.appendChild(ta); nf.appendChild(cf); nf.appendChild(og); "
                "document.body.appendChild(nf); nf.submit(); return 'submitted'; }"],
         "poll_js": "() => document.body.innerText.slice(0, 12000)",
         "poll_want": "teaching lands",
         "poll_required": True,
         "poll_timeout": 25,
         "assert_js": "() => !!document.querySelector('.verdict-stamp') && "
                      "document.body.innerText.includes('Junior corrected')",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 19",
         "title": "Teach to learn.",
         "subtitle": "protege.py stages the junior -- correction plus letter both pass."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Plant the generated type-84 card (pipeline shape) as the sole due card."""
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
            " VALUES(?, ?, '84', ?, ?, ?, '2000-01-01T00:00:00Z')",
            (CARD_ID, row[0], FRONT, BACK, json.dumps(PAYLOAD)))
        con.commit()
        return {"seeded": True, "card_id": CARD_ID,
                "answer_js": json.dumps(json.dumps(ANSWER))[1:-1]}
    finally:
        con.close()
