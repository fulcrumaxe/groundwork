"""Feature demo: confidence-weighted scoring (F-65).

Full behavior: every submit banks signed points (right earns its
confidence, wrong loses it) into reviews.points; the verdict shows
the line and History totals the bank (since Batch 15 -- grades stay
pass/fail). seed_db forces a rubric card due with its rubric-join
answer; the /due beat answers at confidence 5 and must bank +5.
"""
from __future__ import annotations

import json
import re
import sqlite3


def _clean(text) -> str:
    return re.sub(r"\s+", " ", str(text or "")).replace(
        '"', "").replace("'", "").replace("\\", "")[:300]


SCENARIO = {
    "id": "confweight",
    "kind": "feature",
    "batch": 13,
    "item": "F-65",
    "title": "Confidence-weighted scoring",
    "blurb": "Brave-correct beats shy-correct -- calibration pays.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 13 - Feature F-65",
         "title": "Confidence-weighted scoring",
         "subtitle": "Brave-correct beats shy-correct -- calibration pays."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b13-confweight",
         "caption": "Status homes the engine: the four outcomes, computed live.",
         "assert_js": "() => !!document.querySelector('#status-b13-confweight')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 8,
         "caption": "The rule in one line: brave-correct 5, shy-correct 1, shy-wrong -1, brave-wrong -5.",
         "commands": [
             ["python3", "-c",
              "from groundwork import confweight as m; "
              "print('ladder:', m.score(True, 5), m.score(True, 1), m.score(False, 1), m.score(False, 5)); "
              "print(m.rank_line(4)); "
              "print('missing:', m.score(None, 5), '| clamped:', m.score(True, 99))"],
         ]},
        {"type": "chrome", "duration": 14,
         "url_path": "/due",
         "caption": "Answer right at confidence 5 -- the verdict banks +5 on the spot.",
         "js": ["() => { const f = document.querySelector(\"form[action='/cards/{seed_card_id}/review']\"); "
                "if (!f) return 'seed-form-missing'; "
                "const ta = f.querySelector('textarea[name=answer]'); "
                "if (!ta) return 'no-textarea'; ta.value = '{seed_answer}'; "
                "const conf = f.querySelector(\"input[name='confidence'][value='5']\"); "
                "if (conf) conf.checked = true; "
                "f.submit(); return 'submitted'; }"],
         "poll_js": "() => document.body.innerText.slice(0, 12000)",
         "poll_want": "Calibration banked",
         "poll_required": True,
         "poll_timeout": 25,
         "assert_js": "() => document.body.innerText.includes('Calibration banked +5 pts')",
         "assert_want": "True"},
        {"type": "chrome", "duration": 7,
         "url_path": "/reviews",
         "focus": "#calibration",
         "caption": "History totals the bank: every point earned or paid, summed beside accuracy.",
         "assert_js": "() => { const c = document.querySelector('#calibration'); "
                      "return !!c && c.textContent.includes('bank'); }",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 13",
         "title": "Brave when right, humble when not.",
         "subtitle": "confweight.py banks every submit -- one account, verdict and History agree."},
    ],
}


def seed_db(db_path: str) -> dict:
    """One rubric card due-now plus its rubric-join (passing) answer."""
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
