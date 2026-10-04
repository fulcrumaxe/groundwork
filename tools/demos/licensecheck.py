"""Feature demo: license-check (F-40, type 63).

Full behavior: judge whether one candidate dependency may combine
into this AGPL-3.0 project -- OK or NOT-OK plus exactly one reason
keyword -- graded by exact verdict+reason match (a fixed-table
matching exercise, not legal advice). seed_db plants a static
bsd-hash/permissive card (generate() bytes) as the sole due card;
/due judges it and polls the verdict.
"""
from __future__ import annotations

import json
import sqlite3

CARD_ID = "demo-licensecheck-63"

SCENARIO = {
    "id": "licensecheck",
    "kind": "feature",
    "batch": 10,
    "item": "F-40",
    "title": "License-check",
    "blurb": "Judge whether a dependency fits this AGPL-3.0 project -- verdict plus reason.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 10 - Feature F-40",
         "title": "License-check",
         "subtitle": "Verdict plus reason -- judge the combination, not the dep alone."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b10-licensecheck",
         "caption": "Status homes the type: OK/NOT-OK plus one reason keyword, both exact.",
         "assert_js": "() => !!document.querySelector('#status-b10-licensecheck')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "The rule in one line: right verdict plus right reason passes, either alone fails.",
         "commands": [
             ["python3", "-c",
              "from groundwork import licensecheck as m; "
              "ex = {'payload': {'verdict': 'ok', 'reason': 'permissive'}}; "
              "print(m.grade(ex, 'OK permissive')['feedback']); "
              "print(m.grade(ex, 'NOT-OK permissive')['feedback'])"],
         ]},
        {"type": "chrome", "duration": 8,
         "url_path": "/due",
         "focus": "#card-{seed_card_id}",
         "caption": "The license card: project AGPL-3.0, one candidate dep, linkage facts.",
         "assert_js": "() => { const f = document.querySelector("
                      "\"form[action='/cards/{seed_card_id}/review']\"); "
                      "return !!f && !!f.querySelector(\"input[name='answer']\") && "
                      "document.body.innerText.includes('OK to combine'); }",
         "assert_want": "True"},
        {"type": "chrome", "duration": 13,
         "url_path": "/due",
         "caption": "Judge the dep -- the verdict checks verdict plus reason.",
         "js": ["() => { const f = document.querySelector(\"form[action='/cards/{seed_card_id}/review']\"); "
                "if (!f) return 'seed-form-missing'; "
                "const inp = f.querySelector(\"input[name='answer']\"); "
                "if (!inp) return 'no-input'; inp.value = {seed_answer_js}; "
                "const conf = f.querySelector(\"input[name='confidence'][value='4']\"); "
                "if (conf) conf.checked = true; "
                "f.submit(); return 'submitted'; }"],
         "poll_js": "() => document.body.innerText.slice(0, 12000)",
         "poll_want": "Correct: OK (permissive)",
         "poll_required": True,
         "poll_timeout": 25,
         "assert_js": "() => !!document.querySelector('.verdict-stamp') && "
                      "document.body.innerText.includes('Correct: OK (permissive)')",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 10",
         "title": "OK, permissively.",
         "subtitle": "licensecheck.py grades both halves -- a matching exercise."},
    ],
}

FRONT = 'This project is licensed AGPL-3.0. A candidate dependency:\n- `bsd-hash` licensed `BSD-3-Clause` (static link, unmodified)\nIs this dependency OK to combine into the project? Reply with OK or NOT-OK plus exactly ONE reason keyword from: `copyleft`, `patent-grant`, `network-clause`, `version-mismatch`, `permissive`.'
BACK = 'OK (`bsd-hash`, BSD-3-Clause): BSD-3-Clause is permissive: attribution only, no copyleft conditions. Reason keyword `permissive`. This is a matching exercise, not legal advice -- confirm real decisions with a lawyer.'
PAYLOAD = {'dep': 'bsd-hash', 'dep_license': 'BSD-3-Clause', 'project_license': 'AGPL-3.0', 'linkage': 'static', 'modified': False, 'verdict': 'ok', 'reason': 'permissive', 'why': 'BSD-3-Clause is permissive: attribution only, no copyleft conditions.', 'grounded': True}
ANSWER = "OK permissive"


def seed_db(db_path: str) -> dict:
    """Plant one type-63 card (generate() bytes) as the sole due card."""
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
            " VALUES(?, ?, '63', ?, ?, ?, '2000-01-01T00:00:00Z')",
            (CARD_ID, row[0], FRONT, BACK, json.dumps(PAYLOAD)))
        con.commit()
        return {"seeded": True, "card_id": CARD_ID,
                "answer_js": json.dumps(json.dumps(ANSWER))[1:-1]}
    finally:
        con.close()
