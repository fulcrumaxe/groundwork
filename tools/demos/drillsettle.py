"""Feature demo: verdicts settle the stated bet (F-66 integration).

Full behavior: every confidence states a bet at explicit fair odds,
and the verdict settles it -- win on the right, lose on the wrong --
while the banked currency stays the review score beside it (one
account). seed_db forces a rubric card due; the /due beat answers
wrong at confidence 4 and must settle -8 with banked -4 beside it.
"""
from __future__ import annotations

import json
import sqlite3

WRONG_ANSWER = "xylophone zebra quasar xyzzy"

SCENARIO = {
    "id": "drillsettle",
    "kind": "feature",
    "batch": 15,
    "item": "F-66",
    "title": "Verdicts settle the bet",
    "blurb": "Every confidence states odds -- the verdict settles win or lose beside the banked score.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 15 - Feature F-66",
         "title": "Verdicts settle the bet",
         "subtitle": "Every confidence states odds -- the verdict settles win or lose."},
        {"type": "terminal", "duration": 8,
         "caption": "The ladder in one call: fair odds per level, settled both ways.",
         "commands": [
             ["python3", "-c",
              "from groundwork import calibdrill as m; "
              "print('odds:', ' '.join(f\"{c}->{m.offer(c)['win']}/{m.offer(c)['lose']}\" for c in (1, 2, 3, 4, 5))); "
              "print('conf 4 right:', m.settle(4, True), '| conf 4 wrong:', m.settle(4, False)); "
              "deal = m.offer(4); "
              "ev = deal['p'] * deal['win'] + (1 - deal['p']) * deal['lose']; "
              "print('honest EV at 80pct:', round(ev, 2))"],
         ]},
        {"type": "chrome", "duration": 13,
         "url_path": "/due",
         "caption": "Wrong at confidence 4 -- the verdict settles -8, banked -4 beside it.",
         "js": ["() => { const f = document.querySelector(\"form[action='/cards/{seed_card_id}/review']\"); "
                "if (!f) return 'seed-form-missing'; "
                "const ta = f.querySelector('textarea[name=answer]'); "
                "if (!ta) return 'no-textarea'; ta.value = '" + WRONG_ANSWER + "'; "
                "const conf = f.querySelector(\"input[name='confidence'][value='4']\"); "
                "if (conf) conf.checked = true; "
                "f.submit(); return 'submitted'; }"],
         "poll_js": "() => document.body.innerText.slice(0, 12000)",
         "poll_want": "Drill: stated",
         "poll_required": True,
         "poll_timeout": 25,
         "assert_js": "() => document.body.innerText.includes('stated 80%') && "
                      "document.body.innerText.includes('settled -8') && "
                      "document.body.innerText.includes('banked -4')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 4,
         "caption": "Proof in the fixture DB: fail grade banked -4 -- grades stay pass/fail.",
         "commands": [
             ["python3", "-c",
              "import os, sqlite3; con = sqlite3.connect(os.environ.get('DEMO_DB', 'groundwork.db')); "
              "row = con.execute(\"SELECT grade, points FROM reviews"
              " WHERE card_id='{seed_card_id}' ORDER BY id DESC LIMIT 1\").fetchone(); "
              "print('grade:', row[0], '| points:', row[1])"],
         ]},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 15",
         "title": "Stated, then settled.",
         "subtitle": "One account: the drill settles fair odds, the bank keeps score()."},
    ],
}


def seed_db(db_path: str) -> dict:
    """One rubric card due-now (answered wrong at confidence 4)."""
    con = sqlite3.connect(db_path)
    try:
        rows = con.execute(
            "SELECT id, payload FROM cards WHERE exercise_type IN ('5','6')"
            " ORDER BY rowid").fetchall()
        pick = None
        for cid, payload in rows:
            try:
                rub = [r for r in json.loads(payload or "{}").get(
                    "rubric", []) if r]
            except ValueError:
                continue
            if rub:
                pick = cid
                break
        if not pick:
            return {"seeded": False, "reason": "no rubric card"}
        con.execute("UPDATE cards SET due='2000-01-01T00:00:00Z' WHERE id=?",
                    (pick,))
        con.commit()
        return {"seeded": True, "card_id": pick}
    finally:
        con.close()
