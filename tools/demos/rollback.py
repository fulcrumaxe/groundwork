"""Feature demo: rollback planning (F-25, type 48).

Full behavior: order five shuffled rollback steps freeze-first
to verify-last -- exact sequence passes, adjacent pairs earn
partial. seed_db plants a static type-48 card (generate() bytes,
steps listed on the front) as the sole due card; terminal runs
exact-accept + shuffled-partial, /due submits the safe order
and polls the 5/5 verdict.
"""
from __future__ import annotations

import json
import sqlite3

CARD_ID = "demo-rollback-48"

SCENARIO = {
    "id": "rollback",
    "kind": "feature",
    "batch": 8,
    "item": "F-25",
    "title": "Rollback planning",
    "blurb": ("Order the rollback steps for a bad deploy -- freeze, flag, "
              "revert, verify."),
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 8 - Feature F-25",
         "title": "Rollback planning",
         "subtitle": "Five steps, one safe order -- freeze first, verify last."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b8-rollback",
         "caption": ("Status homes the type: exact sequence, adjacent-pair "
                     "partial credit."),
         "assert_js": "() => !!document.querySelector('#status-b8-rollback')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": ("The rule in one line: the safe order passes; shuffled "
                     "pairs score partial."),
         "commands": [
             ["python3", "-c",
              "from groundwork import rollback as m; "
              "ex = {'payload': {'steps': ['a','b','c','d','e'], 'order': [0,2,1,3,4]}}; "
              "print(m.grade(ex, '1 3 2 4 5')['feedback']); "
              "print(m.grade(ex, '1 2 3 4 5')['feedback'])"],
         ]},
        {"type": "chrome", "duration": 8,
         "url_path": "/due",
         "focus": "#card-{seed_card_id}",
         "caption": "The rollback card: five shuffled steps, one safe order to find.",
         "assert_js": "() => { const f = document.querySelector("
                      "\"form[action='/cards/{seed_card_id}/review']\"); "
                      "return !!f && !!f.querySelector(\"input[name='answer']\") && "
                      "document.body.innerText.includes('rollback steps') && "
                      "document.body.innerText.includes('Down-migrate'); }",
         "assert_want": "True"},
        {"type": "chrome", "duration": 13,
         "url_path": "/due",
         "caption": ("Freeze, flag, revert, migrate, verify -- the verdict "
                     "confirms the order."),
         "js": ["() => { const f = document.querySelector(\"form[action='/cards/{seed_card_id}/review']\"); "
                "if (!f) return 'seed-form-missing'; "
                "const inp = f.querySelector(\"input[name='answer']\"); "
                "if (!inp) return 'no-input'; inp.value = {seed_answer_js}; "
                "const conf = f.querySelector(\"input[name='confidence'][value='4']\"); "
                "if (conf) conf.checked = true; "
                "f.submit(); return 'submitted'; }"],
         "poll_js": "() => document.body.innerText.slice(0, 12000)",
         "poll_want": "Correct rollback order",
         "poll_required": True,
         "poll_timeout": 25,
         "assert_js": "() => !!document.querySelector('.verdict-stamp') && "
                      "document.body.innerText.includes('5/5 steps')",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 8",
         "title": "Undo in the safe order.",
         "subtitle": ("rollback.py grades the sequence -- exact to pass, "
                      "pairs for partial.")},
    ],
}


def seed_db(db_path: str) -> dict:
    """Plant one type-48 card (generate() bytes) as the sole due card."""
    steps = ["Freeze the rollout of `checkout` \u2014 stop the bleeding, no new deploys.",
             "Roll back the deploy of `checkout` to the last good release.",
             "Flip the feature flag / route traffic back to the previous release.",
             "Down-migrate the migration that shipped with it (newest first).",
             "Verify health (smoke checks + error rate), then re-enable rollout."]
    solution = [steps[0], steps[2], steps[1], steps[3], steps[4]]
    front = ("A change to `checkout` (service) went bad in production: "
             "migration + deploy + flag-flip all shipped together.\n"
             "Put these 5 rollback steps in the safe order (first step first). "
             "Reply with space-separated step numbers.\n"
             + "\n".join(f"{i + 1}. {s}" for i, s in enumerate(steps)))
    back = "\n".join(f"{i + 1}. {s}" for i, s in enumerate(solution))
    payload = {"steps": steps, "order": [0, 2, 1, 3, 4], "solution": solution,
               "scenario": "migration + deploy + flag-flip rollback",
               "grounded": True}
    answer = "1 3 2 4 5"
    con = sqlite3.connect(db_path)
    try:
        row = con.execute(
            "SELECT id FROM concepts ORDER BY rowid LIMIT 1").fetchone()
        if not row:
            return {"seeded": False, "reason": "no concepts"}
        con.execute("UPDATE cards SET due='2030-01-01T00:00:00Z'")
        # Type 48 is the Decide stage of the gated incident-commander
        # track; clear Replay (77) + Diagnose (76) with two passing
        # proofs each so the seeded card is dealt, not withheld.
        for stub_id, etype in (("demo-rb-track-77", "77"),
                               ("demo-rb-track-76", "76")):
            con.execute("DELETE FROM reviews WHERE card_id=?", (stub_id,))
            con.execute(
                "INSERT OR REPLACE INTO cards(id, concept_id, exercise_type,"
                " front, back, payload, due)"
                " VALUES(?, ?, ?, 'track stub', 'track stub', '{}',"
                " '2030-01-01T00:00:00Z')",
                (stub_id, row[0], etype))
            con.execute(
                "INSERT INTO reviews(card_id, grade, confidence)"
                " VALUES(?, 5, 4), (?, 5, 4)", (stub_id, stub_id))
        con.execute("DELETE FROM reviews WHERE card_id=?", (CARD_ID,))
        con.execute(
            "INSERT OR REPLACE INTO cards(id, concept_id, exercise_type,"
            " front, back, payload, due)"
            " VALUES(?, ?, '48', ?, ?, ?, '2000-01-01T00:00:00Z')",
            (CARD_ID, row[0], front, back, json.dumps(payload)))
        con.commit()
        return {"seeded": True, "card_id": CARD_ID,
                "answer_js": json.dumps(json.dumps(answer))[1:-1]}
    finally:
        con.close()
