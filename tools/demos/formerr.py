"""Improvement demo: inline form errors (I-84).

Full behavior: a review POST with a present-but-bad confidence renders
a role='alert' .field-error line naming the fix atop the result page,
while the grade still lands on the server default. seed_db forces one
rubric card due-first and returns its rubric-join answer; the /due beat
flips a confidence radio to 9 and native-submits through the real form.
"""
from __future__ import annotations

import json
import re
import sqlite3


def _clean(text) -> str:
    return re.sub(r"\s+", " ", str(text or "")).replace(
        '"', "").replace("'", "").replace("\\", "")[:300]


SCENARIO = {
    "id": "formerr",
    "kind": "improvement",
    "batch": 13,
    "item": "I-84",
    "title": "Inline form errors",
    "blurb": "Out-of-range input fails loudly beside the field -- not silence.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 13 - Improvement I-84",
         "title": "Inline form errors",
         "subtitle": "Out-of-range input fails loudly beside the field -- not silence."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b13-formerr",
         "caption": "Status documents the alert line: role=alert, field named, fix named.",
         "assert_js": "() => !!document.querySelector('#status-b13-formerr')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "The rule in one line: bad values name 1-5, missing keys stay silent.",
         "commands": [
             ["python3", "-c",
              "from groundwork import formerr as m; "
              "print('9:', repr(m.confidence_error('9'))); "
              "print('4:', repr(m.confidence_error('4'))); "
              "print('missing:', repr(m.review_note('answer=x'))); "
              "print('bad post:', 'alert' in m.review_note('answer=x&confidence=9'))"],
         ]},
        {"type": "chrome", "duration": 14,
         "url_path": "/due",
         "caption": "Submit confidence 9 through the real form -- the result names the fix inline.",
         "js": ["() => { const f = document.querySelector(\"form[action='/cards/{seed_card_id}/review']\"); "
                "if (!f) return 'seed-form-missing'; "
                "const ta = f.querySelector('textarea[name=answer]'); "
                "if (ta) ta.value = '{seed_answer}'; "
                "const conf = f.querySelector(\"input[name='confidence'][value='5']\"); "
                "if (!conf) return 'no-radio'; conf.value = '9'; conf.checked = true; "
                "f.submit(); return 'submitted'; }"],
         "poll_js": "() => document.body.innerText.slice(0, 12000)",
         "poll_want": "out of range",
         "poll_required": True,
         "poll_timeout": 25,
         "assert_js": "() => { const e = document.querySelector('.field-error'); "
                      "return !!e && e.getAttribute('role') === 'alert' && e.textContent.includes('9'); }",
         "assert_want": "True"},
        {"type": "terminal", "duration": 5,
         "caption": "The grade still lands on the default -- the complaint is on record, nothing is lost.",
         "commands": [
             ["python3", "-c",
              "import os, sqlite3; con = sqlite3.connect(os.environ.get('DEMO_DB', 'groundwork.db')); "
              "row = con.execute(\"SELECT confidence, grade FROM reviews WHERE card_id='{seed_card_id}'"
              " ORDER BY rowid DESC LIMIT 1\").fetchone(); "
              "print('stored confidence:', row[0], '| grade:', row[1])"],
         ]},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 13",
         "title": "Loud beside the field.",
         "subtitle": "formerr.py alerts on the result page -- the review POST prepends it."},
    ],
}


def seed_db(db_path: str) -> dict:
    """One rubric card due-now plus its rubric-join answer.

    The beat posts a real answer with a flipped confidence, so the
    seeded answer must survive JSON + JS single-quote embedding:
    whitespace-flattened, both quote kinds stripped.
    """
    con = sqlite3.connect(db_path)
    try:
        rows = con.execute(
            "SELECT id, payload FROM cards WHERE exercise_type IN ('5','6')"
        ).fetchall()
        pick = None
        for cid, payload in rows:
            try:
                rub = [r for r in json.loads(payload or "{}").get(
                    "rubric", []) if r]
            except ValueError:
                continue
            if rub:
                pick = (cid, rub)
                break
        if not pick:
            return {"seeded": False, "reason": "no rubric card"}
        cid, rub = pick
        answer = _clean(" ".join(rub))
        if not answer:
            return {"seeded": False, "reason": "empty rubric"}
        con.execute("UPDATE cards SET due='2000-01-01T00:00:00Z' WHERE id=?",
                    (cid,))
        con.commit()
        return {"seeded": True, "card_id": cid, "answer": answer}
    finally:
        con.close()
