"""Improvement demo: grading disclosures (Batch 3, I-181).

Full functionality: every Due card discloses how it is judged before
you answer (grading.disclosure_html, one contract per exercise type).
seed_db parks the queue to a rubric card (type 5, planted 4-point
rubric) plus a sandbox card (type 12); the submit beat answers thinly
and the verdict follows the disclosed contract (covered 0/4, missing
points listed).
"""
from __future__ import annotations

import json
import re
import sqlite3

_ANCHOR_OK = re.compile(r"[A-Za-z0-9_-]+")


def _slug(text: str) -> str:
    """Mirror scrollpos.card_anchor: keep [A-Za-z0-9_-], cap at 48."""
    return "".join(_ANCHOR_OK.findall((text or "").strip()))[:48] or "unknown"


SCENARIO = {
    "id": "grading-how",
    "kind": "improvement",
    "batch": 3,
    "item": "I-181",
    "title": "Grading disclosures",
    "blurb": "Every card says how it is judged before you answer.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 3 - Improvement I-181",
         "title": "Grading disclosures",
         "subtitle": "Every card says how it is judged before you answer."},
        {"type": "chrome", "duration": 9,
         "url_path": "/due",
         "focus": "#grading",
         "caption": "The lead card's contract, opened: cover half the key points.",
         "js": ["() => { const d = document.querySelector('#grading'); "
                "if (!d) return 'grading-missing'; d.open = true; "
                "return d.textContent.slice(0, 200); }"],
         "assert_js": "() => { const d = document.querySelector('#grading'); "
                      "return d ? d.textContent : 'missing'; }",
         "assert_want": "half the key points"},
        {"type": "terminal", "duration": 7,
         "caption": "One contract per exercise type, mirroring the real grader.",
         "commands": [
             ["python3", "-c",
              "from groundwork import grading as g; "
              "print('type 5:', g.disclosure('5')); "
              "print('type 12:', g.disclosure('12'))"],
         ]},
        {"type": "chrome", "duration": 12,
         "url_path": "/due",
         "caption": "Answer thinly and the verdict follows the contract: 0/4, missing listed.",
         "js": ["() => { const f = document.querySelector(\"form[action='/cards/{seed_c_rub}/review']\"); "
                "if (!f) return 'seed-form-missing'; "
                "const ta = f.querySelector('textarea[name=answer]'); "
                "if (!ta) return 'no-textarea'; ta.value = 'nothing relevant here'; "
                "const conf = f.querySelector(\"input[name='confidence'][value='4']\"); "
                "if (conf) conf.checked = true; "
                "f.submit(); return 'submitted'; }"],
         "poll_js": "() => document.body.innerText.slice(0, 12000)",
         "poll_want": "key points",
         "poll_required": True,
         "poll_timeout": 25,
         "assert_js": "() => document.body.innerText.slice(0, 12000)",
         "assert_want": "Missing: alpha"},
        {"type": "chrome", "duration": 8,
         "url_path": "/due",
         "focus": "#grading",
         "caption": "The code card's contract: hidden tests, all green to pass.",
         "js": ["() => { const d = document.querySelector('#grading'); "
                "if (!d) return 'grading-missing'; d.open = true; "
                "return d.textContent.slice(0, 200); }"],
         "assert_js": "() => { const d = document.querySelector('#grading'); "
                      "return d ? d.textContent : 'missing'; }",
         "assert_want": "sandbox"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 3",
         "title": "No surprise verdicts.",
         "subtitle": "grading.disclosure mirrors exercises.grade, type by type."},
    ],
}


def seed_db(db_path: str) -> dict:
    """A type-5 rubric card due-first plus a type-12 sandbox card second.

    The rubric card gets a planted 4-point rubric (library type-5 rows
    carry none); everything else parks in 2999 and reviews wipe, so the
    queue holds exactly these two with zero probes.
    """
    con = sqlite3.connect(db_path)
    try:
        rub = con.execute(
            "SELECT id, concept_id FROM cards WHERE exercise_type='5'"
            " ORDER BY due LIMIT 5").fetchall()
        exe = con.execute(
            "SELECT id, concept_id FROM cards WHERE exercise_type='12'"
            " ORDER BY due LIMIT 6").fetchall()
        if not rub or not exe:
            return {"seeded": False, "reason": "need type 5 + type 12"}
        c_rub = rub[0][0]
        c_exec = next((cid for cid, _ in exe if cid != c_rub), None)
        if c_exec is None:
            return {"seeded": False, "reason": "need distinct cards"}
        payload = json.dumps({"hints": [],
                              "rubric": ["alpha", "beta", "gamma", "delta"]})
        con.execute("DELETE FROM reviews")
        con.execute("UPDATE cards SET due='2999-01-01T00:00:00Z'")
        con.execute("UPDATE cards SET due='2000-01-01T00:00:00Z',"
                    " stability=1.0, lapses=0, payload=? WHERE id=?",
                    (payload, c_rub))
        con.execute("UPDATE cards SET due='2000-01-02T00:00:00Z',"
                    " stability=1.0, lapses=0 WHERE id=?", (c_exec,))
        con.commit()
        return {"seeded": True, "c_rub": c_rub, "c_exec": c_exec,
                "a_rub": _slug(c_rub), "a_exec": _slug(c_exec)}
    finally:
        con.close()
