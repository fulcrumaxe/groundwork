"""Improvement demo: module sorting (Batch 2, I-18).

Full functionality: the Modules library toggles newest-first and
oldest-first on ?sort=. seed_db backdates one module to 2000 so the
oldest end is unmistakable, then reports the true first module under
each order (same ORDER BY the page uses, ties included).
"""
from __future__ import annotations

import sqlite3

SCENARIO = {
    "id": "module-sort",
    "kind": "improvement",
    "batch": 2,
    "item": "I-18",
    "title": "Module sorting",
    "blurb": "The Modules library toggles newest-first and oldest-first.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 2 - Improvement I-18",
         "title": "Module sorting",
         "subtitle": "The Modules library toggles newest-first and oldest-first."},
        {"type": "chrome", "duration": 8,
         "url_path": "/modules",
         "focus": "#sort",
         "caption": "The Modules library toggles newest-first and oldest-first.",
         "assert_js": "() => { const s = document.querySelector('#sort'); "
                      "return s.textContent + '|' + "
                      "!!s.querySelector(\"a[href*='sort=oldest']\"); }",
         "assert_want": "Oldest|true"},
        {"type": "chrome", "duration": 10,
         "url_path": "/modules?sort=oldest",
         "caption": "Oldest first: the year-2000 module leads the library.",
         "assert_js": "() => document.querySelector('#library article a')"
                      ".getAttribute('href')",
         "assert_want": "/modules/{seed_oldest}"},
        {"type": "terminal", "duration": 6,
         "caption": "The order key: created_at ascending versus descending.",
         "commands": [
             ["python3", "-c",
              "import os, sqlite3; "
              "con = sqlite3.connect(os.environ.get('DEMO_DB', 'groundwork.db')); "
              "o = con.execute('SELECT id, created_at FROM modules ORDER BY created_at ASC, rowid ASC LIMIT 1').fetchone(); "
              "n = con.execute('SELECT id, created_at FROM modules ORDER BY created_at DESC, rowid DESC LIMIT 1').fetchone(); "
              "print('oldest-first lead:', o[0], o[1]); print('newest-first lead:', n[0], n[1])"],
         ]},
        {"type": "chrome", "duration": 8,
         "url_path": "/modules?sort=newest",
         "caption": "Newest first: the freshest module leads instead.",
         "assert_js": "() => document.querySelector('#library article a')"
                      ".getAttribute('href')",
         "assert_want": "/modules/{seed_newest}"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 2",
         "title": "Both ends of the library.",
         "subtitle": "modules_html flips created_at order on ?sort=."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Backdate one module to 2000; report each order's true lead.

    Leads come from the page's own ORDER BY (ties broken by rowid),
    so the asserts hold whatever the library contains.
    """
    con = sqlite3.connect(db_path)
    try:
        m = con.execute(
            "SELECT id FROM modules ORDER BY created_at DESC LIMIT 1").fetchone()
        if not m:
            return {"seeded": False, "reason": "no modules"}
        # Backdate a mid-list module, never the natural newest: both
        # ends stay interesting.
        mid = con.execute(
            "SELECT id FROM modules ORDER BY created_at DESC LIMIT 1"
            " OFFSET 5").fetchone()
        target = (mid[0] if mid else m[0])
        con.execute("UPDATE modules SET created_at='2000-01-01T00:00:00Z'"
                    " WHERE id=?", (target,))
        con.commit()
        oldest = con.execute(
            "SELECT id FROM modules ORDER BY created_at ASC, rowid ASC"
            " LIMIT 1").fetchone()[0]
        newest = con.execute(
            "SELECT id FROM modules ORDER BY created_at DESC, rowid DESC"
            " LIMIT 1").fetchone()[0]
        return {"seeded": True, "oldest": oldest, "newest": newest}
    finally:
        con.close()
