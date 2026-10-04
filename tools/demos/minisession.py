"""Improvement demo: one-click 5-minute session (I-46).

Full behavior: the Due banner queues the most-overdue cards that
fit ~5 minutes (new 30s, reviews 20s) and starts on the lead card.
seed_db forces exactly three fresh cards due (the default dial
caps new cards at three); the Due beat shows the live About-3-cards
banner plus its #up-next target, the terminal beats prove the
greedy fill and the fixture count.
"""
from __future__ import annotations

import sqlite3

SCENARIO = {
    "id": "minisession",
    "kind": "improvement",
    "batch": 9,
    "item": "I-46",
    "title": "Five-minute session",
    "blurb": "One click queues about five minutes of the most-overdue cards.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 9 - Improvement I-46",
         "title": "Five-minute session",
         "subtitle": "About five minutes of the most-overdue cards -- one click."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b9-minisession",
         "caption": "Status documents the plan: greedy most-overdue fill on a seconds budget.",
         "assert_js": "() => !!document.querySelector('#status-b9-minisession')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 8,
         "caption": "The rule in one line: most-overdue first until the budget fills.",
         "commands": [
             ["python3", "-c",
              "from groundwork import minisession as m; "
              "due = [{'id': f'c{i}', 'due': '2000-01-01T00:00:00Z'} for i in range(12)]; "
              "picks = m.pick_cards(due); "
              "print('picked:', len(picks), 'of', len(due)); "
              "print('seconds:', m.planned_seconds(picks)); "
              "print(m.session_box_html(due)[:130])"],
         ]},
        {"type": "chrome", "duration": 12,
         "url_path": "/due",
         "caption": "Three cards due, three queued -- the banner starts on the lead card.",
         "assert_js": "() => { const s = document.querySelector('#minisession'); "
                      "const a = document.querySelector('#mini-start'); "
                      "return !!s && s.textContent.includes('About 3 cards') && "
                      "!!a && a.getAttribute('href') === '#up-next' && "
                      "!!document.querySelector('#up-next'); }",
         "assert_want": "True"},
        {"type": "terminal", "duration": 5,
         "caption": "The manipulated fixture: exactly three cards due.",
         "commands": [
             ["python3", "-c",
              "import os, sqlite3; con = sqlite3.connect(os.environ.get('DEMO_DB', 'groundwork.db')); "
              "print('due:', con.execute(\"SELECT COUNT(*) FROM cards WHERE due <= '2026-01-01T00:00:00Z' AND stale = 0\").fetchone()[0])"],
         ]},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 9",
         "title": "Five minutes, queued.",
         "subtitle": "minisession.py budgets the queue -- new 30s, reviews 20s."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Force exactly three fresh cards due (new = 30s each, ~2 min)."""
    con = sqlite3.connect(db_path)
    try:
        rows = con.execute(
            "SELECT id FROM cards ORDER BY due LIMIT 3").fetchall()
        if len(rows) < 3:
            return {"seeded": False, "reason": "fewer than 3 cards"}
        con.execute("UPDATE cards SET due='2030-01-01T00:00:00Z'")
        for i, (cid,) in enumerate(rows):
            con.execute("UPDATE cards SET due=? WHERE id=?",
                        (f"2000-01-0{min(i + 1, 9)}T00:00:00Z", cid))
            con.execute("DELETE FROM reviews WHERE card_id=?", (cid,))
        con.commit()
        return {"seeded": True, "count": 3,
                "card_ids": [r[0] for r in rows]}
    finally:
        con.close()
