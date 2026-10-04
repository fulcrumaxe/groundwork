"""Improvement demo: archived-module notice (I-38).

Full behavior: a deleted module's own URL explains itself --
search the library, keep going with a sibling -- while garbage
ids keep the bare 404. seed_db deletes a real module row;
Status demos the notice, terminal runs the id rule, the gone
URL films the wired notice, /modules shows the live target.
"""
from __future__ import annotations

import sqlite3

SCENARIO = {
    "id": "archived",
    "kind": "improvement",
    "batch": 8,
    "item": "I-38",
    "title": "Archived-module notice",
    "blurb": ("Deleted modules explain themselves with search and "
              "siblings, not a bare 404."),
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 8 - Improvement I-38",
         "title": "Archived-module notice",
         "subtitle": ("Gone modules explain themselves -- garbage ids "
                      "still 404.")},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b8-archived",
         "caption": ("Status demos the notice: explanation, library "
                     "search, sibling link."),
         "assert_js": "() => !!document.querySelector('#status-b8-archived') && "
                      "!!document.querySelector('#archived')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": ("The rule in one line: plausible ids explain, junk "
                     "stays 404."),
         "commands": [
             ["python3", "-c",
              "from groundwork import archived as m; "
              "print(m.is_archived_id('12'), m.is_archived_id('a/b'), m.is_archived_id('../etc')); "
              "print('archived' in m.archived_html('12', [{'id':'9','title':'Intro'}]))"],
         ]},
        {"type": "chrome", "duration": 12,
         "url_path": "/modules/{seed_gone_id}",
         "caption": ("A deleted module explains itself: search the library, "
                     "keep going with a sibling."),
         "poll_js": "() => document.body.innerText.slice(0, 12000)",
         "poll_want": "was removed or archived",
         "poll_required": True,
         "poll_timeout": 25,
         "assert_js": "() => !!document.querySelector('#archived') && "
                      "document.body.innerText.includes('{seed_gone_id}')",
         "assert_want": "True"},
        {"type": "chrome", "duration": 8,
         "url_path": "/modules",
         "focus": ".pager-summary",
         "caption": ("The library the notice points at -- the replacement "
                     "lives here."),
         "assert_js": "() => { const s = document.querySelector('.pager-summary'); "
                      "return !!s && s.textContent.includes('Showing') && "
                      "!!document.querySelector('nav.pager'); }",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 8",
         "title": "Gone, not silent.",
         "subtitle": ("archived.py notices deleted ids -- errors.py keeps "
                      "the real 404s.")},
    ],
}


def seed_db(db_path: str) -> dict:
    """Delete one real module; its URL must explain, not bare-404."""
    con = sqlite3.connect(db_path)
    try:
        row = con.execute(
            "SELECT id FROM modules ORDER BY rowid LIMIT 1").fetchone()
        if not row:
            return {"seeded": False, "reason": "no modules"}
        gone_id = row[0]
        sibs = con.execute(
            "SELECT id, task_summary FROM modules WHERE id != ?"
            " ORDER BY rowid LIMIT 8", (gone_id,)).fetchall()
        con.execute("DELETE FROM modules WHERE id=?", (gone_id,))
        con.commit()
        return {"seeded": True, "gone_id": gone_id,
                "sibling_id": sibs[0][0] if sibs else "",
                "sibling_count": len(sibs)}
    finally:
        con.close()
