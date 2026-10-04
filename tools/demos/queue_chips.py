"""Improvement demo: queue status chips (Batch 3, I-219).

Full functionality: Due cards carry an at-a-glance status chip --
new (never attempted), due (due today), or Nd overdue (stale class).
seed_db parks the queue to exactly three cards, one per chip, so all
three film on the live queue with real attempt counts.
"""
from __future__ import annotations

import re
import sqlite3
from datetime import datetime, timedelta, timezone

_ANCHOR_OK = re.compile(r"[A-Za-z0-9_-]+")


def _slug(text: str) -> str:
    """Mirror scrollpos.card_anchor: keep [A-Za-z0-9_-], cap at 48."""
    return "".join(_ANCHOR_OK.findall((text or "").strip()))[:48] or "unknown"


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


SCENARIO = {
    "id": "queue-chips",
    "kind": "improvement",
    "batch": 3,
    "item": "I-219",
    "title": "Queue status chips",
    "blurb": "Due, overdue and new cards carry distinct chips in the queue.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 3 - Improvement I-219",
         "title": "Queue status chips",
         "subtitle": "Due, overdue and new cards carry distinct chips in the queue."},
        {"type": "chrome", "duration": 8,
         "url_path": "/due",
         "focus": "article.next",
         "caption": "The lead card is 45 days overdue -- its chip says so.",
         "assert_js": "() => { const s = document.querySelector('#queue-status'); "
                      "return s ? s.textContent : 'missing'; }",
         "assert_want": "45d overdue"},
        {"type": "chrome", "duration": 7,
         "url_path": "/due",
         "focus": "#card-{seed_a_due}",
         "caption": "Cards due today carry a plain due chip.",
         "assert_js": "() => { const a = document.querySelector('#card-{seed_a_due}'); "
                      "const h = a ? a.querySelector('h3') : null; "
                      "return h ? h.innerHTML : 'missing'; }",
         "assert_want": "chip\">due<"},
        {"type": "chrome", "duration": 7,
         "url_path": "/due",
         "focus": "#card-{seed_a_new}",
         "caption": "Fresh cards show a new chip -- no history yet.",
         "assert_js": "() => { const a = document.querySelector('#card-{seed_a_new}'); "
                      "const h = a ? a.querySelector('h3') : null; "
                      "return h ? h.innerHTML : 'missing'; }",
         "assert_want": "chip\">new<"},
        {"type": "terminal", "duration": 7,
         "caption": "One builder over the fixture rows: attempts plus days overdue.",
         "commands": [
             ["python3", "-c",
              "import os, sqlite3; con = sqlite3.connect(os.environ.get('DEMO_DB', 'groundwork.db')); con.row_factory = sqlite3.Row; "
              "from groundwork import cards as c, queries as q; "
              "ids = ['{seed_c_over}', '{seed_c_due}', '{seed_c_new}']; tries = q.attempts(con, ids); "
              "rows = con.execute('SELECT * FROM cards WHERE id IN (\\'{seed_c_over}\\', \\'{seed_c_due}\\', \\'{seed_c_new}\\') ORDER BY due').fetchall(); "
              "[print(r['id'][:8], 'tries=%d' % tries.get(r['id'], 0), '->', c.status_chip(r, tries.get(r['id'], 0))) for r in rows]"],
         ]},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 3",
         "title": "Status at a glance.",
         "subtitle": "cards.status_chip reads attempts plus days overdue."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Three due cards, one interleave cell: 45d-overdue vs due-today vs new.

    All three share one (concept, exercise type) because the queue
    ranks weakest-cell-first (interleave.order_due): a lone unattempted
    card scores 0.0 and would jump ahead of the overdue seed. Inside a
    single cell the round-robin preserves due order, so the overdue
    card leads and wears #queue-status. The overdue and due cards each
    get one planted review (attempted); the new card keeps zero
    reviews. Everything else parks in 2999 and all other reviews wipe,
    so the queue holds exactly these three (no probes: every seed
    stays under the 7.0 stability probe floor; no boredom: the [2, 4]
    grade tail never reaches the pass streak of 3).
    """
    con = sqlite3.connect(db_path)
    try:
        cell = con.execute(
            "SELECT concept_id, exercise_type FROM cards"
            " GROUP BY concept_id, exercise_type HAVING COUNT(*) >= 3"
            " ORDER BY concept_id LIMIT 1").fetchone()
        if not cell:
            return {"seeded": False, "reason": "need 3 cards in one cell"}
        rows = con.execute(
            "SELECT id FROM cards WHERE concept_id=? AND exercise_type=?"
            " ORDER BY due LIMIT 3", (cell[0], cell[1])).fetchall()
        if len(rows) < 3:
            return {"seeded": False, "reason": "need 3 cards in one cell"}
        c_over, c_due, c_new = [r[0] for r in rows]
        now = datetime.now(timezone.utc)
        # 45d12h cushion: the Due queue's sleep hook can push NEW cards
        # due in quiet hours forward up to +9h; the overdue seed is
        # attempted (hook-proof) but the cushion keeps .days at 45.
        over_due = _iso(now - timedelta(days=45, hours=12))
        due_due = _iso(now - timedelta(hours=1))
        # 2d backdate: a NEW card due in quiet hours would be pushed to
        # 07:00 UTC and could leave the queue; 2d keeps it due anyway.
        new_due = _iso(now - timedelta(days=2))
        stamp = _iso(now)
        con.execute("DELETE FROM reviews")
        con.execute("UPDATE cards SET due='2999-01-01T00:00:00Z'")
        con.execute("UPDATE cards SET due=?, stability=2.0,"
                    " retrievability=0.3, lapses=1 WHERE id=?",
                    (over_due, c_over))
        con.execute("UPDATE cards SET due=?, stability=1.0,"
                    " retrievability=0.9, lapses=0 WHERE id=?",
                    (due_due, c_due))
        con.execute("UPDATE cards SET due=?, stability=1.0,"
                    " retrievability=1.0, lapses=0 WHERE id=?",
                    (new_due, c_new))
        con.execute("INSERT INTO reviews(card_id, grade, confidence,"
                    " reviewed_at, submission) VALUES(?, 2, 3, ?, 'chip seed')",
                    (c_over, stamp))
        con.execute("INSERT INTO reviews(card_id, grade, confidence,"
                    " reviewed_at, submission) VALUES(?, 4, 4, ?, 'chip seed')",
                    (c_due, stamp))
        con.commit()
        return {"seeded": True, "c_over": c_over, "c_due": c_due,
                "c_new": c_new, "a_over": _slug(c_over),
                "a_due": _slug(c_due), "a_new": _slug(c_new)}
    finally:
        con.close()
