"""Improvement demo: queue grouped by module (Batch 4, I-44).

Full functionality: Due cards gather under collapsible per-module
sections instead of one flat list. seed_db parks the queue to exactly
two cards from two modules, so both group headings must film.
"""
from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone

SCENARIO = {
    "id": "queue-groups",
    "kind": "improvement",
    "batch": 4,
    "item": "I-44",
    "title": "Queue grouped by module",
    "blurb": "Due cards gather under collapsible per-module sections.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 4 - Improvement I-44",
         "title": "Queue grouped by module",
         "subtitle": "Due cards gather under collapsible per-module sections."},
        {"type": "terminal", "duration": 8,
         "caption": "Pure grouping: two due cards, two modules, two groups.",
         "commands": [
             ["python3", "-c",
              "import os, sqlite3; from groundwork import queue as q; "
              "db = os.environ.get('DEMO_DB', 'groundwork.db'); "
              "con = sqlite3.connect(db); con.row_factory = sqlite3.Row; "
              "due = [dict(r) for r in con.execute(\"SELECT * FROM cards WHERE due < '2999-01-01T00:00:00Z' AND stale = 0\").fetchall()]; "
              "[print(repr(g['title'][:28]), '->', len(g['cards']), 'card(s)') for g in q.groups(db, due)]"],
         ]},
        {"type": "chrome", "duration": 9,
         "url_path": "/due",
         "focus": "#film-groups",
         "caption": "Each module gets its own section with a study link.",
         "js": ["() => { const all = Array.from(document.querySelectorAll('#queue details')); "
                "const g = all.find(d => { const s = d.querySelector(':scope > summary'); "
                "return s && !!s.querySelector(\"a[href^='/modules/']\"); }); "
                "if (!g) return 'no-group'; g.id = 'film-groups'; return 'marked'; }"],
         "assert_js": "() => !!document.querySelector('#queue-groups') + '|' + "
                      "Array.from(document.querySelectorAll('main summary')).filter(s => "
                      "s.textContent.includes('{seed_mark_a}') || "
                      "s.textContent.includes('{seed_mark_b}')).length + '|' + "
                      "document.body.innerText.includes('{seed_mark_a}') + '|' + "
                      "document.body.innerText.includes('{seed_mark_b}')",
         "assert_want": "true|2|true|true"},
        {"type": "chrome", "duration": 8,
         "url_path": "/due",
         "focus": "#film-groups",
         "caption": "Sections collapse -- long queues stay scannable.",
         "js": ["() => { const all = Array.from(document.querySelectorAll('#queue details')); "
                "const g = all.find(d => { const s = d.querySelector(':scope > summary'); "
                "return s && !!s.querySelector(\"a[href^='/modules/']\"); }); "
                "if (!g) return 'no-group'; g.id = 'film-groups'; return 'marked'; }",
                "() => { const all = Array.from(document.querySelectorAll('#queue summary')); "
                "const s = all.find(x => x.textContent.includes('{seed_mark_a}')); "
                "if (!s) return 'no-group-summary'; s.click(); return 'toggled'; }"],
         "assert_js": "() => { const all = Array.from(document.querySelectorAll('main details')); "
                      "const d = all.find(x => x.textContent.includes('{seed_mark_a}')); "
                      "return d ? String(d.open) : 'missing'; }",
         "assert_want": "false"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 4",
         "title": "Scannable queues.",
         "subtitle": "queue.py gathers the due list by module, first-seen order."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Two due cards from two modules; everything else parked.

    Both seeds are attempted (one planted review each), so the Due
    queue's sleep hook cannot push them out of the queue.
    """
    con = sqlite3.connect(db_path)
    try:
        mods = con.execute(
            "SELECT concepts.module_id FROM cards"
            " JOIN concepts ON concepts.id = cards.concept_id"
            " GROUP BY concepts.module_id"
            " ORDER BY concepts.module_id LIMIT 2").fetchall()
        if len(mods) < 2:
            return {"seeded": False, "reason": "need 2 modules with cards"}
        mids = [m[0] for m in mods]
        cards = []
        for mid in mids:
            c = con.execute(
                "SELECT cards.id FROM cards JOIN concepts"
                " ON concepts.id = cards.concept_id"
                " WHERE concepts.module_id=? ORDER BY cards.due LIMIT 1",
                (mid,)).fetchone()
            if not c:
                return {"seeded": False, "reason": "module without cards"}
            cards.append(c[0])
        now = datetime.now(timezone.utc)
        stamp = (now - timedelta(days=2)).strftime("%Y-%m-%dT%H:%M:%SZ")
        con.execute("DELETE FROM reviews")
        con.execute("UPDATE cards SET due='2999-01-01T00:00:00Z'")
        marks = ["QGAlpha42", "QGBeta42"]
        for mid, cid, mark in zip(mids, cards, marks):
            con.execute(
                "UPDATE modules SET task_summary = ? || ' ' || COALESCE(task_summary, id)"
                " WHERE id=?", (mark, mid))
            con.execute("UPDATE cards SET due=?, stability=1.0,"
                        " retrievability=0.9, lapses=0 WHERE id=?",
                        (stamp, cid))
            con.execute("INSERT INTO reviews(card_id, grade, confidence,"
                        " reviewed_at, submission) VALUES(?, 4, 3, ?, 'group seed')",
                        (cid, stamp))
        con.commit()
        return {"seeded": True, "mids": mids, "cards": cards,
                "mark_a": marks[0], "mark_b": marks[1]}
    finally:
        con.close()
