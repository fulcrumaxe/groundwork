"""Feature demo: Feynman check (F-81, type 85).

Full behavior: explain the concept as if to a smart 12-year-old --
rubric coverage gated by a jargon budget of two; business-speak
over budget halves the score and fails the card. seed_db plants
the generated Feynman card as the sole due card; the /due beat
explains it plainly and polls the Feynman-nods verdict.
"""
from __future__ import annotations

import json
import sqlite3

CARD_ID = "demo-b19-feynman"
FRONT = ("Explain `add` as if to a smart 12-year-old: what it does, why it "
         "exists, one concrete example. Plain words score; jargon costs "
         "(budget: 2).\n```python\ndef add(a, b):\n    return a + b\n```")
BACK = "Key points: sum; inputs. Plain-words tip: say it simply first."
PAYLOAD = {"rubric": ["sum", "inputs"], "budget": 2,
           "jargon": ["leverage", "synergy", "utilize", "robust", "scalable"],
           "grounded": True}
ANSWER = ("add takes two inputs and gives back their sum, like pooling "
          "two piles of coins")

SCENARIO = {
    "id": "feynman",
    "kind": "feature",
    "batch": 19,
    "item": "F-81",
    "title": "Feynman check",
    "blurb": "Explain it simply -- rubric coverage gated by a jargon budget.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 19 - Feature F-81",
         "title": "Feynman check",
         "subtitle": "Cover the points in plain words -- jargon over budget fails."},
        {"type": "terminal", "duration": 7,
         "caption": "Plain words pass; four jargon terms blow the budget of two.",
         "commands": [
             ["python3", "-c",
              "from groundwork import feynman as m; "
              "ex = {'payload': {'rubric': ['sum', 'inputs'], 'budget': 2}}; "
              "print(m.grade(ex, 'add takes two inputs and gives back their sum')['feedback']); "
              "print(m.grade(ex, 'add leverages synergy to utilize the inputs for a robust sum')['feedback'])"],
         ]},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b19-feynman",
         "caption": "Status homes the type: twelve-year-old bar, jargon budget of two.",
         "assert_js": "() => !!document.querySelector('#status-b19-feynman')",
         "assert_want": "True"},
        {"type": "chrome", "duration": 8,
         "url_path": "/due",
         "focus": "#card-{seed_card_id} h3",
         "caption": "The Feynman card: plain explanation wanted, jargon counted.",
         "assert_js": "() => { const f = document.querySelector("
                     "\"form[action='/cards/{seed_card_id}/review']\"); "
                     "return !!f && document.body.innerText.includes('12-year-old'); }",
         "assert_want": "True"},
        {"type": "chrome", "duration": 13,
         "url_path": "/due",
         "caption": "Explained like the reader is twelve -- plain and complete.",
         "js": ["() => { const f = document.querySelector(\"form[action='/cards/{seed_card_id}/review']\"); "
                "if (!f) return 'seed-form-missing'; "
                "const nf = document.createElement('form'); nf.method = 'post'; nf.action = f.action; "
                "const ta = document.createElement('textarea'); ta.name = 'answer'; ta.value = {seed_answer_js}; "
                "const cf = document.createElement('input'); cf.type = 'hidden'; cf.name = 'confidence'; cf.value = '4'; "
                "const og = document.createElement('input'); og.type = 'hidden'; og.name = 'origin'; og.value = '/due'; "
                "nf.appendChild(ta); nf.appendChild(cf); nf.appendChild(og); "
                "document.body.appendChild(nf); nf.submit(); return 'submitted'; }"],
         "poll_js": "() => document.body.innerText.slice(0, 12000)",
         "poll_want": "Feynman nods",
         "poll_required": True,
         "poll_timeout": 25,
         "assert_js": "() => !!document.querySelector('.verdict-stamp') && "
                      "document.body.innerText.includes('Plain and complete')",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 19",
         "title": "Simple is the proof.",
         "subtitle": "feynman.py counts jargon -- plain coverage passes."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Plant the generated type-85 card (pipeline shape) as the sole due card."""
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
            " VALUES(?, ?, '85', ?, ?, ?, '2000-01-01T00:00:00Z')",
            (CARD_ID, row[0], FRONT, BACK, json.dumps(PAYLOAD)))
        con.commit()
        return {"seeded": True, "card_id": CARD_ID,
                "answer_js": json.dumps(json.dumps(ANSWER))[1:-1]}
    finally:
        con.close()
