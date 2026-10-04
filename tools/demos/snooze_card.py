"""Improvement demo: snooze a card (Batch 2, I-45).

Full functionality: POSTing a card's snooze form pushes its due date
to tomorrow without recording any grade. seed_db clears the queue to
exactly one card with no reviews; the /due interaction beat
native-submits its snooze form (landing on the full Snoozed page)
and the terminal beat shows the pushed due date plus zero reviews.
"""
from __future__ import annotations

import sqlite3

SCENARIO = {
    "id": "snooze-card",
    "kind": "improvement",
    "batch": 2,
    "item": "I-45",
    "title": "Snooze a card",
    "blurb": "Not today? Snooze pushes one card to tomorrow \u2014 no grade recorded.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 2 - Improvement I-45",
         "title": "Snooze a card",
         "subtitle": "Not today? Snooze pushes one card to tomorrow -- no grade recorded."},
        {"type": "chrome", "duration": 7,
         "url_path": "/due",
         "focus": "#snooze",
         "caption": "Every Due card ends with Snooze until tomorrow -- the honest deferral.",
         "assert_js": "() => { const b = document.querySelector('#snooze'); "
                      "return b ? b.textContent : 'missing'; }",
         "assert_want": "Snooze until tomorrow"},
        {"type": "chrome", "duration": 13,
         "url_path": "/due",
         "caption": "Snooze the seeded card -- tomorrow's due date, no grade recorded.",
         "js": ["() => { const f = document.querySelector(\"form[action='/cards/{seed_cid}/snooze']\"); "
                "if (!f) return 'snooze-form-missing'; f.submit(); return 'submitted'; }"],
         "poll_js": "() => document.body.innerText.slice(0, 12000)",
         "poll_want": "Snoozed until",
         "poll_required": True,
         "poll_timeout": 25,
         "assert_js": "() => document.body.innerText.includes('no grade recorded')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "Proof in the fixture DB: due pushed forward, zero reviews recorded.",
         "commands": [
             ["python3", "-c",
              "import os, sqlite3; con = sqlite3.connect(os.environ.get('DEMO_DB', 'groundwork.db')); "
              "print('due:', con.execute(\"SELECT due FROM cards WHERE id='{seed_cid}'\").fetchone()[0]); "
              "print('reviews:', con.execute(\"SELECT COUNT(*) FROM reviews WHERE card_id='{seed_cid}'\").fetchone()[0])"],
         ]},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 2",
         "title": "Not today, honestly.",
         "subtitle": "snooze_due() pushes one card a day -- submit_review never fires."},
    ],
}


def seed_db(db_path: str) -> dict:
    """One due card, no reviews anywhere (a single-card queue).

    Wiping reviews also suppresses probe cards (probes need owned
    concepts), so the queue holds exactly the snooze target and the
    zero-review proof beat is airtight.
    """
    con = sqlite3.connect(db_path)
    try:
        card = con.execute(
            "SELECT cards.id, concepts.name FROM cards JOIN concepts"
            " ON concepts.id = cards.concept_id"
            " ORDER BY cards.due LIMIT 1").fetchone()
        if not card:
            return {"seeded": False, "reason": "no cards"}
        cid = card[0]
        con.execute("DELETE FROM reviews")
        con.execute("UPDATE cards SET due='2999-01-01T00:00:00Z'")
        con.execute("UPDATE cards SET due='2000-01-01T00:00:00Z'"
                    " WHERE id=?", (cid,))
        con.commit()
        return {"seeded": True, "cid": cid, "concept": card[1]}
    finally:
        con.close()
