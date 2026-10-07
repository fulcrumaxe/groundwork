"""Feature demo: streaks stretch the schedule (F-62 integration).

Full behavior: submit_review feeds the trailing grade history into
sched.review_card(grades=) (Batch 14) -- a pass streak stretches the
due gap past the legacy date, while a trailing fail keeps the legacy
gap exactly. seed_db builds a 4-pass streak on a rubric card; the
/due beat answers from the rubric and the verdict must land over a
week out.
"""
from __future__ import annotations

import json
import re
import sqlite3


def _clean(text) -> str:
    return re.sub(r"\s+", " ", str(text or "")).replace(
        '"', "").replace("'", "").replace("\\", "")[:300]


SCENARIO = {
    "id": "streaksched",
    "kind": "feature",
    "batch": 14,
    "item": "F-62",
    "title": "Streaks stretch the schedule",
    "blurb": "submit_review feeds trailing grades to sched -- strong cards return later.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 14 - Feature F-62",
         "title": "Streaks stretch the schedule",
         "subtitle": "submit_review feeds trailing grades to sched -- strong cards return later."},
        {"type": "terminal", "duration": 8,
         "caption": "The seam in one call: trailing grades stretch review_card; a trailing fail keeps legacy.",
         "commands": [
             ["python3", "-c",
              "from groundwork import sched as m; "
              "now = m.utcnow(); "
              "kw = dict(stability=4.0, difficulty=0.5, grade=5, now=now); "
              "print('legacy: ', m.review_card(**kw)['due']); "
              "print('streak4:', m.review_card(grades=[5, 5, 5, 5], **kw)['due']); "
              "print('fail==legacy:', "
              "m.review_card(9.0, 0.5, 2, grades=[5, 5, 5, 2])['due'] "
              "== m.review_card(9.0, 0.5, 2)['due'])"],
         ]},
        {"type": "chrome", "duration": 14,
         "url_path": "/due",
         "caption": "submit_review feeds the trailing streak to sched -- the verdict stretches weeks out.",
         "js": ["() => { const f = document.querySelector(\"form[action='/cards/{seed_card_id}/review']\"); "
                "if (!f) return 'seed-form-missing'; "
                "const ta = f.querySelector('textarea[name=answer]'); "
                "if (!ta) return 'no-textarea'; ta.value = '{seed_answer}'; "
                "const conf = f.querySelector(\"input[name='confidence'][value='4']\"); "
                "if (conf) conf.checked = true; "
                "f.submit(); return 'submitted'; }"],
         "poll_js": "() => document.body.innerText.slice(0, 12000)",
         "poll_want": "Next review:",
         "poll_required": True,
         "poll_timeout": 25,
         "assert_js": "() => { const m = document.body.innerText.match(/Next review: (\\S+)/); "
                      "if (!m) return 'no-date'; "
                      "const days = (new Date(m[1]) - Date.now()) / 864e5; "
                      "return days > 7 ? 'stretched' : 'short:' + days.toFixed(1); }",
         "assert_want": "stretched"},
        {"type": "terminal", "duration": 5,
         "caption": "Proof in the fixture DB: five straight passes, due weeks out.",
         "commands": [
             ["python3", "-c",
              "import os, sqlite3; con = sqlite3.connect(os.environ.get('DEMO_DB', 'groundwork.db')); "
              "due = con.execute(\"SELECT due FROM cards WHERE id='{seed_card_id}'\").fetchone()[0]; "
              "n = con.execute(\"SELECT COUNT(*) FROM reviews WHERE card_id='{seed_card_id}' AND grade >= 4\").fetchone()[0]; "
              "print('passes:', n, '| due:', due)"],
         ]},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 14",
         "title": "Earned distance, wired in.",
         "subtitle": "submit_review hands trailing history to sched.review_card(grades=)."},
    ],
}


def seed_db(db_path: str) -> dict:
    """A 4-pass streak on a rubric card, plus its rubric-join answer."""
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
        con.execute("UPDATE cards SET due='2000-01-01T00:00:00Z',"
                    " stability=5.0, difficulty=0.5 WHERE id=?", (cid,))
        con.execute("DELETE FROM reviews WHERE card_id=?", (cid,))
        for grade in (5, 4, 5, 5):
            con.execute(
                "INSERT INTO reviews(card_id, grade, confidence)"
                " VALUES(?, ?, 3)", (cid, grade))
        con.commit()
        return {"seeded": True, "card_id": cid, "answer": answer}
    finally:
        con.close()
