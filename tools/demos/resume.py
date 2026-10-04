"""Improvement demo: resume interrupted sessions (I-48).

Full behavior: each History attempt row carries a continue link
(/due?resume=<module>:<day>) that rebuilds the queue as it was --
cards still due from that module, with a resume banner. seed_db
reviews one card of a module today and leaves two due; the click
beat follows the seeded continue link and polls the narrowed
banner. (Scenario research found the narrowing dead -- due cards
carried no module field -- fixed in mcp.py with a regression test.)
"""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone

SCENARIO = {
    "id": "resume",
    "kind": "improvement",
    "batch": 9,
    "item": "I-48",
    "title": "Continue interrupted sessions",
    "blurb": "History rows offer a continue link that rebuilds the queue as it was.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 9 - Improvement I-48",
         "title": "Continue interrupted sessions",
         "subtitle": "A History link rebuilds the queue -- same module, still due."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b9-resume",
         "caption": "Status documents the key: module plus day, shape-checked like originguard.",
         "assert_js": "() => !!document.querySelector('#status-b9-resume')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "The rule in one line: keys narrow to the module, garbage falls back to /due.",
         "commands": [
             ["python3", "-c",
              "from groundwork import resume as m; "
              "print(m.continue_url('m7:2026-09-20')); "
              "print(m.continue_url('garbage')); "
              "cards = [{'id': 'c1', 'module_id': 'm7'}, {'id': 'c2', 'module_id': 'm8'}]; "
              "print([c['id'] for c in m.session_cards(cards, 'm7:2026-09-20')])"],
         ]},
        {"type": "chrome", "duration": 8,
         "url_path": "/reviews",
         "focus": "#attempts",
         "caption": "History carries the continue link on today's attempt row.",
         "assert_js": "() => !!document.querySelector(\"a.resume-link[href*='{seed_mid}']\")",
         "assert_want": "True"},
        {"type": "chrome", "duration": 12,
         "url_path": "/reviews",
         "focus": "#resume-box",
         "caption": "Follow it -- Due narrows to the two cards still due from that module.",
         "js": ["() => { const a = document.querySelector(\"a.resume-link[href*='{seed_mid}']\"); "
                "if (!a) return 'seed-link-missing'; a.click(); return 'clicked'; }"],
         "poll_js": "() => document.body.innerText.slice(0, 12000)",
         "poll_want": "Resuming session",
         "poll_required": True,
         "poll_timeout": 25,
         "assert_js": "() => { const b = document.querySelector('#resume-box'); "
                      "return !!b && b.textContent.includes('2 cards still due'); }",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 9",
         "title": "Picked up where you left off.",
         "subtitle": "resume.py rebuilds the queue -- module context, still-due cards."},
    ],
}


def seed_db(db_path: str) -> dict:
    """One module: two cards due, one reviewed today; rest pushed out."""
    con = sqlite3.connect(db_path)
    try:
        mod = con.execute(
            "SELECT concepts.module_id FROM cards"
            " JOIN concepts ON concepts.id = cards.concept_id"
            " GROUP BY concepts.module_id HAVING COUNT(*) >= 3"
            " ORDER BY concepts.module_id LIMIT 1").fetchone()
        if not mod:
            return {"seeded": False, "reason": "no 3-card module"}
        mid = mod[0]
        cards = con.execute(
            "SELECT cards.id FROM cards"
            " JOIN concepts ON concepts.id = cards.concept_id"
            " WHERE concepts.module_id = ? ORDER BY cards.due LIMIT 3",
            (mid,)).fetchall()
        con.execute("UPDATE cards SET due='2030-01-01T00:00:00Z'")
        for cid, in cards:
            con.execute("DELETE FROM reviews WHERE card_id=?", (cid,))
        due_ids = [cards[0][0], cards[1][0]]
        for cid in due_ids:
            con.execute("UPDATE cards SET due='2000-01-01T00:00:00Z'"
                        " WHERE id=?", (cid,))
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        con.execute(
            "INSERT INTO reviews(card_id, grade, confidence, reviewed_at,"
            " submission) VALUES(?, 4, 4, ?, 'resume seed')",
            (cards[2][0], now))
        con.commit()
        return {"seeded": True, "mid": mid,
                "day": now[:10], "due_ids": due_ids,
                "reviewed_id": cards[2][0]}
    finally:
        con.close()
