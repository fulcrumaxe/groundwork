"""Feature demo: blind spots (Batch 4, F-184).

Full functionality: Status lists the lowest-mastery concepts with
lesson links, so study time goes where it matters. seed_db drops one
concept to 2% mastery, so it must lead the list.
"""
from __future__ import annotations

import sqlite3


def _slug(text: str) -> str:
    """Mirror lessons.slug: lowercased alnum, runs of other chars to '-'."""
    out = "".join(ch.lower() if ch.isalnum() else "-" for ch in (text or ""))
    return "-".join(filter(None, out.split("-"))) or "lesson"


SCENARIO = {
    "id": "blind-spots",
    "kind": "feature",
    "batch": 4,
    "item": "F-184",
    "title": "Blind spots",
    "blurb": "Lowest-mastery concepts -- study time goes where it matters.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 4 - Feature F-184",
         "title": "Blind spots",
         "subtitle": "Lowest-mastery concepts -- study time goes where it matters."},
        {"type": "chrome", "duration": 10,
         "url_path": "/status",
         "focus": "#status-blindspots",
         "caption": "The lowest-mastery concept leads, with its lesson link.",
         "assert_js": "() => document.body.innerText.includes('{seed_concept}') + '|' + "
                      "document.body.innerText.includes('(2% \u00b7')",
         "assert_want": "true|true"},
        {"type": "terminal", "duration": 7,
         "caption": "Bottom of the mastery table: one concept at 2%.",
         "commands": [
             ["python3", "-c",
              "import os, sqlite3; "
              "con = sqlite3.connect(os.environ.get('DEMO_DB', 'groundwork.db')); "
              "rows = con.execute('SELECT name, mastery FROM concepts ORDER BY mastery ASC, rowid LIMIT 3').fetchall(); "
              "[print('%s: %.0f%%' % (r[0], 100 * (r[1] or 0.0))) for r in rows]"],
         ]},
        {"type": "chrome", "duration": 8,
         "url_path": "/status",
         "focus": "#lesson-{seed_lesson}",
         "caption": "The lesson link jumps to the concept to study.",
         "js": ["() => { const h = document.querySelector('#status-blindspots'); "
                "let n = h ? h.nextElementSibling : null; "
                "while (n && n.tagName !== 'UL' && !/^H[23]$/.test(n.tagName)) n = n.nextElementSibling; "
                "const a = n ? n.querySelector('a') : null; "
                "if (!a) return 'spot-link-missing'; a.click(); return 'clicked'; }"],
         "poll_js": "() => location.pathname",
         "poll_want": "/modules/{seed_mid}",
         "poll_required": True,
         "poll_timeout": 25,
         "assert_js": "() => { window.scrollTo(0, 0); "
                      "return location.pathname + '|' + location.hash.slice(0, 8); }",
         "assert_want": "/modules/{seed_mid}|#lesson-"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 4",
         "title": "Study where it matters.",
         "subtitle": "blindspots.py ranks concepts by mastery, lowest first."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Float every concept to 90%, sink one to 2%.

    The sunk concept leads the bottom-ten list deterministically; its
    lesson link is the first in the section.
    """
    con = sqlite3.connect(db_path)
    try:
        c = con.execute(
            "SELECT id, name, module_id FROM concepts"
            " ORDER BY rowid LIMIT 1").fetchone()
        if not c:
            return {"seeded": False, "reason": "no concepts"}
        cid, name, mid = c
        con.execute("UPDATE concepts SET mastery=0.9")
        con.execute("UPDATE concepts SET mastery=0.02 WHERE id=?", (cid,))
        con.commit()
        node = cid.split(":", 1)[1] if ":" in cid else cid
        return {"seeded": True, "cid": cid, "concept": name, "mid": mid,
                "lesson": _slug(node)}
    finally:
        con.close()
