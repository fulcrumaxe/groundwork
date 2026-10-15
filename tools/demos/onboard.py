"""Feature demo: 30-day onboarding countdown (F-135).

Full behavior: a module shows day N of 30 from the learner's first
review plus a core-flow checklist (entry points, then
most-depended-upon). Outside the window it renders nothing.
seed_db restarts the first module's clock 5 days ago (day 6).
"""
from __future__ import annotations

import sqlite3
from datetime import date, timedelta

SCENARIO = {
    "id": "onboard",
    "kind": "feature",
    "batch": 25,
    "item": "F-135",
    "title": "Onboarding countdown",
    "blurb": "Day N of 30 with the core flows to own first.",
    "beats": [
        {"type": "title", "duration": 4,
         "kicker": "Batch 25 - Feature F-135",
         "title": "Onboarding countdown",
         "subtitle": "New here? Day 6 of 30 -- own these flows first."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b25-onboard",
         "caption": "Status names the window: 30 days, then silent.",
         "assert_js": "() => !!document.querySelector('#status-b25-onboard') "
                      "&& document.body.innerText.includes('day N of 30')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "Entry points first, then most-depended-upon.",
         "commands": [
             ["python3", "-c",
              "from groundwork import onboard as m; "
              "print('day:', m.day_of('2026-10-10', '2026-10-15')); "
              "ls = [{'name': 'serve', 'needs': ['route']}, {'name': 'route'}]; "
              "print([f['name'] for f in m.core_flows(ls)]); "
              "print('active:', m.is_active('2026-10-10', '2026-10-15'))"],
         ]},
        {"type": "chrome", "duration": 10,
         "url_path": "/modules/{seed_module}",
         "focus": "#onboard",
         "caption": "The module banner: day 6 of 30, core flows listed.",
         "assert_js": "() => !!document.querySelector('#onboard') "
                      "&& document.body.innerText.includes('Day 6 of 30')",
         "assert_want": "True"},
        {"type": "title", "duration": 4,
         "kicker": "Groundwork - Batch 25",
         "title": "Gentle first month.",
         "subtitle": "onboard.py counts from first review -- no streaks."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Restart the first carded module's clock 5 days ago (day 6)."""
    con = sqlite3.connect(db_path)
    try:
        mod = con.execute(
            "SELECT modules.id FROM modules JOIN concepts"
            " ON concepts.module_id = modules.id JOIN cards"
            " ON cards.concept_id = concepts.id"
            " GROUP BY modules.id ORDER BY modules.rowid LIMIT 1").fetchone()
        if not mod:
            return {"seeded": False, "reason": "no carded modules"}
        mid = mod[0]
        card = con.execute(
            "SELECT cards.id FROM cards JOIN concepts"
            " ON concepts.id = cards.concept_id"
            " WHERE concepts.module_id=? ORDER BY cards.rowid LIMIT 1",
            (mid,)).fetchone()
        if not card:
            return {"seeded": False, "reason": "no cards"}
        five_ago = (date.today() - timedelta(days=5)).strftime("%Y-%m-%d")
        con.execute(
            "DELETE FROM reviews WHERE card_id IN (SELECT cards.id FROM cards"
            " JOIN concepts ON concepts.id = cards.concept_id"
            " WHERE concepts.module_id=?)",
            (mid,))
        con.execute(
            "INSERT INTO reviews(card_id, grade, confidence, reviewed_at,"
            " submission) VALUES(?, 3, 3, ?, 'onboard seed')",
            (card[0], f"{five_ago}T12:00:00Z"))
        con.commit()
        return {"seeded": True, "module": mid}
    finally:
        con.close()
