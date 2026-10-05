"""Feature demo: overconfidence cards (F-67).

Full behavior: when mean confidence outruns accuracy by 25+ points
over 10+ attempts, History deals an intervention card naming the
weakest skill plus one counter-habit (since Batch 15 -- small samples
and underconfidence stay silent). seed_db plants twelve skewed
reviews (grades 1,1,2 at confidence 5) on one exercise type.
"""
from __future__ import annotations

import sqlite3

SKEW_GRADES = (1, 1, 2)
CARDS_NEEDED = 4

SCENARIO = {
    "id": "overconf",
    "kind": "feature",
    "batch": 13,
    "item": "F-67",
    "title": "Overconfidence cards",
    "blurb": "A 25-point gap deals a card: weakest skill plus one counter-habit.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 13 - Feature F-67",
         "title": "Overconfidence cards",
         "subtitle": "A 25-point gap deals a card -- weakest skill plus one counter-habit."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b13-overconf",
         "caption": "Status homes the card with a live 34-point dealt sample.",
         "assert_js": "() => !!document.querySelector('#status-b13-overconf') && "
                      "!!document.querySelector('.overconf-card')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 8,
         "caption": "The rule in one line: big gap plus enough attempts deals, anything else stays silent.",
         "commands": [
             ["python3", "-c",
              "from groundwork import overconf as m; "
              "print('gap:', round(m.gap(0.25, 5.0), 2)); "
              "print('deal:', m.needs_intervention(0.34, 24), '| small-n:', m.needs_intervention(0.34, 5)); "
              "print('silent:', repr(m.intervention_html(0.1, 'x', 24)) == repr(''))"],
         ]},
        {"type": "chrome", "duration": 11,
         "url_path": "/reviews",
         "focus": ".overconf-card",
         "caption": "History deals the card from live attempts: gap stated, weakest skill named.",
         "assert_js": "() => { const c = document.querySelector('.overconf-card'); "
                      "return !!c && c.textContent.includes('Overconfidence check'); }",
         "assert_want": "True"},
        {"type": "terminal", "duration": 5,
         "caption": "Proof in the fixture DB: twelve skewed attempts behind the dealt card.",
         "commands": [
             ["python3", "-c",
              "import os, sqlite3; con = sqlite3.connect(os.environ.get('DEMO_DB', 'groundwork.db')); "
              "row = con.execute(\"SELECT COUNT(*), AVG(grade), AVG(confidence) FROM reviews"
              " WHERE submission='overconf seed'\").fetchone(); "
              "print('attempts:', row[0], '| avg grade:', round(row[1], 1), '| avg conf:', round(row[2], 1))"],
         ]},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 13",
         "title": "Bet only what you earned.",
         "subtitle": "overconf.py coaches History -- the gap deals, the habit follows."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Twelve skewed reviews on one exercise type (stable weakest skill)."""
    con = sqlite3.connect(db_path)
    try:
        group = con.execute(
            "SELECT exercise_type FROM cards GROUP BY exercise_type"
            " HAVING COUNT(*) >= ? ORDER BY COUNT(*) DESC LIMIT 1",
            (CARDS_NEEDED,)).fetchone()
        if not group:
            return {"seeded": False, "reason": "no card group"}
        etype = group[0]
        ids = [r[0] for r in con.execute(
            "SELECT id FROM cards WHERE exercise_type=? ORDER BY rowid"
            " LIMIT ?", (etype, CARDS_NEEDED)).fetchall()]
        for cid in ids:
            for grade in SKEW_GRADES:
                con.execute(
                    "INSERT INTO reviews(card_id, grade, confidence,"
                    " submission) VALUES(?, ?, 5, 'overconf seed')",
                    (cid, grade))
        con.commit()
        return {"seeded": True, "etype": etype,
                "attempts": len(ids) * len(SKEW_GRADES)}
    finally:
        con.close()
