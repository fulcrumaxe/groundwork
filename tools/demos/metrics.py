"""Feature demo: metrics reading (F-36, type 59).

Full behavior: read three text metric series spanning one deploy
mark and name the single graph that regresses -- the distractors
stay flat or improve. Grading is an exact isolated-letter match,
so pasted series never pass. seed_db plants a static graph-B card
(generate() bytes) as the sole due card; /due picks B and polls
the letter verdict.
"""
from __future__ import annotations

import json
import sqlite3

CARD_ID = "demo-metrics-59"

SCENARIO = {
    "id": "metrics",
    "kind": "feature",
    "batch": 10,
    "item": "F-36",
    "title": "Metrics reading",
    "blurb": "Spot which graph regressed at the deploy mark -- reply with its letter.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 10 - Feature F-36",
         "title": "Metrics reading",
         "subtitle": "Three graphs, one deploy -- a single letter names the regression."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b10-metrics",
         "caption": "Status homes the type: pre vs post at the deploy mark, one letter.",
         "assert_js": "() => !!document.querySelector('#status-b10-metrics')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "The rule in one line: the isolated letter passes, any other letter fails.",
         "commands": [
             ["python3", "-c",
              "from groundwork import metrics as m; "
              "ex = {'payload': {'answer': 'B'}}; "
              "print(m.grade(ex, 'graph b')['feedback']); "
              "print(m.grade(ex, 'A')['feedback'])"],
         ]},
        {"type": "chrome", "duration": 8,
         "url_path": "/due",
         "focus": "#card-{seed_card_id}",
         "caption": "The metrics card: three series, one | mark, flat and better distractors.",
         "assert_js": "() => { const f = document.querySelector("
                      "\"form[action='/cards/{seed_card_id}/review']\"); "
                      "return !!f && !!f.querySelector(\"input[name='answer']\") && "
                      "document.body.innerText.includes('regression at the deploy'); }",
         "assert_want": "True"},
        {"type": "chrome", "duration": 13,
         "url_path": "/due",
         "caption": "Pick the letter -- the verdict compares pre vs post at the mark.",
         "js": ["() => { const f = document.querySelector(\"form[action='/cards/{seed_card_id}/review']\"); "
                "if (!f) return 'seed-form-missing'; "
                "const inp = f.querySelector(\"input[name='answer']\"); "
                "if (!inp) return 'no-input'; inp.value = {seed_answer_js}; "
                "const conf = f.querySelector(\"input[name='confidence'][value='4']\"); "
                "if (conf) conf.checked = true; "
                "f.submit(); return 'submitted'; }"],
         "poll_js": "() => document.body.innerText.slice(0, 12000)",
         "poll_want": "Graph B shows the regression",
         "poll_required": True,
         "poll_timeout": 25,
         "assert_js": "() => !!document.querySelector('.verdict-stamp') && "
                      "document.body.innerText.includes('Graph B shows the regression')",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 10",
         "title": "B, at the mark.",
         "subtitle": "metrics.py grades one letter -- dumps never count."},
    ],
}

FRONT = 'Three metric series span one deploy (marked |). Exactly ONE graph shows a regression at the deploy — the others stay flat or improve. Reply with the single letter A, B, or C.\n```\nA. latency p99 (ms) — deploy at |\n   t00     120 ms ########\n   t01     116 ms #\n   t02     124 ms ################\n   t03     117 ms ####\n   t04     125 ms #################\n   t05     120 ms #########\n | t06     123 ms ##############\n   t07     121 ms ##########\n   t08     119 ms ########\n   t09     126 ms ####################\n   t10     120 ms #########\n   t11     120 ms #########\nB. cpu (%) — deploy at |\n   t00      44 % #\n   t01      44 % #\n   t02      47 % ###\n   t03      46 % ##\n   t04      46 % ##\n   t05      44 % #\n | t06      66 % #################\n   t07      65 % ################\n   t08      70 % ####################\n   t09      70 % ###################\n   t10      67 % #################\n   t11      69 % ##################\nC. error rate (%) — deploy at |\n   t00     1.0 % #################\n   t01     1.0 % ###################\n   t02     1.0 % ####################\n   t03     1.0 % ###################\n   t04     1.0 % ###############\n   t05     1.0 % ##################\n | t06     0.8 % #\n   t07     0.8 % ##\n   t08     0.8 % ##\n   t09     0.8 % #\n   t10     0.8 % ##\n   t11     0.8 % ###\n```'
BACK = 'Graph B (cpu) regressed at the deploy: avg 45.19 -> 67.88 %.'
PAYLOAD = {'graphs': [{'letter': 'A', 'label': 'latency p99', 'unit': 'ms', 'kind': 'flat', 'pre': 120.21, 'post': 121.54}, {'letter': 'B', 'label': 'cpu', 'unit': '%', 'kind': 'regress', 'pre': 45.19, 'post': 67.88}, {'letter': 'C', 'label': 'error rate', 'unit': '%', 'kind': 'better', 'pre': 1.01, 'post': 0.78}], 'choices': ['A', 'B', 'C'], 'answer': 'B', 'grounded': True}
ANSWER = "B"


def seed_db(db_path: str) -> dict:
    """Plant one type-59 card (generate() bytes) as the sole due card."""
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
            " VALUES(?, ?, '59', ?, ?, ?, '2000-01-01T00:00:00Z')",
            (CARD_ID, row[0], FRONT, BACK, json.dumps(PAYLOAD)))
        con.commit()
        return {"seeded": True, "card_id": CARD_ID,
                "answer_js": json.dumps(json.dumps(ANSWER))[1:-1]}
    finally:
        con.close()
