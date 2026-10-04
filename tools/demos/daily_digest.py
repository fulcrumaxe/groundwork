"""Improvement demo: daily digest (Batch 4, I-242).

Full functionality: Due opens with today at a glance -- due now,
new cards, due tomorrow, and a suggested start link. seed_db parks
the queue to three due now plus two due within a day, so the counts
must read exactly.
"""
from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _slug(text: str) -> str:
    """Mirror lessons.slug: lowercased alnum, runs of other chars to '-'."""
    out = "".join(ch.lower() if ch.isalnum() else "-" for ch in (text or ""))
    return "-".join(filter(None, out.split("-"))) or "lesson"


SCENARIO = {
    "id": "daily-digest",
    "kind": "improvement",
    "batch": 4,
    "item": "I-242",
    "title": "Daily digest",
    "blurb": "Today at a glance: due now, new cards, and where to start.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 4 - Improvement I-242",
         "title": "Daily digest",
         "subtitle": "Today at a glance: due now, new cards, and where to start."},
        {"type": "chrome", "duration": 10,
         "url_path": "/due",
         "focus": "#digest",
         "caption": "Today: three due now, two more by tomorrow, and a start link.",
         "assert_js": "() => { const h = document.querySelector('#digest'); "
                      "const p = h ? h.querySelector('p') : null; "
                      "return p ? p.textContent : 'missing'; }",
         "assert_want": "3 due now \u00b7 {seed_new} new \u00b7 2 more by tomorrow"},
        {"type": "terminal", "duration": 7,
         "caption": "The renderer over the fixture rows: same counts, same start.",
         "commands": [
             ["python3", "-c",
              "import os; from groundwork import digest as d; "
              "print(d.section_html(os.environ.get('DEMO_DB', 'groundwork.db')))"],
         ]},
        {"type": "chrome", "duration": 8,
         "url_path": "/due",
         "focus": "#lesson-{seed_lesson}",
         "caption": "Start with jumps to the first due lesson.",
         "js": ["() => { const a = document.querySelector('#digest a'); "
                "if (!a) return 'no-start-link'; a.click(); return 'clicked'; }"],
         "poll_js": "() => location.hash",
         "poll_want": "#lesson-",
         "poll_required": True,
         "poll_timeout": 25,
         "assert_js": "() => { window.scrollTo(0, 0); "
                      "return location.pathname + '|' + location.hash.slice(0, 8); }",
         "assert_want": "/modules/{seed_mid}|#lesson-"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 4",
         "title": "Today at a glance.",
         "subtitle": "digest.py counts the queue and names where to start."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Three due now, two due within a day, zero prior reviews.

    Wiping reviews makes every non-stale card new, so the new count is
    deterministic. The earliest-due card's concept names the start link.
    """
    con = sqlite3.connect(db_path)
    try:
        cards = con.execute(
            "SELECT id FROM cards WHERE stale = 0 ORDER BY due LIMIT 5"
            ).fetchall()
        if len(cards) < 5:
            return {"seeded": False, "reason": "need 5 live cards"}
        ids = [c[0] for c in cards]
        now = datetime.now(timezone.utc)
        con.execute("DELETE FROM reviews")
        con.execute("UPDATE cards SET due='2999-01-01T00:00:00Z'")
        dues = [now - timedelta(days=3), now - timedelta(days=2),
                now - timedelta(days=1), now + timedelta(hours=12),
                now + timedelta(hours=20)]
        for cid, due in zip(ids, dues):
            con.execute("UPDATE cards SET due=?, stability=1.0,"
                        " retrievability=0.9, lapses=0 WHERE id=?",
                        (_iso(due), cid))
        # Attempted seeds are sleep-hook-proof; only the due-now trio
        # needs planting (tomorrow's pair stays new either way).
        for cid in ids[:3]:
            con.execute("INSERT INTO reviews(card_id, grade, confidence,"
                        " reviewed_at, submission) VALUES(?, 4, 3, ?, 'digest seed')",
                        (cid, _iso(now - timedelta(days=4))))
        row = con.execute(
            "SELECT concepts.id, concepts.name, concepts.module_id FROM cards"
            " JOIN concepts ON concepts.id = cards.concept_id"
            " WHERE cards.id=?", (ids[0],)).fetchone()
        new_n = con.execute(
            "SELECT COUNT(*) FROM cards WHERE cards.stale = 0 AND NOT EXISTS"
            " (SELECT 1 FROM reviews WHERE reviews.card_id = cards.id)"
            ).fetchone()[0]
        con.commit()
        node = row[0].split(":", 1)[1] if ":" in row[0] else row[0]
        return {"seeded": True, "new": new_n, "concept": row[1],
                "mid": row[2], "first_card": ids[0],
                "lesson": _slug(node)}
    finally:
        con.close()
