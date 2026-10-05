"""Feature demo: CI pipeline authoring exercise (F-42, type 65).

Full behavior: the learner authors a push-triggered CI workflow YAML;
a static dry-run lint checks on/push, a non-empty jobs map, steps per
job, and run/uses per step -- no runner, no network, no partial
credit. seed_db plants the generated card as the sole due card; the
terminal beat grades the reference pass plus a failing submit.
"""
from __future__ import annotations

import json
import sqlite3

CARD_ID = 'demo-cipipe-65'
FRONT = 'Author the `ci-app` CI pipeline: triggers on push to `main`, one job with steps that check out code and run tests. Submit a complete workflow YAML file.'
BACK = 'on:\n  push:\n    branches: [main]\njobs:\n  test:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v4\n      - run: pytest'
PAYLOAD = {'workflow': 'ci-app', 'branch': 'main', 'grounded': True}
ANSWER = 'on:\n  push:\n    branches: [main]\njobs:\n  test:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v4\n      - run: pytest'

SCENARIO = {
    "id": "cipipe",
    "kind": "feature",
    "batch": 11,
    "item": "F-42",
    "title": "CI pipeline",
    "blurb": "Author a push-triggered workflow -- a static lint dry-runs it.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 11 - Feature F-42",
         "title": "CI pipeline",
         "subtitle": "Write the YAML -- the lint plays CI server."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b11-cipipe",
         "caption": "Status homes the type: push trigger, jobs, steps, no runner.",
         "assert_js": "() => !!document.querySelector('#status-b11-cipipe')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 8,
         "caption": "The rule in one line: complete workflow passes, prose fails the lint.",
         "commands": [
             ["python3", "-c",
              "import sys; sys.path.insert(0, 'tools'); "
              "from demos.cipipe import PAYLOAD, ANSWER; "
              "from groundwork import cipipe as m; "
              "ex = {'payload': PAYLOAD}; "
              "ok = m.grade(ex, ANSWER); bad = m.grade(ex, 'hello'); "
              "print('good:', ok['pass'], '-', ok['feedback']); "
              "print('bad:', bad['pass'], '-', bad['feedback'])"],
         ]},
        {"type": "chrome", "duration": 8,
         "url_path": "/due",
         "focus": "#card-{seed_card_id}",
         "caption": "The pipeline card: spec on top, answer box below, same as every card.",
         "assert_js": "() => { const f = document.querySelector("
                      "\"form[action='/cards/{seed_card_id}/review']\"); "
                      "return !!f && !!f.querySelector(\"[name='answer']\") && "
                      "document.body.innerText.includes('ci-app'); }",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 11",
         "title": "Green without a runner.",
         "subtitle": "cipipe.py lints the workflow -- push, jobs, steps, or fail."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Plant one type-65 card (generated shape) as the sole due card."""
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
            " VALUES(?, ?, '65', ?, ?, ?, '2000-01-01T00:00:00Z')",
            (CARD_ID, row[0], FRONT, BACK, json.dumps(PAYLOAD)))
        con.commit()
        return {"seeded": True, "card_id": CARD_ID}
    finally:
        con.close()
