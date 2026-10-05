"""Feature demo: spacing optimizer (F-62).

Full behavior: the scheduler stretches the due gap by the trailing
pass streak (since Batch 14) -- consecutive passes multiply the gap
x2.2 to a 60-day ceiling, any fail collapses to tomorrow. seed_db
builds a 4-pass streak on a rubric card; the /due beat answers from
the rubric and the verdict must land over a week out.
"""
from __future__ import annotations

import json
import re
import sqlite3


def _clean(text) -> str:
    return re.sub(r"\s+", " ", str(text or "")).replace(
        '"', "").replace("'", "").replace("\\", "")[:300]


SCENARIO = {
    "id": "spacingopt",
    "kind": "feature",
    "batch": 13,
    "item": "F-62",
    "title": "Spacing optimizer",
    "blurb": "Strong ideas stretch out, fragile ones return tomorrow.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 13 - Feature F-62",
         "title": "Spacing optimizer",
         "subtitle": "Strong ideas stretch out, fragile ones return tomorrow."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b13-spacingopt",
         "caption": "Status homes the engine: same history shape, two learners, two gaps.",
         "assert_js": "() => !!document.querySelector('#status-b13-spacingopt')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 8,
         "caption": "The rule in one line: four straight passes stretch, a recent fail returns.",
         "commands": [
             ["python3", "-c",
              "from groundwork import spacingopt as m; "
              "print('strong:', m.next_interval([5, 4, 5, 5])); "
              "print('fragile:', m.next_interval([5, 5, 2])); "
              "print(m.describe([5, 4, 5, 5])); "
              "print(m.describe([5, 5, 2]))"],
         ]},
        {"type": "chrome", "duration": 14,
         "url_path": "/due",
         "caption": "Answer the streak card right -- the verdict lands weeks out, not tomorrow.",
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
         "kicker": "Groundwork - Batch 13",
         "title": "Earned distance.",
         "subtitle": "spacingopt.py stretches sched -- collapse stays the stability model's job."},
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
