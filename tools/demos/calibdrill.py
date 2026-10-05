"""Feature demo: calibration drills (F-66).

Full behavior: every confidence widget shows explicit win/lose odds
per level, and each verdict settles the stated bet at fair odds (since
Batch 15 -- the banked currency stays the review score, shown beside
it). seed_db forces a rubric card due with its rubric-join answer; the
submit beat answers at confidence 4 and must settle +2.
"""
from __future__ import annotations

import json
import re
import sqlite3


def _clean(text) -> str:
    return re.sub(r"\s+", " ", str(text or "")).replace(
        '"', "").replace("'", "").replace("\\", "")[:300]


SCENARIO = {
    "id": "calibdrill",
    "kind": "feature",
    "batch": 13,
    "item": "F-66",
    "title": "Calibration drills",
    "blurb": "Bet points at explicit odds -- fair when honest, profitable when calibrated.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 13 - Feature F-66",
         "title": "Calibration drills",
         "subtitle": "Bet points at explicit odds -- profitable only when calibrated."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b13-calibdrill",
         "caption": "Status homes the drill with a live odds card: bet only what you believe.",
         "assert_js": "() => !!document.querySelector('#status-b13-calibdrill') && "
                      "!!document.querySelector('.calib-drill')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 8,
         "caption": "The rule in one line: fair at the honest probability -- bravado earns nothing.",
         "commands": [
             ["python3", "-c",
              "from groundwork import calibdrill as m; "
              "deal = m.offer(4); "
              "print('conf 4:', deal); "
              "print('settle right/wrong:', m.settle(4, True), m.settle(4, False)); "
              "ev = deal['p'] * deal['win'] + (1 - deal['p']) * deal['lose']; "
              "print('honest EV: %.2f' % ev)"],
         ]},
        {"type": "chrome", "duration": 10,
         "url_path": "/due",
         "focus": ".confslider",
         "caption": "Every confidence widget shows its price: win and lose at fair odds, 1 through 5.",
         "assert_js": "() => { const o = document.querySelector('.odds'); "
                      "return !!o && o.textContent.includes('Odds'); }",
         "assert_want": "True"},
        {"type": "chrome", "duration": 12,
         "url_path": "/due",
         "caption": "Answer right at confidence 4 -- the verdict settles the stated bet.",
         "js": ["() => { const f = document.querySelector(\"form[action='/cards/{seed_card_id}/review']\"); "
                "if (!f) return 'seed-form-missing'; "
                "const ta = f.querySelector('textarea[name=answer]'); "
                "if (!ta) return 'no-textarea'; ta.value = '{seed_answer}'; "
                "const conf = f.querySelector(\"input[name='confidence'][value='4']\"); "
                "if (conf) conf.checked = true; "
                "f.submit(); return 'submitted'; }"],
         "poll_js": "() => document.body.innerText.slice(0, 12000)",
         "poll_want": "Drill: stated",
         "poll_required": True,
         "poll_timeout": 25,
         "assert_js": "() => document.body.innerText.includes('stated 80%') && "
                      "document.body.innerText.includes('settled +2')",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 13",
         "title": "Bet only what you believe.",
         "subtitle": "calibdrill.py prices every confidence -- widgets quote, verdicts settle."},
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
